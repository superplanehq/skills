"""Flattened view of a parsed canvas YAML — single source of truth for canvas evaluators.

Mirrors superplane/agent/evals/evaluators/workflow_utils.py: parse the structured
input once into a ``CanvasShape``; evaluators consume the shape rather than rolling
their own walkers.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from evals.tool_registry import CaseResult


@dataclass
class CanvasShape:
    components: list[str] = field(default_factory=list)
    """Component name for each node, in declaration order. Includes triggers."""

    triggers: list[str] = field(default_factory=list)
    """Subset of ``components`` that are triggers (i.e. node had a ``trigger`` block)."""

    node_names_by_id: dict[str, str] = field(default_factory=dict)
    """Node id → component/trigger name. Used by graph traversal evaluators."""

    graph: dict[str, set[str]] = field(default_factory=dict)
    """Adjacency list keyed by source id."""


def process_canvas(parsed: dict[str, Any]) -> CanvasShape:
    """Parse ``spec.nodes`` and ``spec.edges`` into a flat shape.

    Recognizes the form the real CLI emits today: each node has either a
    ``trigger.name`` (trigger node) or a ``component.name`` (action node), and
    edges live under ``spec.edges`` with ``sourceId`` / ``targetId`` keys.
    """
    spec = parsed.get("spec") or {}
    shape = CanvasShape()

    for node in spec.get("nodes") or []:
        if not isinstance(node, dict):
            continue
        node_id = node.get("id")
        if not isinstance(node_id, str) or not node_id:
            continue
        name = _node_name(node)
        if not name:
            continue
        shape.components.append(name)
        shape.node_names_by_id[node_id] = name
        shape.graph.setdefault(node_id, set())
        # A node is a trigger if it has any non-empty `trigger` key (object or scalar).
        trig = node.get("trigger")
        if (isinstance(trig, dict) and trig) or (isinstance(trig, str) and trig):
            shape.triggers.append(name)

    for edge in spec.get("edges") or []:
        if not isinstance(edge, dict):
            continue
        src = edge.get("sourceId")
        dst = edge.get("targetId")
        if src in shape.node_names_by_id and dst in shape.node_names_by_id:
            shape.graph[src].add(dst)

    return shape


_NAME_KEYS = ("trigger", "action", "component")


def _node_name(node: dict[str, Any]) -> str | None:
    """Return the component/trigger name for a node, or None if it can't be resolved.

    Accepts every shape the agent and CLI emit:
      - ``trigger: {name: foo}`` / ``trigger: foo``  — trigger nodes
      - ``action:  {name: foo}`` / ``action: foo``   — action nodes (v0.18.0+ terminology)
      - ``component: {name: foo}`` / ``component: foo`` — legacy/templates
    """
    for key in _NAME_KEYS:
        value = node.get(key)
        if isinstance(value, dict):
            name = value.get("name")
            if isinstance(name, str) and name:
                return name
        elif isinstance(value, str) and value:
            return value
    return None


def parsed_canvas_yaml(result: CaseResult) -> dict[str, Any] | None:
    """Return the parsed canvas YAML for a case, or None if no YAML was written.

    Re-parses on every call. Each canvas evaluator independently calls this; for our
    case sizes (KB-scale YAML, ~5 evaluators per case) the cost is microseconds and
    not worth the lifecycle complexity of a memoization cache.
    """
    yamls = result.yaml_files_written()
    if not yamls:
        return None
    # Last YAML written wins; in practice cases write one canvas.yaml.
    content = list(yamls.values())[-1]
    try:
        parsed = yaml.safe_load(content)
    except yaml.YAMLError:
        return None
    return parsed if isinstance(parsed, dict) else None


def shape_for(result: CaseResult) -> CanvasShape | None:
    """Convenience: parsed YAML → CanvasShape, or None if no YAML / unparseable."""
    parsed = parsed_canvas_yaml(result)
    return process_canvas(parsed) if parsed is not None else None
