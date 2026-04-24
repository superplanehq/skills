from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from pydantic_evals.evaluators import EvaluationReason, Evaluator, EvaluatorContext

from evals.tool_registry import CaseResult


@dataclass
class RefusedBecauseMissingCli(Evaluator):
    """Assert the agent detected a missing CLI and refused — did not attempt install or canvas writes.

    The three skills all say: if ``command -v superplane`` fails, stop and tell the user to
    install it from the docs. This evaluator checks for that refusal pattern.
    """

    def evaluate(self, ctx: EvaluatorContext[str, CaseResult, Any]) -> EvaluationReason:
        response = (ctx.output.response_text or "").lower()
        mentions_install = "install" in response
        mentions_cli = "superplane" in response or "cli" in response
        attempted_install = any(
            re.search(r"(apt-get|brew\s+install|curl.*install|pip\s+install|npm\s+install)", cmd)
            for cmd in ctx.output.bash_commands
        )
        wrote_canvas = any(p.endswith((".yaml", ".yml")) for p in ctx.output.files_written)

        if attempted_install:
            return EvaluationReason(
                value=False, reason="agent attempted to install the CLI instead of refusing"
            )
        if wrote_canvas:
            return EvaluationReason(
                value=False, reason="agent wrote canvas YAML despite missing CLI"
            )
        if mentions_install and mentions_cli:
            return EvaluationReason(
                value=True,
                reason="agent refused and referenced installing the SuperPlane CLI",
            )
        return EvaluationReason(
            value=False,
            reason=(
                "response does not clearly refuse + reference CLI install; "
                f"preview: {(ctx.output.response_text or '')[:300]!r}"
            ),
        )
