from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pydantic_evals.evaluators import EvaluationReason, Evaluator, EvaluatorContext

from evals.harness import parsed_canvas_yaml
from evals.tool_registry import CaseResult


def _trigger_names(parsed: dict[str, Any]) -> list[str]:
    """Return trigger names from parsed canvas YAML.

    Triggers in canvas-yaml-spec live under ``spec.triggers[*].trigger.name`` or
    ``spec.nodes[*]`` where node kind == 'trigger'. We check both conventions.
    """
    spec = parsed.get("spec") or {}
    names: list[str] = []
    triggers = spec.get("triggers") or []
    if isinstance(triggers, list):
        for t in triggers:
            if not isinstance(t, dict):
                continue
            inner = t.get("trigger") if isinstance(t.get("trigger"), dict) else t
            name = inner.get("name") if isinstance(inner, dict) else None
            if isinstance(name, str) and name:
                names.append(name)
    for node in spec.get("nodes") or []:
        if not isinstance(node, dict):
            continue
        kind = str(node.get("kind", "")).lower()
        if kind == "trigger":
            trig = node.get("trigger") or node.get("component") or {}
            if isinstance(trig, dict):
                name = trig.get("name")
                if isinstance(name, str) and name:
                    names.append(name)
    return names


@dataclass
class CanvasHasTrigger(Evaluator):
    trigger: str

    def evaluate(self, ctx: EvaluatorContext[str, CaseResult, Any]) -> EvaluationReason:
        parsed = parsed_canvas_yaml(ctx.output)
        if parsed is None:
            return EvaluationReason(value=False, reason="no parseable canvas YAML")
        triggers = _trigger_names(parsed)
        if self.trigger in triggers:
            return EvaluationReason(
                value=True, reason=f"trigger {self.trigger!r} found in canvas"
            )
        return EvaluationReason(
            value=False,
            reason=f"trigger {self.trigger!r} not found; canvas triggers: {triggers!r}",
        )
