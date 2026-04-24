from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from pydantic_evals.evaluators import EvaluationReason, Evaluator, EvaluatorContext

from evals.tool_registry import CaseResult


@dataclass
class BashCommandsInOrder(Evaluator):
    """Assert the agent ran bash commands matching each pattern, in the given order.

    Patterns must appear in order but may be interleaved with other commands.
    """

    patterns: list[str] = field(default_factory=list)

    def evaluate(self, ctx: EvaluatorContext[str, CaseResult, Any]) -> EvaluationReason:
        regexes = [re.compile(p) for p in self.patterns]
        idx = 0
        first_match_at: list[int | None] = [None] * len(regexes)
        for i, cmd in enumerate(ctx.output.bash_commands):
            if idx >= len(regexes):
                break
            if regexes[idx].search(cmd):
                first_match_at[idx] = i
                idx += 1
        if idx == len(regexes):
            return EvaluationReason(
                value=True,
                reason=f"All {len(regexes)} pattern(s) matched in order at indices {first_match_at}",
            )
        missing = self.patterns[idx:]
        return EvaluationReason(
            value=False,
            reason=(
                f"Matched {idx}/{len(regexes)} patterns in order; missing (in order): {missing!r}. "
                f"Observed bash calls: {ctx.output.bash_commands[:15]!r}"
            ),
        )
