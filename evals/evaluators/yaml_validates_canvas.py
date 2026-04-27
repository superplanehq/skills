from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pydantic_evals.evaluators import EvaluationReason, Evaluator, EvaluatorContext

from evals.evaluators.canvas_shape import parsed_canvas_yaml
from evals.tool_registry import CaseResult

_REQUIRED_KEYS = ("apiVersion", "kind", "metadata", "spec")


@dataclass
class YamlValidatesCanvas(Evaluator):
    """Assert the agent wrote a YAML file shaped like a Canvas resource."""

    def evaluate(self, ctx: EvaluatorContext[str, CaseResult, Any]) -> EvaluationReason:
        parsed = parsed_canvas_yaml(ctx.output)
        if parsed is None:
            return EvaluationReason(value=False, reason="no parseable canvas YAML")
        missing = [k for k in _REQUIRED_KEYS if k not in parsed]
        if missing:
            return EvaluationReason(value=False, reason=f"YAML missing keys: {missing}")
        if str(parsed.get("kind", "")).lower() != "canvas":
            return EvaluationReason(
                value=False, reason=f"YAML kind is {parsed.get('kind')!r}, expected 'Canvas'"
            )
        return EvaluationReason(value=True, reason="YAML parses as a Canvas resource")
