"""Async entrypoint for the skills eval suite.

Usage (via Makefile):
  make evals                              # run all cases
  make evals CASES=push_to_slack,cancel_flow
  EVAL_MODEL=claude-opus-4-7 make evals
  make evals.cli | .canvas | .monitor     # per-skill subsets

Or directly:
  uv run python -m evals.runner --list
  uv run python -m evals.runner --skill superplane-cli
  uv run python -m evals.runner --cases whoami_basic
"""
from __future__ import annotations

import asyncio
import os
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic_evals import Dataset

from evals.case_filter import case_filter, filter_by_skill, select_cases
from evals.case_logger import CaseLogger
from evals.cases import dataset
from evals.harness import run_case
from evals.report import ReportBuilder
from evals.tool_registry import CaseResult

REPORTS_ROOT = Path(__file__).resolve().parent / "reports"
LOGS_ROOT = Path(__file__).resolve().parent.parent / "tmp" / "evals"


def _print_list(cases: list[Any]) -> None:
    for c in cases:
        skill = (c.metadata or {}).get("skill", "?")
        print(f"{c.name}\t{skill}")


def _build_task(logger: CaseLogger, model: str, case_name_by_inputs: dict[str, str]) -> Any:
    """Return the pydantic-evals-compatible task callable.

    pydantic-evals calls the task with each case's ``inputs`` and expects ``CaseResult``.
    Per-case metadata (``strip_cli``) drives harness flags.
    """
    name_by_inputs = case_name_by_inputs
    strip_cli_by_inputs: dict[str, bool] = {
        c.inputs: bool((c.metadata or {}).get("strip_cli", False)) for c in dataset.cases
    }

    async def task(inputs: str) -> CaseResult:
        case_name = name_by_inputs.get(inputs, "unknown")
        strip_cli = strip_cli_by_inputs.get(inputs, False)
        await logger.log_case(case_name, f"START inputs={inputs!r} strip_cli={strip_cli}")
        result = await run_case(inputs, model=model, strip_cli=strip_cli)
        await logger.log_case(
            case_name,
            f"END bash_commands={len(result.bash_commands)} "
            f"files={len(result.files_written)} cost={result.cost_usd} "
            f"duration={result.duration_s:.1f}s",
        )
        for cmd in result.bash_commands:
            await logger.log_case(case_name, f"bash: {cmd}")
        for path in result.files_written:
            await logger.log_case(case_name, f"wrote: {path}")
        if result.task_failed:
            await logger.log_case(case_name, f"FAILED: {result.error_message}")
        return result

    return task


async def main_async(
    selected: list[str] | None, skill: str | None, list_only: bool
) -> int:
    all_cases = list(dataset.cases)
    if skill:
        all_cases = filter_by_skill(all_cases, skill)
    if list_only:
        _print_list(all_cases)
        return 0

    cases = select_cases(all_cases, selected)
    if not cases:
        print("No cases match the given filters.", file=sys.stderr)
        return 2

    model = os.environ.get("EVAL_MODEL", "claude-haiku-4-5").strip() or "claude-haiku-4-5"
    run_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%S_%fZ")
    logger = CaseLogger(run_id=run_id, case_names=[c.name for c in cases], output_root=LOGS_ROOT)

    name_by_inputs = {c.inputs: c.name for c in cases}
    eval_dataset = Dataset(name="skills", cases=cases, evaluators=dataset.evaluators)
    task = _build_task(logger, model, name_by_inputs)

    wall_start = time.perf_counter()
    try:
        report = await eval_dataset.evaluate(task, progress=True)
    finally:
        logger.close()
    wall_seconds = time.perf_counter() - wall_start

    case_skill_by_name = {
        c.name: (c.metadata or {}).get("skill", "—") for c in cases
    }
    builder = ReportBuilder(
        report,
        model=model,
        evaluate_wall_seconds=wall_seconds,
        case_names=[c.name for c in cases],
        interaction_log_paths_by_case_name=logger.display_paths_by_case_name,
        output_root=REPORTS_ROOT / run_id,
        case_skill_by_name=case_skill_by_name,
    )
    summary = builder.render()
    # Exit non-zero if any assertions failed — makes Semaphore/local CI fail-fast.
    failed = summary["assertions_total"] - summary["assertions_passed"]
    return 0 if failed == 0 else 1


def main(argv: list[str] | None = None) -> int:
    selected, skill, list_only = case_filter(argv)
    return asyncio.run(main_async(selected, skill, list_only))


if __name__ == "__main__":
    sys.exit(main())
