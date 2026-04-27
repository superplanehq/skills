from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pydantic_evals.evaluators import EvaluationReason, Evaluator, EvaluatorContext

from evals.evaluators.canvas_shape import shape_for
from evals.tool_registry import CaseResult


@dataclass
class CanvasHasTrigger(Evaluator):
    """Assert the canvas has a node configured as the named trigger."""

    trigger: str

    def evaluate(self, ctx: EvaluatorContext[str, CaseResult, Any]) -> EvaluationReason:
        shape = shape_for(ctx.output)
        if shape is None:
            return EvaluationReason(value=False, reason="no parseable canvas YAML")
        if self.trigger in shape.triggers:
            return EvaluationReason(value=True, reason=f"trigger {self.trigger!r} found")
        return EvaluationReason(
            value=False,
            reason=f"trigger {self.trigger!r} not found; canvas triggers: {shape.triggers!r}",
        )
