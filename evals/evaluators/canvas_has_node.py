from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pydantic_evals.evaluators import EvaluationReason, Evaluator, EvaluatorContext

from evals.harness import parsed_canvas_yaml
from evals.tool_registry import CaseResult


def _node_components(parsed: dict[str, Any]) -> list[str]:
    """Return the list of component names from nodes in the parsed canvas YAML.

    Looks at ``spec.nodes[*].component.name`` (the shape used in canvas-yaml-spec).
    Falls back to ``node.block`` if set.
    """
    spec = parsed.get("spec") or {}
    nodes = spec.get("nodes") or []
    components: list[str] = []
    if not isinstance(nodes, list):
        return components
    for node in nodes:
        if not isinstance(node, dict):
            continue
        comp = node.get("component") or {}
        if isinstance(comp, dict):
            name = comp.get("name")
            if isinstance(name, str) and name:
                components.append(name)
                continue
        block = node.get("block")
        if isinstance(block, str) and block:
            components.append(block)
    return components


@dataclass
class CanvasHasNode(Evaluator):
    """Assert the written canvas YAML has ``count`` node(s) with component name ``node``."""

    node: str
    count: int = 1

    def evaluate(self, ctx: EvaluatorContext[str, CaseResult, Any]) -> EvaluationReason:
        parsed = parsed_canvas_yaml(ctx.output)
        if parsed is None:
            return EvaluationReason(value=False, reason="no parseable canvas YAML")
        components = _node_components(parsed)
        observed = components.count(self.node)
        if observed == self.count:
            return EvaluationReason(
                value=True,
                reason=f"node {self.node!r} found {observed} time(s) as expected",
            )
        return EvaluationReason(
            value=False,
            reason=(
                f"node {self.node!r} found {observed} time(s), expected {self.count}. "
                f"Components in canvas: {components!r}"
            ),
        )
