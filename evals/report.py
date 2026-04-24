"""Console + JSON report for eval runs. Simplified from superplane's ReportBuilder.

No pydantic-ai usage coupling; costs come from claude-agent-sdk's ResultMessage.
"""
from __future__ import annotations

import json
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
    ) -> None:
        self.report = report
        self.model = model
        self.evaluate_wall_seconds = evaluate_wall_seconds
        self.case_names = case_names
        self.interaction_log_paths_by_case_name = interaction_log_paths_by_case_name or {}
        self.output_root = output_root

    def _ordered_report_rows(self) -> list[_ReportRow]:
        """Match dataset order; pydantic-evals splits successes vs task exceptions."""
        by_name: dict[str, _ReportRow] = {}
        for ok_row in self.report.cases:
            if ok_row.name in by_name:
                raise RuntimeError(f"duplicate successful report case name {ok_row.name!r}")
            by_name[ok_row.name] = cast(_ReportRow, ok_row)
        for fail_row in self.report.failures:
            if fail_row.name in by_name:
                raise RuntimeError(f"eval report case name collision: {fail_row.name!r}")
            by_name[fail_row.name] = cast(_ReportRow, fail_row)
        return [by_name[name] for name in self.case_names if name in by_name]

    def render(self) -> dict[str, Any]:
        self.output_root.mkdir(parents=True, exist_ok=True)
        ordered_rows = self._ordered_report_rows()

        total_assertions = 0
        passed_assertions = 0
        total_cost_usd = 0.0
        cost_known = False
        task_time_sum_seconds = 0.0

        print()
        for i, case_result in enumerate(ordered_rows):
            case_name = case_result.name
            safe_case_name = re.sub(r"[^A-Za-z0-9_.-]", "_", case_name)

            if isinstance(case_result, ReportCaseFailure):
                serialized = {
                    "__task_failed__": True,
                    "error_message": case_result.error_message,
                }
                case_input = getattr(case_result, "inputs", "-")
                assertion_lines: list[str] = []
                duration_seconds = None
                case_cost = None
            else:
                output: CaseResult = case_result.output  # type: ignore[assignment]
                serialized = _serialize_case_result(output)
                case_input = getattr(case_result, "inputs", "-")
                assertion_lines = self._format_assertion_lines(case_result)
                duration_seconds = output.duration_s
                case_cost = output.cost_usd
                if case_cost is not None:
                    total_cost_usd += case_cost
                    cost_known = True

            output_json = self.output_root / f"{safe_case_name}.json"
            with output_json.open("w", encoding="utf-8") as fh:
                json.dump(serialized, fh, indent=2, default=str)

            assertion_values = self._get_assertion_values(case_result)
            total_assertions += len(assertion_values)
            passed_assertions += sum(
                1 for a in assertion_values if bool(getattr(a, "value", False))
            )

            duration_display = f"{duration_seconds:.1f}s" if duration_seconds else "-"
            print(f"{case_name}  {duration_display}")
            print(f"  input:    {case_input}")
            print(f"  output:   {output_json}")
            log_path = self.interaction_log_paths_by_case_name.get(case_name)
            if log_path:
                print(f"  log:      {log_path}")
            print(f"  cost:     {_format_cost(case_cost)}")
            print("  assertions:")
            if not assertion_lines:
                print("    - none")
            for line in assertion_lines:
                print(f"    - {line}")
            if duration_seconds is not None:
                task_time_sum_seconds += duration_seconds
            if i < len(ordered_rows) - 1:
                print()

        summary_payload = {
            "model": self.model,
            "cases_total": len(ordered_rows),
            "cases_passed": sum(
                1 for r in ordered_rows if not isinstance(r, ReportCaseFailure)
            ),
            "assertions_total": total_assertions,
            "assertions_passed": passed_assertions,
            "task_time_sum_seconds": round(task_time_sum_seconds, 3),
            "wall_time_seconds": round(self.evaluate_wall_seconds, 3),
            "total_cost_usd": round(total_cost_usd, 6) if cost_known else None,
            "logs_by_case": self.interaction_log_paths_by_case_name,
        }
        summary_path = self.output_root / "summary.json"
        with summary_path.open("w", encoding="utf-8") as fh:
            json.dump(summary_payload, fh, indent=2)

        print()
        print("=" * 48)
        total_time = task_time_sum_seconds + self.evaluate_wall_seconds
        print(f"totalTime:  {total_time:.1f}s")
        print(f"totalCost:  {_format_cost(total_cost_usd if cost_known else None)}")
        print(f"{passed_assertions}/{total_assertions} assertions passed")
        return summary_payload

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
                line = f"{line} — {reason}"
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
