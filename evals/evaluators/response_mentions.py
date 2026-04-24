from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pydantic_evals.evaluators import EvaluationReason, Evaluator, EvaluatorContext

from evals.tool_registry import CaseResult


@dataclass
class ResponseMentions(Evaluator):
    """Assert the final assistant text contains ``phrase`` (case-insensitive by default)."""

    phrase: str
    case_insensitive: bool = True

    def evaluate(self, ctx: EvaluatorContext[str, CaseResult, Any]) -> EvaluationReason:
        haystack = ctx.output.response_text or ""
        needle = self.phrase
        if self.case_insensitive:
            haystack, needle = haystack.lower(), needle.lower()
        if needle in haystack:
            return EvaluationReason(value=True, reason=f"response mentions {self.phrase!r}")
        preview = (ctx.output.response_text or "")[:300]
        return EvaluationReason(
            value=False,
            reason=f"response does not mention {self.phrase!r}. Preview: {preview!r}",
        )
