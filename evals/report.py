"""Console + JSON + Markdown report for eval runs.

Two console formats, selected by ``EVAL_REPORT_FORMAT``:
  - text     : aligned-column-per-case (mirrors superplane/agent/evals/report.py)
  - markdown : per-case detail blocks + summary table at the end
  - both     : text first, then markdown (default)

A ``report.md`` and ``summary.json`` are always written to the run's output dir.
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal, Union, cast

from pydantic_evals.reporting import EvaluationReport, ReportCase, ReportCaseFailure

from evals.tool_registry import CaseResult

ReportFormat = Literal["text", "markdown", "both"]
_VALID_FORMATS: frozenset[str] = frozenset({"text", "markdown", "both"})

_ReportRow = Union[ReportCase[Any, Any, Any], ReportCaseFailure[Any, Any, Any]]


@dataclass
class _AssertionLine:
    text: str
    passed: bool


@dataclass
class _CaseRow:
    """Per-case data shared between text and markdown renderers."""

    name: str
    skill: str
    passed: bool
    task_failed: bool
    error_message: str | None
    input: str
    duration_s: float | None
    cost_usd: float | None
    tool_calls: int | None
    input_tokens: int | None
    output_tokens: int | None
    cache_read_tokens: int | None
    cache_write_tokens: int | None
    n_assertions: int
    n_passed: int
    assertion_lines: list[_AssertionLine] = field(default_factory=list)
    output_path: str = ""
    log_path: str = ""


@dataclass
class _Totals:
    task_time_s: float
    wall_time_s: float
    tool_calls: int
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int
    cache_write_tokens: int
    cost_usd: float | None
    assertions_total: int
    assertions_passed: int

    @property
    def total_time_s(self) -> float:
        return self.task_time_s + self.wall_time_s


class ReportBuilder:
    def __init__(
        self,
        report: EvaluationReport,
        *,
        model: str,
        evaluate_wall_seconds: float,
        case_names: list[str],
        interaction_log_paths_by_case_name: dict[str, str] | None = None,
        output_root: Path,
        case_skill_by_name: dict[str, str] | None = None,
    ) -> None:
        self.report = report
        self.model = model
        self.wall_seconds = evaluate_wall_seconds
        self.case_names = case_names
        self.log_paths = interaction_log_paths_by_case_name or {}
        self.output_root = output_root
        self.skills = case_skill_by_name or {}

    def render(self) -> dict[str, Any]:
        self.output_root.mkdir(parents=True, exist_ok=True)
        rows, totals, summary = self._collect()

        with (self.output_root / "summary.json").open("w", encoding="utf-8") as fh:
            json.dump(summary, fh, indent=2)
        markdown = self._render_markdown(rows, totals)
        with (self.output_root / "report.md").open("w", encoding="utf-8") as fh:
            fh.write(markdown)

        fmt = _resolve_format(os.environ.get("EVAL_REPORT_FORMAT"))
        if fmt in {"text", "both"}:
            self._print_text(rows, totals)
        if fmt in {"markdown", "both"}:
            if fmt == "both":
                print()
                print()
            print(markdown)

        return summary

    # -------- collection --------

    def _ordered_rows(self) -> list[_ReportRow]:
        by_name: dict[str, _ReportRow] = {}
        for r in self.report.cases:
            by_name[r.name] = cast(_ReportRow, r)
        for r in self.report.failures:
            by_name[r.name] = cast(_ReportRow, r)
        return [by_name[n] for n in self.case_names if n in by_name]

    def _collect(self) -> tuple[list[_CaseRow], _Totals, dict[str, Any]]:
        rows: list[_CaseRow] = []
        agg = {
            "assertions_total": 0, "assertions_passed": 0,
            "tool_calls": 0, "input_tokens": 0, "output_tokens": 0,
            "cache_read_tokens": 0, "cache_write_tokens": 0,
            "task_time_s": 0.0, "cost_usd": 0.0, "cost_known": False,
        }

        for case_result in self._ordered_rows():
            row = self._build_row(case_result)
            self._persist_case_json(row, case_result)
            agg["assertions_total"] += row.n_assertions
            agg["assertions_passed"] += row.n_passed
            if row.tool_calls is not None:
                agg["tool_calls"] += row.tool_calls
                agg["input_tokens"] += row.input_tokens or 0
                agg["output_tokens"] += row.output_tokens or 0
                agg["cache_read_tokens"] += row.cache_read_tokens or 0
                agg["cache_write_tokens"] += row.cache_write_tokens or 0
            if row.cost_usd is not None:
                agg["cost_usd"] += row.cost_usd
                agg["cost_known"] = True
            if row.duration_s is not None:
                agg["task_time_s"] += row.duration_s
            rows.append(row)

        totals = _Totals(
            task_time_s=agg["task_time_s"],
            wall_time_s=self.wall_seconds,
            tool_calls=agg["tool_calls"],
            input_tokens=agg["input_tokens"],
            output_tokens=agg["output_tokens"],
            cache_read_tokens=agg["cache_read_tokens"],
            cache_write_tokens=agg["cache_write_tokens"],
            cost_usd=round(agg["cost_usd"], 6) if agg["cost_known"] else None,
            assertions_total=agg["assertions_total"],
            assertions_passed=agg["assertions_passed"],
        )
        summary = {
            "model": self.model,
            "cases_total": len(rows),
            "cases_passed": sum(1 for r in rows if r.passed),
            "assertions_total": totals.assertions_total,
            "assertions_passed": totals.assertions_passed,
            "task_time_sum_seconds": round(totals.task_time_s, 3),
            "wall_time_seconds": round(totals.wall_time_s, 3),
            "totals": {
                "tool_calls": totals.tool_calls,
                "input_tokens": totals.input_tokens,
                "output_tokens": totals.output_tokens,
                "cache_read_tokens": totals.cache_read_tokens,
                "cache_write_tokens": totals.cache_write_tokens,
                "cost_usd": totals.cost_usd,
            },
            "per_case": [_summary_case(r) for r in rows],
            "logs_by_case": self.log_paths,
        }
        return rows, totals, summary

    def _build_row(self, case_result: _ReportRow) -> _CaseRow:
        name = case_result.name
        assertions = _assertion_values(case_result)
        n_assertions = len(assertions)
        n_passed = sum(1 for a in assertions if bool(getattr(a, "value", False)))

        if isinstance(case_result, ReportCaseFailure):
            return _CaseRow(
                name=name,
                skill=self.skills.get(name, "—"),
                passed=False,
                task_failed=True,
                error_message=case_result.error_message,
                input=getattr(case_result, "inputs", "-"),
                duration_s=None,
                cost_usd=None,
                tool_calls=None,
                input_tokens=None,
                output_tokens=None,
                cache_read_tokens=None,
                cache_write_tokens=None,
                n_assertions=n_assertions,
                n_passed=n_passed,
                output_path=str(self.output_root / f"{_safe_filename(name)}.json"),
                log_path=self.log_paths.get(name, "-"),
            )

        output: CaseResult = case_result.output  # type: ignore[assignment]
        return _CaseRow(
            name=name,
            skill=self.skills.get(name, "—"),
            passed=not output.task_failed and n_assertions > 0 and n_passed == n_assertions,
            task_failed=output.task_failed,
            error_message=output.error_message,
            input=getattr(case_result, "inputs", "-"),
            duration_s=output.duration_s,
            cost_usd=output.cost_usd,
            tool_calls=output.tool_calls,
            input_tokens=output.input_tokens,
            output_tokens=output.output_tokens,
            cache_read_tokens=output.cache_read_tokens,
            cache_write_tokens=output.cache_write_tokens,
            n_assertions=n_assertions,
            n_passed=n_passed,
            assertion_lines=[_assertion_line(a) for a in assertions],
            output_path=str(self.output_root / f"{_safe_filename(name)}.json"),
            log_path=self.log_paths.get(name, "-"),
        )

    def _persist_case_json(self, row: _CaseRow, case_result: _ReportRow) -> None:
        if isinstance(case_result, ReportCaseFailure):
            payload: dict[str, Any] = {
                "__task_failed__": True,
                "error_message": case_result.error_message,
            }
        else:
            payload = _serialize_case_result(case_result.output)  # type: ignore[arg-type]
        with Path(row.output_path).open("w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2, default=str)

    # -------- text format --------

    def _print_text(self, rows: list[_CaseRow], totals: _Totals) -> None:
        print()
        for i, row in enumerate(rows):
            duration = f"{row.duration_s:.1f}s" if row.duration_s is not None else "-"
            print(f"{row.name} {duration}")
            print(f"  {'input:':<13} {row.input}")
            print(f"  {'output:':<13} {row.output_path}")
            print(f"  {'log:':<13} {row.log_path}")
            for label, value in _metric_pairs(row):
                print(f"  {label:<13} {value}")
            if row.task_failed and row.error_message:
                print(f"  {'error:':<13} {row.error_message}")
            print(f"  {'assertions:':<13}")
            if not row.assertion_lines:
                print("    - none")
            for line in row.assertion_lines:
                status = "passed" if line.passed else "failed"
                print(f"    - {line.text} [{status}]")
            if i < len(rows) - 1:
                print()
                print()

        print()
        print()
        print("================================================")
        print()
        print(f"{'totalTime:':<13} {totals.total_time_s:.1f}s")
        print(f"{'totalCost:':<13} {_format_cost(totals.cost_usd)}")
        print(f"{'toolCalls:':<13} {totals.tool_calls}")
        print(f"{'inputTokens:':<13} {totals.input_tokens}")
        print(f"{'outputTokens:':<13} {totals.output_tokens}")
        print()
        print(f"{totals.assertions_passed}/{totals.assertions_total} assertions passed")

    # -------- markdown format --------

    def _render_markdown(self, rows: list[_CaseRow], totals: _Totals) -> str:
        lines: list[str] = []
        cases_passed = sum(1 for r in rows if r.passed)
        cases_total = len(rows)

        lines += [
            "# 🧪 Skills Evals — Run Report",
            "",
            f"- **Model:** `{self.model}`",
            f"- **Run:** `{self.output_root.name}`",
            "",
            "## Cases",
            "",
        ]
        for row in rows:
            lines += self._render_case_block(row)

        lines += [
            "## 📊 Summary",
            "",
            f"- **Cases:** {cases_passed}/{cases_total} passed"
            f"  ·  **Assertions:** {totals.assertions_passed}/{totals.assertions_total} passed",
            f"- **Total time:** {totals.total_time_s:.1f}s"
            f"  ·  **Total cost:** {_format_cost(totals.cost_usd)}"
            f"  ·  **Tool calls:** {totals.tool_calls}"
            f"  ·  **Tokens (in/out):** {totals.input_tokens}/{totals.output_tokens}",
            "",
            "| 🧩 Test | 🛠️ Skill | ✅ Result | Assertions | Duration | Cost | Tools | InTok | OutTok |",
            "| --- | --- | :---: | :---: | ---: | ---: | ---: | ---: | ---: |",
        ]
        lines += [_summary_row(r) for r in rows]
        lines.append(_summary_total_row(cases_passed, cases_total, totals))
        lines.append("")
        return "\n".join(lines)

    def _render_case_block(self, row: _CaseRow) -> list[str]:
        status = "✅ Pass" if row.passed else "❌ Fail"
        duration = f"{row.duration_s:.1f}s" if row.duration_s is not None else "—"
        cost = _format_cost(row.cost_usd)
        block = [
            f"### `{row.name}` — {status}  ·  {duration}  ·  {cost}",
            "",
            f"- **Skill:** `{row.skill}`",
            f"- **Input:** {row.input}",
            f"- **Output:** `{row.output_path}`",
            f"- **Log:** `{row.log_path}`",
            "",
            "| toolCalls | inputTokens | outputTokens | cacheRead | cacheWrite | cost |",
            "| ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
        if row.tool_calls is None:
            block.append("| — | — | — | — | — | — |")
            if row.error_message:
                block += ["", f"**Task error:** `{row.error_message}`"]
        else:
            block.append(
                f"| {row.tool_calls} | {row.input_tokens} | {row.output_tokens} | "
                f"{row.cache_read_tokens} | {row.cache_write_tokens} | {cost} |"
            )
        block += ["", f"**Assertions ({row.n_passed}/{row.n_assertions}):**", ""]
        if not row.assertion_lines:
            block.append("- _none_")
        else:
            for line in row.assertion_lines:
                marker = "✅" if line.passed else "❌"
                block.append(f"- {marker} {line.text}")
        block += ["", "---", ""]
        return block


# -------- helpers --------

def _resolve_format(raw: str | None) -> ReportFormat:
    fmt = (raw or "both").strip().lower()
    return cast(ReportFormat, fmt if fmt in _VALID_FORMATS else "both")


def _safe_filename(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]", "_", name)


def _assertion_values(case_result: Any) -> list[Any]:
    assertions = getattr(case_result, "assertions", None)
    if assertions is None:
        return []
    if isinstance(assertions, dict):
        return list(assertions.values())
    try:
        return list(assertions)
    except TypeError:
        return []


def _assertion_line(assertion: Any) -> _AssertionLine:
    name = getattr(assertion, "name", "assertion")
    passed = bool(getattr(assertion, "value", False))
    reason = getattr(assertion, "reason", None)
    status = "passed" if passed else "failed"
    text = f"{name}: {status}"
    if reason:
        text = f"{text} - {reason}"
    return _AssertionLine(text=text, passed=passed)


def _metric_pairs(row: _CaseRow) -> list[tuple[str, str]]:
    if row.tool_calls is None:
        return [
            ("toolCalls:", "-"),
            ("inputTokens:", "-"),
            ("outputTokens:", "-"),
            ("cacheRead:", "-"),
            ("cacheWrite:", "-"),
            ("cost:", "-"),
        ]
    return [
        ("toolCalls:", str(row.tool_calls)),
        ("inputTokens:", str(row.input_tokens)),
        ("outputTokens:", str(row.output_tokens)),
        ("cacheRead:", str(row.cache_read_tokens)),
        ("cacheWrite:", str(row.cache_write_tokens)),
        ("cost:", _format_cost(row.cost_usd)),
    ]


def _summary_row(row: _CaseRow) -> str:
    result = "✅ Pass" if row.passed else "❌ Fail"
    duration = f"{row.duration_s:.1f}s" if row.duration_s is not None else "—"
    cost = _format_cost(row.cost_usd)
    tools = str(row.tool_calls) if row.tool_calls is not None else "—"
    in_tok = str(row.input_tokens) if row.input_tokens is not None else "—"
    out_tok = str(row.output_tokens) if row.output_tokens is not None else "—"
    asserts = f"{row.n_passed}/{row.n_assertions}" if row.n_assertions else "—"
    return (
        f"| `{row.name}` | {row.skill} | {result} | {asserts} | "
        f"{duration} | {cost} | {tools} | {in_tok} | {out_tok} |"
    )


def _summary_total_row(passed: int, total: int, totals: _Totals) -> str:
    return (
        f"| **Total** | — | **{passed}/{total}** | "
        f"**{totals.assertions_passed}/{totals.assertions_total}** | "
        f"**{totals.total_time_s:.1f}s** | **{_format_cost(totals.cost_usd)}** | "
        f"**{totals.tool_calls}** | **{totals.input_tokens}** | **{totals.output_tokens}** |"
    )


def _summary_case(row: _CaseRow) -> dict[str, Any]:
    return {
        "name": row.name,
        "skill": row.skill,
        "passed": row.passed,
        "duration_s": row.duration_s,
        "cost_usd": row.cost_usd,
        "tool_calls": row.tool_calls,
        "input_tokens": row.input_tokens,
        "output_tokens": row.output_tokens,
        "cache_read_tokens": row.cache_read_tokens,
        "cache_write_tokens": row.cache_write_tokens,
        "n_assertions": row.n_assertions,
        "n_passed": row.n_passed,
    }


def _serialize_case_result(output: CaseResult) -> dict[str, Any]:
    return {
        "bash_commands": output.bash_commands,
        "files_written": {k: _truncate(v) for k, v in output.files_written.items()},
        "tool_uses": output.tool_uses,
        "response_text": _truncate(output.response_text, 4000),
        "cost_usd": output.cost_usd,
        "duration_s": round(output.duration_s, 3),
        "num_turns": output.num_turns,
        "tool_calls": output.tool_calls,
        "input_tokens": output.input_tokens,
        "output_tokens": output.output_tokens,
        "cache_read_tokens": output.cache_read_tokens,
        "cache_write_tokens": output.cache_write_tokens,
        "task_failed": output.task_failed,
        "error_message": output.error_message,
    }


def _truncate(s: Any, limit: int = 8000) -> Any:
    if not isinstance(s, str):
        return s
    return s if len(s) <= limit else s[:limit] + f"... [truncated {len(s) - limit} chars]"


def _format_cost(value: float | None) -> str:
    return "-" if value is None else f"${value:.4f}"
