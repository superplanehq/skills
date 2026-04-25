"""Console + JSON + Markdown report for eval runs.

Two console formats:
  - text     : aligned-column-per-case, mirrors superplane/agent/evals/report.py
  - markdown : single table — Test | Skill | Result | Assertions | Duration | Cost | Tools | In | Out

Selected via the ``EVAL_REPORT_FORMAT`` env var: ``text`` | ``markdown`` | ``both`` (default).
A ``report.md`` is always written to the run's output directory regardless of console format.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Union, cast

from pydantic_evals.reporting import EvaluationReport, ReportCase, ReportCaseFailure

from evals.tool_registry import CaseResult

_ReportRow = Union[ReportCase[Any, Any, Any], ReportCaseFailure[Any, Any, Any]]


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
        self.evaluate_wall_seconds = evaluate_wall_seconds
        self.case_names = case_names
        self.interaction_log_paths_by_case_name = interaction_log_paths_by_case_name or {}
        self.output_root = output_root
        self.case_skill_by_name = case_skill_by_name or {}

    def _ordered_report_rows(self) -> list[_ReportRow]:
        by_name: dict[str, _ReportRow] = {}
        for ok_row in self.report.cases:
            by_name[ok_row.name] = cast(_ReportRow, ok_row)
        for fail_row in self.report.failures:
            by_name[fail_row.name] = cast(_ReportRow, fail_row)
        return [by_name[name] for name in self.case_names if name in by_name]

    def render(self) -> dict[str, Any]:
        """Build per-case rows, write JSON + report.md, print to stdout per env format."""
        self.output_root.mkdir(parents=True, exist_ok=True)
        ordered_rows = self._ordered_report_rows()
        case_rows, totals, summary = self._collect(ordered_rows)

        # Always persist machine-readable artifacts.
        with (self.output_root / "summary.json").open("w", encoding="utf-8") as fh:
            json.dump(summary, fh, indent=2)
        markdown = self._render_markdown(case_rows, totals)
        with (self.output_root / "report.md").open("w", encoding="utf-8") as fh:
            fh.write(markdown)

        # Console output, per EVAL_REPORT_FORMAT.
        fmt = (os.environ.get("EVAL_REPORT_FORMAT") or "both").strip().lower()
        if fmt not in {"text", "markdown", "both"}:
            fmt = "both"
        if fmt in {"text", "both"}:
            self._print_text(case_rows, totals)
        if fmt in {"markdown", "both"}:
            if fmt == "both":
                print()
                print()
            print(markdown)

        return summary

    # ------------------------------------------------------------------ collection

    def _collect(
        self, ordered_rows: list[_ReportRow]
    ) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
        case_rows: list[dict[str, Any]] = []
        total_assertions = 0
        passed_assertions = 0
        total_cost_usd = 0.0
        cost_known = False
        total_tool_calls = 0
        total_input_tokens = 0
        total_output_tokens = 0
        total_cache_read = 0
        total_cache_write = 0
        task_time_sum_seconds = 0.0

        for case_result in ordered_rows:
            case_name = case_result.name
            safe = re.sub(r"[^A-Za-z0-9_.-]", "_", case_name)
            output_json_path = self.output_root / f"{safe}.json"

            if isinstance(case_result, ReportCaseFailure):
                serialized = {
                    "__task_failed__": True,
                    "error_message": case_result.error_message,
                }
                output: CaseResult | None = None
                duration_seconds: float | None = None
            else:
                output = case_result.output  # type: ignore[assignment]
                serialized = _serialize_case_result(output)
                duration_seconds = output.duration_s

            with output_json_path.open("w", encoding="utf-8") as fh:
                json.dump(serialized, fh, indent=2, default=str)

            assertion_values = self._get_assertion_values(case_result)
            assertion_lines = self._format_assertion_lines(case_result)
            n_assertions = len(assertion_values)
            n_passed = sum(1 for a in assertion_values if bool(getattr(a, "value", False)))
            total_assertions += n_assertions
            passed_assertions += n_passed

            case_passed = (
                output is not None
                and not output.task_failed
                and n_assertions > 0
                and n_passed == n_assertions
            )

            if output is not None:
                total_tool_calls += output.tool_calls
                total_input_tokens += output.input_tokens
                total_output_tokens += output.output_tokens
                total_cache_read += output.cache_read_tokens
                total_cache_write += output.cache_write_tokens
                if output.cost_usd is not None:
                    total_cost_usd += output.cost_usd
                    cost_known = True
            if duration_seconds is not None:
                task_time_sum_seconds += duration_seconds

            case_rows.append({
                "name": case_name,
                "skill": self.case_skill_by_name.get(case_name, "—"),
                "passed": case_passed,
                "task_failed": output.task_failed if output else False,
                "error_message": (output.error_message if output else None)
                                 or (case_result.error_message
                                     if isinstance(case_result, ReportCaseFailure) else None),
                "input": getattr(case_result, "inputs", "-"),
                "duration_s": duration_seconds,
                "cost_usd": output.cost_usd if output else None,
                "tool_calls": output.tool_calls if output else None,
                "input_tokens": output.input_tokens if output else None,
                "output_tokens": output.output_tokens if output else None,
                "cache_read_tokens": output.cache_read_tokens if output else None,
                "cache_write_tokens": output.cache_write_tokens if output else None,
                "n_assertions": n_assertions,
                "n_passed": n_passed,
                "assertion_lines": assertion_lines,
                "output_path": str(output_json_path),
                "log_path": self.interaction_log_paths_by_case_name.get(case_name, "-"),
            })

        totals = {
            "task_time_sum_seconds": task_time_sum_seconds,
            "wall_time_seconds": self.evaluate_wall_seconds,
            "tool_calls": total_tool_calls,
            "input_tokens": total_input_tokens,
            "output_tokens": total_output_tokens,
            "cache_read_tokens": total_cache_read,
            "cache_write_tokens": total_cache_write,
            "cost_usd": round(total_cost_usd, 6) if cost_known else None,
            "assertions_total": total_assertions,
            "assertions_passed": passed_assertions,
        }
        summary = {
            "model": self.model,
            "cases_total": len(case_rows),
            "cases_passed": sum(1 for r in case_rows if r["passed"]),
            "assertions_total": total_assertions,
            "assertions_passed": passed_assertions,
            "task_time_sum_seconds": round(task_time_sum_seconds, 3),
            "wall_time_seconds": round(self.evaluate_wall_seconds, 3),
            "totals": {
                "tool_calls": total_tool_calls,
                "input_tokens": total_input_tokens,
                "output_tokens": total_output_tokens,
                "cache_read_tokens": total_cache_read,
                "cache_write_tokens": total_cache_write,
                "cost_usd": round(total_cost_usd, 6) if cost_known else None,
            },
            "per_case": [
                {k: r[k] for k in (
                    "name", "skill", "passed", "duration_s", "cost_usd", "tool_calls",
                    "input_tokens", "output_tokens", "cache_read_tokens", "cache_write_tokens",
                    "n_assertions", "n_passed",
                )}
                for r in case_rows
            ],
            "logs_by_case": self.interaction_log_paths_by_case_name,
        }
        return case_rows, totals, summary

    # ------------------------------------------------------------------ text format

    def _print_text(self, case_rows: list[dict[str, Any]], totals: dict[str, Any]) -> None:
        print()
        for i, row in enumerate(case_rows):
            duration_display = (
                f"{row['duration_s']:.1f}s" if row["duration_s"] is not None else "-"
            )
            print(f"{row['name']} {duration_display}")
            print(f"  {'input:':<13} {row['input']}")
            print(f"  {'output:':<13} {row['output_path']}")
            print(f"  {'log:':<13} {row['log_path']}")
            if row["tool_calls"] is None:
                print(f"  {'toolCalls:':<13} -")
                print(f"  {'inputTokens:':<13} -")
                print(f"  {'outputTokens:':<13} -")
                print(f"  {'cacheRead:':<13} -")
                print(f"  {'cacheWrite:':<13} -")
                print(f"  {'cost:':<13} -")
                if row["error_message"]:
                    print(f"  {'error:':<13} {row['error_message']}")
            else:
                print(f"  {'toolCalls:':<13} {row['tool_calls']}")
                print(f"  {'inputTokens:':<13} {row['input_tokens']}")
                print(f"  {'outputTokens:':<13} {row['output_tokens']}")
                print(f"  {'cacheRead:':<13} {row['cache_read_tokens']}")
                print(f"  {'cacheWrite:':<13} {row['cache_write_tokens']}")
                print(f"  {'cost:':<13} {_format_cost(row['cost_usd'])}")
            print(f"  {'assertions:':<13}")
            if not row["assertion_lines"]:
                print("    - none")
            for line in row["assertion_lines"]:
                print(f"    - {line}")
            if i < len(case_rows) - 1:
                print()
                print()

        print()
        print()
        print("================================================")
        print()
        total_time = totals["task_time_sum_seconds"] + totals["wall_time_seconds"]
        print(f"{'totalTime:':<13} {total_time:.1f}s")
        print(f"{'totalCost:':<13} {_format_cost(totals['cost_usd'])}")
        print(f"{'toolCalls:':<13} {totals['tool_calls']}")
        print(f"{'inputTokens:':<13} {totals['input_tokens']}")
        print(f"{'outputTokens:':<13} {totals['output_tokens']}")
        print()
        print(f"{totals['assertions_passed']}/{totals['assertions_total']} assertions passed")

    # ------------------------------------------------------------------ markdown format

    def _render_markdown(
        self, case_rows: list[dict[str, Any]], totals: dict[str, Any]
    ) -> str:
        """Per-case detail blocks first, summary table at the end."""
        lines: list[str] = []
        cases_passed = sum(1 for r in case_rows if r["passed"])
        cases_total = len(case_rows)
        total_time = totals["task_time_sum_seconds"] + totals["wall_time_seconds"]

        lines.append("# 🧪 Skills Evals — Run Report")
        lines.append("")
        lines.append(f"- **Model:** `{self.model}`")
        lines.append(f"- **Run:** `{self.output_root.name}`")
        lines.append("")

        # ------- per-case detail blocks -------
        lines.append("## Cases")
        lines.append("")
        for row in case_rows:
            status = "✅ Pass" if row["passed"] else "❌ Fail"
            duration = f"{row['duration_s']:.1f}s" if row["duration_s"] is not None else "—"
            cost = _format_cost(row["cost_usd"])

            lines.append(f"### `{row['name']}` — {status}  ·  {duration}  ·  {cost}")
            lines.append("")
            lines.append(f"- **Skill:** `{row['skill']}`")
            lines.append(f"- **Input:** {row['input']}")
            lines.append(f"- **Output:** `{row['output_path']}`")
            lines.append(f"- **Log:** `{row['log_path']}`")
            lines.append("")

            # Per-case metrics table.
            if row["tool_calls"] is None:
                lines.append("| toolCalls | inputTokens | outputTokens | cacheRead | cacheWrite | cost |")
                lines.append("| ---: | ---: | ---: | ---: | ---: | ---: |")
                lines.append("| — | — | — | — | — | — |")
                if row["error_message"]:
                    lines.append("")
                    lines.append(f"**Task error:** `{row['error_message']}`")
            else:
                lines.append(
                    "| toolCalls | inputTokens | outputTokens | cacheRead | cacheWrite | cost |"
                )
                lines.append("| ---: | ---: | ---: | ---: | ---: | ---: |")
                lines.append(
                    f"| {row['tool_calls']} | {row['input_tokens']} | {row['output_tokens']} | "
                    f"{row['cache_read_tokens']} | {row['cache_write_tokens']} | {cost} |"
                )
            lines.append("")

            # Assertions checklist.
            lines.append(f"**Assertions ({row['n_passed']}/{row['n_assertions']}):**")
            lines.append("")
            if not row["assertion_lines"]:
                lines.append("- _none_")
            else:
                for line in row["assertion_lines"]:
                    marker = "✅" if " passed " in f" {line} " else "❌"
                    lines.append(f"- {marker} {line}")
            lines.append("")
            lines.append("---")
            lines.append("")

        # ------- summary at end -------
        lines.append("## 📊 Summary")
        lines.append("")
        lines.append(
            f"- **Cases:** {cases_passed}/{cases_total} passed"
            f"  ·  **Assertions:** {totals['assertions_passed']}/{totals['assertions_total']} passed"
        )
        lines.append(
            f"- **Total time:** {total_time:.1f}s"
            f"  ·  **Total cost:** {_format_cost(totals['cost_usd'])}"
            f"  ·  **Tool calls:** {totals['tool_calls']}"
            f"  ·  **Tokens (in/out):** {totals['input_tokens']}/{totals['output_tokens']}"
        )
        lines.append("")
        lines.append(
            "| 🧩 Test | 🛠️ Skill | ✅ Result | Assertions | Duration | Cost | Tools | InTok | OutTok |"
        )
        lines.append(
            "| --- | --- | :---: | :---: | ---: | ---: | ---: | ---: | ---: |"
        )
        for row in case_rows:
            result = "✅ Pass" if row["passed"] else "❌ Fail"
            duration = f"{row['duration_s']:.1f}s" if row["duration_s"] is not None else "—"
            cost = _format_cost(row["cost_usd"])
            tools = str(row["tool_calls"]) if row["tool_calls"] is not None else "—"
            in_tok = str(row["input_tokens"]) if row["input_tokens"] is not None else "—"
            out_tok = str(row["output_tokens"]) if row["output_tokens"] is not None else "—"
            assertions_cell = f"{row['n_passed']}/{row['n_assertions']}" if row["n_assertions"] else "—"
            skill = row["skill"] or "—"
            lines.append(
                f"| `{row['name']}` | {skill} | {result} | "
                f"{assertions_cell} | {duration} | {cost} | "
                f"{tools} | {in_tok} | {out_tok} |"
            )
        lines.append(
            f"| **Total** | — | "
            f"**{cases_passed}/{cases_total}** | "
            f"**{totals['assertions_passed']}/{totals['assertions_total']}** | "
            f"**{total_time:.1f}s** | "
            f"**{_format_cost(totals['cost_usd'])}** | "
            f"**{totals['tool_calls']}** | "
            f"**{totals['input_tokens']}** | "
            f"**{totals['output_tokens']}** |"
        )
        lines.append("")

        return "\n".join(lines)

    def _get_assertion_values(self, case_result: Any) -> list[Any]:
        assertions = getattr(case_result, "assertions", None)
        if assertions is None:
            return []
        if isinstance(assertions, dict):
            return list(assertions.values())
        try:
            return list(assertions)
        except TypeError:
            return []

    def _format_assertion_lines(self, case_result: Any) -> list[str]:
        lines: list[str] = []
        for assertion in self._get_assertion_values(case_result):
            name = getattr(assertion, "name", "assertion")
            passed = bool(getattr(assertion, "value", False))
            reason = getattr(assertion, "reason", None)
            status = "passed" if passed else "failed"
            line = f"{name}: {status}"
            if reason:
                line = f"{line} - {reason}"
            lines.append(line)
        return lines


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


def _truncate(s: str, limit: int = 8000) -> str:
    if not isinstance(s, str):
        return s
    return s if len(s) <= limit else s[:limit] + f"... [truncated {len(s) - limit} chars]"


def _format_cost(value: float | None) -> str:
    if value is None:
        return "-"
    return f"${value:.4f}"
