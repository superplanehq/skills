"""Spawn Claude via claude-agent-sdk with the repo's skills loaded, record tool uses.

Runs inside the eval docker container. The real `superplane` CLI is already on PATH
and pre-connected via `scripts/bootstrap-token.sh`, so each case's Claude can just
run CLI commands against the running superplane-demo service.

Per-case flow:
  1. Make an isolated tempdir (scratch space for canvas.yaml etc.).
  2. Mount ``skills/superplane-*`` at ``<tempdir>/.claude/skills/*`` via symlink so
     Claude Code discovers them as project-level skills.
  3. Optionally strip `superplane` from PATH (for the missing-CLI refusal case).
  4. Drive ``claude_agent_sdk.query()`` and record every tool use into a ``CaseResult``.
"""
from __future__ import annotations

import os
import shutil
import tempfile
import time
from pathlib import Path
from typing import Any

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
    """Symlink each skill directory into ``<tempdir>/.claude/skills/``.

    claude-agent-sdk discovers project-level skills at ``.claude/skills/<name>/SKILL.md``.
    """
    target_root = tempdir / ".claude" / "skills"
    target_root.mkdir(parents=True, exist_ok=True)
    for skill_dir in SKILLS_DIR.iterdir():
        if not skill_dir.is_dir():
            continue
        link = target_root / skill_dir.name
        if link.exists() or link.is_symlink():
            link.unlink()
        link.symlink_to(skill_dir)


def _path_without_superplane() -> str:
    """PATH with any directory containing a `superplane` binary removed.

    Used by the missing-CLI refusal case so `command -v superplane` fails.
    """
    original = os.environ.get("PATH", "")
    kept: list[str] = []
    for entry in original.split(os.pathsep):
        if not entry:
            continue
        candidate = Path(entry) / "superplane"
        if candidate.exists():
            continue
        kept.append(entry)
    return os.pathsep.join(kept) if kept else "/usr/bin:/bin"


def _record_assistant_message(msg: AssistantMessage, result: CaseResult) -> None:
    text_chunks: list[str] = []
    for block in msg.content:
        if isinstance(block, ToolUseBlock):
            tool_name = block.name
            tool_input = dict(block.input) if isinstance(block.input, dict) else {}
            result.tool_uses.append({"name": tool_name, "input": tool_input})
            if tool_name == "Bash":
                cmd = tool_input.get("command", "")
                if isinstance(cmd, str) and cmd:
                    result.bash_commands.append(cmd)
            elif tool_name == "Write":
                path = tool_input.get("file_path", "")
                content = tool_input.get("content", "")
                if isinstance(path, str) and path:
                    result.files_written[path] = content if isinstance(content, str) else ""
            elif tool_name == "Edit":
                path = tool_input.get("file_path", "")
                new_content = tool_input.get("new_string", "")
                old = tool_input.get("old_string", "")
                if isinstance(path, str) and path:
                    prior = result.files_written.get(path, "")
                    if isinstance(prior, str) and isinstance(old, str) and old in prior:
                        result.files_written[path] = prior.replace(
                            old, new_content if isinstance(new_content, str) else "", 1
                        )
                    else:
                        result.files_written[path] = (
                            new_content if isinstance(new_content, str) else ""
                        )
        elif isinstance(block, TextBlock):
            text_chunks.append(block.text)
    if text_chunks:
        result.response_text = "\n".join(text_chunks)


async def run_case(
    prompt: str,
    *,
    model: str,
    strip_cli: bool = False,
    max_turns: int = 20,
) -> CaseResult:
    """Run one eval case end-to-end and return the recorded ``CaseResult``.

    ``strip_cli=True`` removes `superplane` from PATH for this case so
    `command -v superplane` fails — used by the "missing CLI" refusal test.
    """
    result = CaseResult()
    tempdir = Path(tempfile.mkdtemp(prefix="skills-eval-"))
    try:
        _mount_skills(tempdir)

        # Inherit parent env (SUPERPLANE_URL, API token config, ANTHROPIC_API_KEY, etc.)
        # and override PATH only if the case needs a missing CLI.
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
                    result.cost_usd = getattr(msg, "total_cost_usd", None)
                    result.num_turns = getattr(msg, "num_turns", 0) or 0
                    usage = getattr(msg, "usage", None) or {}
                    if isinstance(usage, dict):
                        result.input_tokens = int(usage.get("input_tokens") or 0)
                        result.output_tokens = int(usage.get("output_tokens") or 0)
                        result.cache_read_tokens = int(
                            usage.get("cache_read_input_tokens") or 0
                        )
                        result.cache_write_tokens = int(
                            usage.get("cache_creation_input_tokens") or 0
                        )
                    if getattr(msg, "is_error", False):
                        result.task_failed = True
                        result.error_message = getattr(msg, "result", None) or "agent error"
        except Exception as err:  # noqa: BLE001 — harness boundary
            result.task_failed = True
            result.error_message = f"{type(err).__name__}: {err}"
        finally:
            result.duration_s = time.perf_counter() - started

        return result
    finally:
        shutil.rmtree(tempdir, ignore_errors=True)


def parsed_canvas_yaml(result: CaseResult) -> dict[str, Any] | None:
    """Return the parsed canvas YAML content if a YAML file was written.

    Evaluators that inspect canvas structure call this to get a ``spec`` dict.
    """
    import yaml

    yamls = result.yaml_files_written()
    if not yamls:
        return None
    preferred = {p: c for p, c in yamls.items() if "canvas" in Path(p).name.lower()}
    candidates = preferred or yamls
    content = list(candidates.values())[-1]
    try:
        parsed = yaml.safe_load(content)
    except yaml.YAMLError:
        return None
    return parsed if isinstance(parsed, dict) else None
