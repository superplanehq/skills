from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pydantic_evals.evaluators import EvaluationReason, Evaluator, EvaluatorContext

from evals.harness import parsed_canvas_yaml
from evals.tool_registry import CaseResult


@dataclass
class YamlValidatesCanvas(Evaluator):
    """Assert the written YAML parses and has the shape of a Canvas resource.

    Checks: ``apiVersion``, ``kind: Canvas`` (case-insensitive), ``metadata``, ``spec`` keys.
    """

    def evaluate(self, ctx: EvaluatorContext[str, CaseResult, Any]) -> EvaluationReason:
        parsed = parsed_canvas_yaml(ctx.output)
        if parsed is None:
            return EvaluationReason(
                value=False,
                reason="no YAML file was written, or the YAML did not parse as a mapping",
            )
        missing = [k for k in ("apiVersion", "kind", "metadata", "spec") if k not in parsed]
        if missing:
            return EvaluationReason(
                value=False, reason=f"YAML missing required top-level keys: {missing}"
            )
        kind = str(parsed.get("kind", "")).lower()
        if kind != "canvas":
            return EvaluationReason(
                value=False, reason=f"YAML kind is {parsed.get('kind')!r}, expected 'Canvas'"
            )
        return EvaluationReason(value=True, reason="YAML parses as a Canvas resource")
