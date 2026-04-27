from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from pydantic_evals.evaluators import EvaluationReason, Evaluator, EvaluatorContext

from evals.tool_registry import CaseResult


@dataclass
class BashCommandCalled(Evaluator):
    """Assert at least ``min_calls`` Bash commands matched ``pattern``."""

    pattern: str
    min_calls: int = 1

    def evaluate(self, ctx: EvaluatorContext[str, CaseResult, Any]) -> EvaluationReason:
        regex = re.compile(self.pattern)
        count = sum(1 for cmd in ctx.output.bash_commands if regex.search(cmd))
        if count >= self.min_calls:
            return EvaluationReason(
                value=True,
                reason=f"pattern {self.pattern!r} matched {count} bash call(s) (min {self.min_calls})",
            )
        return EvaluationReason(
            value=False,
            reason=(
                f"pattern {self.pattern!r} matched {count} bash call(s); "
                f"expected at least {self.min_calls}. Observed: {ctx.output.bash_commands[:10]!r}"
            ),
        )


@dataclass
class BashCommandNotCalled(Evaluator):
    """Assert no Bash command matched ``pattern``."""

    pattern: str

    def evaluate(self, ctx: EvaluatorContext[str, CaseResult, Any]) -> EvaluationReason:
        regex = re.compile(self.pattern)
        matches = [cmd for cmd in ctx.output.bash_commands if regex.search(cmd)]
        if not matches:
            return EvaluationReason(value=True, reason=f"pattern {self.pattern!r} never matched")
        return EvaluationReason(
            value=False, reason=f"pattern {self.pattern!r} unexpectedly matched: {matches!r}"
        )
