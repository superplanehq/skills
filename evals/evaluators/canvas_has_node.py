from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pydantic_evals.evaluators import EvaluationReason, Evaluator, EvaluatorContext

from evals.evaluators.canvas_shape import shape_for
from evals.tool_registry import CaseResult


@dataclass
class CanvasHasNode(Evaluator):
    """Assert the canvas has ``count`` nodes whose component name is ``node``."""

    node: str
    count: int = 1

    def evaluate(self, ctx: EvaluatorContext[str, CaseResult, Any]) -> EvaluationReason:
        shape = shape_for(ctx.output)
        if shape is None:
            return EvaluationReason(value=False, reason="no parseable canvas YAML")
        observed = shape.components.count(self.node)
        if observed == self.count:
            return EvaluationReason(
                value=True, reason=f"node {self.node!r} found {observed} time(s)"
            )
        return EvaluationReason(
            value=False,
            reason=(
                f"node {self.node!r} found {observed} time(s), expected {self.count}. "
                f"Components: {shape.components!r}"
            ),
        )
