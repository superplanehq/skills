"""Argv/env parsing for case selection. Ported from superplane/agent/evals/case_filter.py."""
from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Collection, Sequence
from typing import Any


def split_case_names(value: str | None) -> list[str] | None:
    if value is None:
        return None
    names = [part.strip() for part in value.split(",")]
    names = [n for n in names if n]
    return names if names else None


def select_cases(all_cases: Sequence[Any], selected: Collection[str] | None) -> list[Any]:
    if not selected:
        return list(all_cases)
    wanted = frozenset(selected)
    known = {c.name for c in all_cases if c.name}
    unknown = sorted(wanted - known)
    if unknown:
        available = "\n  ".join(sorted(known))
        sys.stderr.write(
            f"Unknown eval case name(s): {', '.join(unknown)}\nValid names:\n  {available}\n"
        )
        raise SystemExit(2)
    return [c for c in all_cases if c.name in wanted]


def filter_by_skill(all_cases: Sequence[Any], skill: str | None) -> list[Any]:
    """Filter cases by the ``skill`` key in ``Case.metadata``."""
    if not skill:
        return list(all_cases)
    return [c for c in all_cases if (c.metadata or {}).get("skill") == skill]


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run SuperPlane skills regression evals.")
    parser.add_argument(
        "--cases",
        metavar="NAMES",
        help="Comma-separated eval case names; overrides CASES env when set.",
    )
    parser.add_argument(
        "--skill",
        metavar="NAME",
        help="Filter to cases tagged with this skill name (superplane-cli, "
        "superplane-canvas-builder, superplane-monitor).",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="Print case names (one per line) and exit.",
    )
    return parser.parse_args(argv)


def case_filter(argv: list[str] | None = None) -> tuple[list[str] | None, str | None, bool]:
    """Return (selected_case_names | None, skill_filter | None, list_only).

    Precedence: CLI flags > env vars. Env: ``EVAL_CASES`` (csv), ``EVAL_SKILL``.
    """
    args = parse_args(argv if argv is not None else sys.argv[1:])
    selected = split_case_names(args.cases)
    if selected is None:
        selected = split_case_names(os.getenv("EVAL_CASES") or os.getenv("CASES"))
    skill = args.skill or os.getenv("EVAL_SKILL") or None
    return selected, skill, args.list
