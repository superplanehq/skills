"""Spawn Claude via claude-agent-sdk with the repo's skills loaded; record tool uses."""
from __future__ import annotations

import os
import shutil
import tempfile
import time
from pathlib import Path

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ResultMessage,
    TextBlock,
    ToolUseBlock,
    query,
)

from evals.tool_registry import CaseResult

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "skills"


def _mount_skills(tempdir: Path) -> None:
    """Symlink each skill into ``<tempdir>/.claude/skills/`` (where the SDK looks)."""
    target_root = tempdir / ".claude" / "skills"
    target_root.mkdir(parents=True, exist_ok=True)
    for skill_dir in SKILLS_DIR.iterdir():
        if not skill_dir.is_dir():
            continue
        link = target_root / skill_dir.name
        link.unlink(missing_ok=True)
        link.symlink_to(skill_dir)


def _path_without_superplane() -> str:
    """PATH with any directory containing a ``superplane`` binary removed.

    Used by the missing-CLI refusal case so ``command -v superplane`` returns nothing.
    """
    path = os.environ.get("PATH", "")
    found = shutil.which("superplane", path=path)
    while found:
        owning_dir = str(Path(found).parent)
        path = os.pathsep.join(p for p in path.split(os.pathsep) if p != owning_dir)
        found = shutil.which("superplane", path=path) if path else None
    return path


def _record_assistant_message(msg: AssistantMessage, result: CaseResult) -> None:
    text_chunks: list[str] = []
    for block in msg.content:
        if isinstance(block, TextBlock):
            text_chunks.append(block.text)
            continue
        if not isinstance(block, ToolUseBlock):
            continue
        tool_input = dict(block.input) if isinstance(block.input, dict) else {}
        result.tool_uses.append({"name": block.name, "input": tool_input})
        if block.name == "Bash":
            cmd = tool_input.get("command")
            if isinstance(cmd, str) and cmd:
                result.bash_commands.append(cmd)
        elif block.name == "Write":
            path = tool_input.get("file_path")
            content = tool_input.get("content", "")
            if isinstance(path, str) and path:
                result.files_written[path] = content if isinstance(content, str) else ""
        elif block.name == "Edit":
            path = tool_input.get("file_path")
            old = tool_input.get("old_string", "")
            new = tool_input.get("new_string", "")
            if not isinstance(path, str) or not path:
                continue
            prior = result.files_written.get(path, "")
            if isinstance(prior, str) and isinstance(old, str) and old in prior:
                result.files_written[path] = prior.replace(old, new if isinstance(new, str) else "", 1)
            else:
                # No prior Write seen — record what we have so evaluators see something.
                result.files_written[path] = new if isinstance(new, str) else ""
    if text_chunks:
        result.response_text = "\n".join(text_chunks)


def _record_result_message(msg: ResultMessage, result: CaseResult) -> None:
    result.cost_usd = getattr(msg, "total_cost_usd", None)
    result.num_turns = getattr(msg, "num_turns", 0) or 0
    usage = getattr(msg, "usage", None) or {}
    if isinstance(usage, dict):
        result.input_tokens = int(usage.get("input_tokens") or 0)
        result.output_tokens = int(usage.get("output_tokens") or 0)
        result.cache_read_tokens = int(usage.get("cache_read_input_tokens") or 0)
        result.cache_write_tokens = int(usage.get("cache_creation_input_tokens") or 0)
    if getattr(msg, "is_error", False):
        result.task_failed = True
        result.error_message = getattr(msg, "result", None) or "agent error"


async def run_case(
    prompt: str,
    *,
    model: str,
    strip_cli: bool = False,
    max_turns: int = 20,
) -> CaseResult:
    """Run one eval case end-to-end and return the recorded ``CaseResult``."""
    result = CaseResult()
    tempdir = Path(tempfile.mkdtemp(prefix="skills-eval-"))
    try:
        _mount_skills(tempdir)

        case_env = dict(os.environ)
        if strip_cli:
            case_env["PATH"] = _path_without_superplane()

        options = ClaudeAgentOptions(
            cwd=str(tempdir),
            model=model,
            allowed_tools=["Bash", "Read", "Write", "Edit", "Glob", "Grep"],
            permission_mode="bypassPermissions",
            max_turns=max_turns,
            setting_sources=["project"],
            skills="all",
            env=case_env,
        )

        started = time.perf_counter()
        try:
            async for msg in query(prompt=prompt, options=options):
                if isinstance(msg, AssistantMessage):
                    _record_assistant_message(msg, result)
                elif isinstance(msg, ResultMessage):
                    _record_result_message(msg, result)
        except Exception as err:  # noqa: BLE001 — harness boundary
            result.task_failed = True
            result.error_message = f"{type(err).__name__}: {err}"
        finally:
            result.duration_s = time.perf_counter() - started

        return result
    finally:
        shutil.rmtree(tempdir, ignore_errors=True)
