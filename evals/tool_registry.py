"""Per-case recorder for bash commands, file writes, tool uses, and final response text.

The harness fills a ``CaseResult`` from streamed agent messages; evaluators read from it.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class CaseResult:
    """Structured record of everything a Claude eval run did.

    Passed to pydantic-evals as the per-case output; evaluators read from it.
    """

    bash_commands: list[str] = field(default_factory=list)
    """Every shell command Claude ran via the Bash tool, in order."""

    files_written: dict[str, str] = field(default_factory=dict)
    """Map of absolute path -> final file content, for Write/Edit tool uses.
    Later writes to the same path overwrite earlier ones."""

    tool_uses: list[dict] = field(default_factory=list)
    """Raw ordered list of {"name": str, "input": dict} for every tool call."""

    response_text: str = ""
    """Final assistant message text (concatenated text blocks from the last turn)."""

    cost_usd: float | None = None
    """Cost reported by claude-agent-sdk (from ResultMessage.total_cost_usd if available)."""

    duration_s: float = 0.0
    """Wall-clock duration of this case's agent query, in seconds."""

    num_turns: int = 0
    """Number of assistant turns (from ResultMessage.num_turns)."""

    input_tokens: int = 0
    """Input tokens billed (from ResultMessage.usage.input_tokens)."""

    output_tokens: int = 0
    """Output tokens billed (from ResultMessage.usage.output_tokens)."""

    cache_read_tokens: int = 0
    """Cache-read tokens (from ResultMessage.usage.cache_read_input_tokens)."""

    cache_write_tokens: int = 0
    """Cache-creation tokens (from ResultMessage.usage.cache_creation_input_tokens)."""

    task_failed: bool = False
    """True if the agent harness raised an exception before producing a final response."""

    error_message: str | None = None
    """Populated when task_failed is True."""

    @property
    def tool_calls(self) -> int:
        """Total number of tool invocations in this case."""
        return len(self.tool_uses)

    def yaml_files_written(self) -> dict[str, str]:
        """Subset of ``files_written`` whose paths end in .yaml or .yml."""
        return {
            path: content
            for path, content in self.files_written.items()
            if path.endswith((".yaml", ".yml"))
        }

    def bash_matches(self, pattern: str) -> int:
        """Count bash commands matching a regex pattern."""
        import re

        regex = re.compile(pattern)
        return sum(1 for cmd in self.bash_commands if regex.search(cmd))
