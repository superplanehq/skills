from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from pydantic_evals.evaluators import EvaluationReason, Evaluator, EvaluatorContext

from evals.tool_registry import CaseResult


@dataclass
class FileContentMatches(Evaluator):
    """Assert at least one written file whose path matches ``path_pattern`` has content matching ``content_pattern``."""

    path_pattern: str
    content_pattern: str

    def evaluate(self, ctx: EvaluatorContext[str, CaseResult, Any]) -> EvaluationReason:
        path_re = re.compile(self.path_pattern)
        content_re = re.compile(self.content_pattern)
        candidates = {p: c for p, c in ctx.output.files_written.items() if path_re.search(p)}
        if not candidates:
            return EvaluationReason(
                value=False,
                reason=(
                    f"no file matched path {self.path_pattern!r}; "
                    f"files written: {list(ctx.output.files_written)!r}"
                ),
            )
        hits = [p for p, c in candidates.items() if content_re.search(c)]
        if hits:
            return EvaluationReason(
                value=True,
                reason=f"content pattern {self.content_pattern!r} found in {hits}",
            )
        return EvaluationReason(
            value=False,
            reason=(
                f"content pattern {self.content_pattern!r} not found in any of "
                f"{list(candidates)!r}"
            ),
        )


@dataclass
class FileContentNotMatches(Evaluator):
    """Assert no written file whose path matches ``path_pattern`` contains ``content_pattern``."""

    path_pattern: str
    content_pattern: str

    def evaluate(self, ctx: EvaluatorContext[str, CaseResult, Any]) -> EvaluationReason:
        path_re = re.compile(self.path_pattern)
        content_re = re.compile(self.content_pattern)
        offenders = [
            p for p, c in ctx.output.files_written.items()
            if path_re.search(p) and content_re.search(c)
        ]
        if not offenders:
            return EvaluationReason(
                value=True,
                reason=f"content pattern {self.content_pattern!r} never matched any file with path {self.path_pattern!r}",
            )
        return EvaluationReason(
            value=False,
            reason=(
                f"content pattern {self.content_pattern!r} unexpectedly matched in {offenders!r}"
            ),
        )
