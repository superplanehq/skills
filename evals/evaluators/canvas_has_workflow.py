"""Assert the canvas contains a directed path matching a sequence of node names.

Use ``"..."`` between two names to allow any number of intermediate hops.
Example: ``CanvasHasWorkflow("github.onPullRequest", "...", "wait", "...", "deleteSandbox")``.
"""
from __future__ import annotations

from collections import deque
from typing import Any

from pydantic_evals.evaluators import EvaluationReason, Evaluator, EvaluatorContext

from evals.evaluators.canvas_shape import CanvasShape, shape_for
from evals.tool_registry import CaseResult


class CanvasHasWorkflow(Evaluator):
    def __init__(self, *steps: str) -> None:
        self.steps = steps

    def evaluate(self, ctx: EvaluatorContext[str, CaseResult, Any]) -> EvaluationReason:
        shape = shape_for(ctx.output)
        if shape is None:
            return EvaluationReason(value=False, reason="no parseable canvas YAML")
        if not shape.node_names_by_id:
            return EvaluationReason(value=False, reason="canvas has no nodes")

        steps = _normalize(self.steps)
        if not steps:
            return EvaluationReason(value=False, reason="empty workflow sequence")

        starts = [nid for nid, name in shape.node_names_by_id.items() if name == steps[0]]
        if not starts:
            return EvaluationReason(value=False, reason=f"workflow start {steps[0]!r} not found")

        cache: dict[tuple[str, int], bool] = {}
        for node_id in starts:
            if _matches(node_id, 0, steps, shape, cache):
                return EvaluationReason(value=True, reason=f"workflow path matches {steps}")
        return EvaluationReason(value=False, reason=f"no connected path matches {steps}")


def _normalize(steps: tuple[str, ...]) -> list[str]:
    """Strip whitespace, collapse repeated wildcards, drop leading/trailing wildcards."""
    cleaned = [s.strip() for s in steps if s.strip()]
    out: list[str] = []
    for s in cleaned:
        if s == "..." and out and out[-1] == "...":
            continue
        out.append(s)
    while out and out[0] == "...":
        out.pop(0)
    while out and out[-1] == "...":
        out.pop()
    return out


def _matches(
    node: str,
    idx: int,
    steps: list[str],
    shape: CanvasShape,
    cache: dict[tuple[str, int], bool],
) -> bool:
    key = (node, idx)
    if key in cache:
        return cache[key]
    if shape.node_names_by_id[node] != steps[idx]:
        cache[key] = False
        return False
    if idx == len(steps) - 1:
        cache[key] = True
        return True
    nxt = steps[idx + 1]
    if nxt == "...":
        target = steps[idx + 2]
        for reachable in _reachable(node, target, shape):
            if _matches(reachable, idx + 2, steps, shape, cache):
                cache[key] = True
                return True
        cache[key] = False
        return False
    for neighbor in shape.graph.get(node, ()):
        if shape.node_names_by_id[neighbor] != nxt:
            continue
        if _matches(neighbor, idx + 1, steps, shape, cache):
            cache[key] = True
            return True
    cache[key] = False
    return False


def _reachable(start: str, target_name: str, shape: CanvasShape) -> list[str]:
    """All ids reachable from ``start`` whose component name is ``target_name``."""
    queue: deque[str] = deque(shape.graph.get(start, ()))
    seen: set[str] = set()
    out: list[str] = []
    while queue:
        node = queue.popleft()
        if node in seen:
            continue
        seen.add(node)
        if shape.node_names_by_id[node] == target_name:
            out.append(node)
        queue.extend(shape.graph.get(node, ()))
    return out
