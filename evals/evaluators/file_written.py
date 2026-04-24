from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from pydantic_evals.evaluators import EvaluationReason, Evaluator, EvaluatorContext

from evals.tool_registry import CaseResult


@dataclass
class FileWritten(Evaluator):
    """Assert the agent wrote (via Write/Edit) at least one file whose path matches ``path_pattern``."""

    path_pattern: str

    def evaluate(self, ctx: EvaluatorContext[str, CaseResult, Any]) -> EvaluationReason:
        regex = re.compile(self.path_pattern)
        matches = [p for p in ctx.output.files_written if regex.search(p)]
        if matches:
            return EvaluationReason(
                value=True, reason=f"file(s) matching {self.path_pattern!r}: {matches}"
            )
        return EvaluationReason(
            value=False,
            reason=(
                f"no file matched {self.path_pattern!r}; "
                f"files written: {list(ctx.output.files_written)!r}"
            ),
        )


@dataclass
class FileNotWritten(Evaluator):
    """Assert no file matching ``path_pattern`` was written."""

    path_pattern: str

    def evaluate(self, ctx: EvaluatorContext[str, CaseResult, Any]) -> EvaluationReason:
        regex = re.compile(self.path_pattern)
        matches = [p for p in ctx.output.files_written if regex.search(p)]
        if not matches:
            return EvaluationReason(value=True, reason=f"no file matched {self.path_pattern!r}")
        return EvaluationReason(
            value=False, reason=f"unexpected file(s) matched: {matches}"
        )
