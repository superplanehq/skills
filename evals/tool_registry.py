"""Per-case record of everything Claude did during one eval run."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class CaseResult:
    """Structured output of one eval case. Becomes ``ctx.output`` in pydantic-evals."""

    bash_commands: list[str] = field(default_factory=list)
    files_written: dict[str, str] = field(default_factory=dict)
    """Path → final content. Later writes to the same path overwrite earlier ones."""

    tool_uses: list[dict] = field(default_factory=list)
    response_text: str = ""
    cost_usd: float | None = None
    duration_s: float = 0.0
    num_turns: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0

    task_failed: bool = False
    """True if the harness raised before the agent produced a final response.

    Distinct from "the agent decided to refuse" — that's a successful run with the
    refusal as response_text.
    """
    error_message: str | None = None

    @property
    def tool_calls(self) -> int:
        return len(self.tool_uses)

    def yaml_files_written(self) -> dict[str, str]:
        return {p: c for p, c in self.files_written.items() if p.endswith((".yaml", ".yml"))}
