from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pydantic_evals.evaluators import EvaluationReason, Evaluator, EvaluatorContext

from evals.harness import parsed_canvas_yaml
from evals.tool_registry import CaseResult


def _trigger_names(parsed: dict[str, Any]) -> list[str]:
    """Return trigger names from parsed canvas YAML.

    Recognizes three shapes:
      - top-level ``spec.triggers[*].trigger.name`` (or ``spec.triggers[*].name``)
      - ``spec.nodes[*]`` with ``kind: trigger`` and a ``trigger.name`` / ``component.name``
      - ``spec.nodes[*]`` with a ``trigger`` key (regardless of ``kind``) — what the
        real backend's CLI emits today.
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
        trig = node.get("trigger")
        if isinstance(trig, dict):
            name = trig.get("name")
            if isinstance(name, str) and name:
                names.append(name)
                continue
        # Legacy: kind == trigger with component.name
        if str(node.get("kind", "")).lower() == "trigger":
            comp = node.get("component") or {}
            if isinstance(comp, dict):
                name = comp.get("name")
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
