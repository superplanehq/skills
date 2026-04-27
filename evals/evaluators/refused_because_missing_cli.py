from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from pydantic_evals.evaluators import EvaluationReason, Evaluator, EvaluatorContext

from evals.tool_registry import CaseResult

_INSTALL_ATTEMPT = re.compile(r"(apt-get|brew\s+install|curl.*install|pip\s+install|npm\s+install)")


@dataclass
class RefusedBecauseMissingCli(Evaluator):
    """The skills say: if ``command -v superplane`` fails, stop and tell the user.

    This evaluator checks all three contracts: the agent didn't try to install,
    didn't write canvas YAML, and the response references the CLI install.
    """

    def evaluate(self, ctx: EvaluatorContext[str, CaseResult, Any]) -> EvaluationReason:
        result = ctx.output

        if any(_INSTALL_ATTEMPT.search(cmd) for cmd in result.bash_commands):
            return EvaluationReason(
                value=False, reason="agent attempted to install the CLI instead of refusing"
            )
        if any(p.endswith((".yaml", ".yml")) for p in result.files_written):
            return EvaluationReason(
                value=False, reason="agent wrote canvas YAML despite missing CLI"
            )

        response = (result.response_text or "").lower()
        if "install" in response and ("superplane" in response or "cli" in response):
            return EvaluationReason(
                value=True, reason="agent refused and referenced installing the SuperPlane CLI"
            )
        return EvaluationReason(
            value=False,
            reason=f"response missing install + CLI reference; preview: {response[:300]!r}",
        )
