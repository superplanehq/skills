"""Async entrypoint for the skills eval suite.

Usage:
  uv run python -m evals.runner --list
  uv run python -m evals.runner --skill superplane-cli
  uv run python -m evals.runner --cases whoami_basic,push_to_slack

Or via Makefile: ``make evals``, ``make evals CASES=...``, ``make evals SKILL=...``.
"""
from __future__ import annotations

import asyncio
import os
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic_evals import Case, Dataset

from evals.case_filter import case_filter, filter_by_skill, select_cases
from evals.case_logger import CaseLogger
from evals.cases import dataset
from evals.harness import run_case
from evals.report import ReportBuilder
from evals.tool_registry import CaseResult

REPORTS_ROOT = Path(__file__).resolve().parent / "reports"
LOGS_ROOT = Path(__file__).resolve().parent.parent / "tmp" / "evals"

# Cap parallel Claude subprocesses against the shared superplane-demo container.
# Override with EVAL_CONCURRENCY for stress testing.
DEFAULT_CONCURRENCY = 4


def _print_list(cases: list[Case]) -> None:
    for c in cases:
        skill = (c.metadata or {}).get("skill", "?")
        print(f"{c.name}\t{skill}")


def _build_task(
    logger: CaseLogger, model: str, cases: list[Case]
) -> Any:
    """Wrap ``harness.run_case`` so pydantic-evals can call it per case.

    The dataset passes ``inputs`` (the prompt string) to the task; we look up the
    matching ``Case`` to pull metadata flags.
    """
    case_by_name = {c.name: c for c in cases}
    name_by_inputs = {c.inputs: c.name for c in cases}

    async def task(inputs: str) -> CaseResult:
        case_name = name_by_inputs.get(inputs, "unknown")
        metadata = (case_by_name[case_name].metadata or {}) if case_name in case_by_name else {}
        strip_cli = bool(metadata.get("strip_cli"))

        await logger.log_case(case_name, f"START strip_cli={strip_cli}")
        result = await run_case(inputs, model=model, strip_cli=strip_cli)
        await logger.log_case(
            case_name,
            f"END bash_commands={len(result.bash_commands)} files={len(result.files_written)} "
            f"cost={result.cost_usd} duration={result.duration_s:.1f}s",
        )
        for cmd in result.bash_commands:
            await logger.log_case(case_name, f"bash: {cmd}")
        for path in result.files_written:
            await logger.log_case(case_name, f"wrote: {path}")
        if result.task_failed:
            await logger.log_case(case_name, f"FAILED: {result.error_message}")
        return result

    return task


async def main_async(selected: list[str] | None, skill: str | None, list_only: bool) -> int:
    cases = list(dataset.cases)
    if skill:
        cases = filter_by_skill(cases, skill)
    if list_only:
        _print_list(cases)
        return 0

    cases = select_cases(cases, selected)
    if not cases:
        print("No cases match the given filters.", file=sys.stderr)
        return 2

    model = (os.environ.get("EVAL_MODEL") or "claude-haiku-4-5").strip()
    concurrency = int(os.environ.get("EVAL_CONCURRENCY") or DEFAULT_CONCURRENCY)
    run_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%S_%fZ")
    logger = CaseLogger(run_id=run_id, case_names=[c.name for c in cases], output_root=LOGS_ROOT)

    eval_dataset = Dataset(name="skills", cases=cases, evaluators=dataset.evaluators)
    task = _build_task(logger, model, cases)

    wall_start = time.perf_counter()
    try:
        report = await eval_dataset.evaluate(task, max_concurrency=concurrency, progress=True)
    finally:
        logger.close()
    wall_seconds = time.perf_counter() - wall_start

    builder = ReportBuilder(
        report,
        model=model,
        evaluate_wall_seconds=wall_seconds,
        case_names=[c.name for c in cases],
        interaction_log_paths_by_case_name=logger.display_paths_by_case_name,
        output_root=REPORTS_ROOT / run_id,
        case_skill_by_name={c.name: (c.metadata or {}).get("skill", "—") for c in cases},
    )
    summary = builder.render()
    failed_assertions = summary["assertions_total"] - summary["assertions_passed"]
    return 0 if failed_assertions == 0 else 1


def main(argv: list[str] | None = None) -> int:
    selected, skill, list_only = case_filter(argv)
    return asyncio.run(main_async(selected, skill, list_only))


if __name__ == "__main__":
    sys.exit(main())
