"""Port of superplane's CanvasHasWorkflow evaluator, retargeted to parsed canvas YAML.

Preserves the "..." wildcard: ``CanvasHasWorkflow("trigger", "...", "deleteSandbox")``
matches a directed path with zero-or-more intermediate nodes between the named steps.
"""
from __future__ import annotations

from collections import deque
from typing import Any

from pydantic_evals.evaluators import EvaluationReason, Evaluator, EvaluatorContext

from evals.harness import parsed_canvas_yaml
from evals.tool_registry import CaseResult


class CanvasHasWorkflow(Evaluator):
    def __init__(self, *steps: str) -> None:
        self.steps = steps

    def evaluate(self, ctx: EvaluatorContext[str, CaseResult, Any]) -> EvaluationReason:
        parsed = parsed_canvas_yaml(ctx.output)
        if parsed is None:
            return EvaluationReason(value=False, reason="no parseable canvas YAML")

        node_names, graph = _build_graph(parsed)
        if not node_names:
            return EvaluationReason(value=False, reason="canvas has no nodes")

        normalized_steps = _normalize_steps(self.steps)
        if not normalized_steps:
            return EvaluationReason(value=False, reason="empty workflow sequence")

        first = normalized_steps[0]
        starts = [nid for nid, name in node_names.items() if name == first]
        if not starts:
            return EvaluationReason(
                value=False, reason=f"workflow start {first!r} not found"
            )

        cache: dict[tuple[str, int], bool] = {}
        for node_id in starts:
            if _matches_from(node_id, 0, normalized_steps, node_names, graph, cache):
                return EvaluationReason(
                    value=True, reason=f"workflow path matches {normalized_steps}"
                )
        return EvaluationReason(
            value=False, reason=f"no connected path matches {normalized_steps}"
        )


def _build_graph(parsed: dict[str, Any]) -> tuple[dict[str, str], dict[str, set[str]]]:
    spec = parsed.get("spec") or {}
    node_names: dict[str, str] = {}
    graph: dict[str, set[str]] = {}

    # Nodes: spec.nodes[*] with id + component.name (or block).
    for node in spec.get("nodes") or []:
        if not isinstance(node, dict):
            continue
        node_id = node.get("id")
        if not isinstance(node_id, str) or not node_id:
            continue
        component = node.get("component") or {}
        name = component.get("name") if isinstance(component, dict) else None
        if not isinstance(name, str) or not name:
            block = node.get("block")
            name = block if isinstance(block, str) and block else None
        if not name:
            # Fall back to checking trigger.name for trigger-kind nodes.
            trigger = node.get("trigger") or {}
            if isinstance(trigger, dict):
                name = trigger.get("name")
        if isinstance(name, str) and name:
            node_names[node_id] = name
            graph.setdefault(node_id, set())

    # Triggers in the top-level spec.triggers[*]: treat as nodes with id = trigger.id.
    for trig in spec.get("triggers") or []:
        if not isinstance(trig, dict):
            continue
        tid = trig.get("id") or (trig.get("trigger") or {}).get("id")
        tname = trig.get("name") or (trig.get("trigger") or {}).get("name")
        if isinstance(tid, str) and tid and isinstance(tname, str) and tname:
            node_names[tid] = tname
            graph.setdefault(tid, set())

    # Edges: spec.edges[*].
    for edge in spec.get("edges") or []:
        if not isinstance(edge, dict):
            continue
        src = edge.get("sourceId") or edge.get("source")
        dst = edge.get("targetId") or edge.get("target")
        if (
            isinstance(src, str)
            and isinstance(dst, str)
            and src in node_names
            and dst in node_names
        ):
            graph.setdefault(src, set()).add(dst)

    return node_names, graph


def _normalize_steps(steps: tuple[str, ...]) -> list[str]:
    cleaned = [s.strip() for s in steps if s.strip()]
    normalized: list[str] = []
    for s in cleaned:
        if s == "..." and normalized and normalized[-1] == "...":
            continue
        normalized.append(s)
    while normalized and normalized[0] == "...":
        normalized.pop(0)
    while normalized and normalized[-1] == "...":
        normalized.pop()
    return normalized


def _matches_from(
    node: str,
    idx: int,
    steps: list[str],
    node_names: dict[str, str],
    graph: dict[str, set[str]],
    cache: dict[tuple[str, int], bool],
) -> bool:
    key = (node, idx)
    if key in cache:
        return cache[key]
    if node_names[node] != steps[idx]:
        cache[key] = False
        return False
    if idx == len(steps) - 1:
        cache[key] = True
        return True
    nxt = steps[idx + 1]
    if nxt == "...":
        target = steps[idx + 2]
        for reachable in _reachable(node, target, node_names, graph):
            if _matches_from(reachable, idx + 2, steps, node_names, graph, cache):
                cache[key] = True
                return True
        cache[key] = False
        return False
    for neighbor in graph.get(node, set()):
        if node_names[neighbor] != nxt:
            continue
        if _matches_from(neighbor, idx + 1, steps, node_names, graph, cache):
            cache[key] = True
            return True
    cache[key] = False
    return False


def _reachable(
    start: str,
    target_name: str,
    node_names: dict[str, str],
    graph: dict[str, set[str]],
) -> list[str]:
    q: deque[str] = deque(graph.get(start, set()))
    seen: set[str] = set()
    out: list[str] = []
    while q:
        n = q.popleft()
        if n in seen:
            continue
        seen.add(n)
        if node_names[n] == target_name:
            out.append(n)
        for m in graph.get(n, set()):
            if m not in seen:
                q.append(m)
    return out
