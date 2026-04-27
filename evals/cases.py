"""Eval cases for the three SuperPlane skills.

Each case carries ``metadata.skill`` for filtering. Cases that should run with
the CLI absent (i.e. ``command -v superplane`` fails) set ``metadata.strip_cli``.
"""
from __future__ import annotations

from pydantic_evals import Case, Dataset

from evals.evaluators import (
    BashCommandCalled,
    BashCommandNotCalled,
    BashCommandsInOrder,
    CanvasHasNode,
    CanvasHasTrigger,
    FileNotWritten,
    FileWritten,
    RefusedBecauseMissingCli,
    ResponseMentions,
    YamlValidatesCanvas,
)


def _tagged(skill: str, cases: list[Case]) -> list[Case]:
    """Set or merge ``metadata.skill`` on each case."""
    for c in cases:
        c.metadata = {"skill": skill, **(c.metadata or {})}
    return cases


cli_cases = _tagged("superplane-cli", [
    Case(
        name="whoami_basic",
        inputs="Check which SuperPlane org I'm currently connected to, then tell me the result.",
        evaluators=(BashCommandCalled(r"superplane\s+whoami"),),
    ),
    Case(
        name="list_components_github",
        inputs=(
            "List the SuperPlane components available for the GitHub integration. "
            "Run the CLI, then summarize what you find."
        ),
        evaluators=(BashCommandCalled(r"superplane\s+index\s+components\s+--from\s+github"),),
    ),
    Case(
        name="missing_cli_refusal",
        inputs="Create a new SuperPlane canvas named foo.",
        evaluators=(
            RefusedBecauseMissingCli(),
            BashCommandNotCalled(r"superplane\s+canvases\s+create"),
        ),
        metadata={"strip_cli": True},
    ),
    Case(
        name="connect_flow",
        inputs="Connect me to the SuperPlane instance at https://sp.example.com with token abc123.",
        evaluators=(
            BashCommandsInOrder(patterns=[
                r"superplane\s+connect\s+https://sp\.example\.com",
                r"superplane\s+whoami",
            ]),
        ),
    ),
    Case(
        name="describe_trigger",
        inputs=(
            "Inspect the github.onPush trigger schema via the CLI and report its configuration "
            "fields and payload shape."
        ),
        evaluators=(BashCommandCalled(r"superplane\s+index\s+triggers\s+--name\s+github\.onPush"),),
    ),
])


# No integrations are connected on the clean demo. Cases here test that the agent
# produces a well-formed YAML referencing components by exact name (the backend
# may reject the apply, which is fine — we only validate YAML shape).
canvas_cases = _tagged("superplane-canvas-builder", [
    Case(
        name="push_to_slack",
        inputs=(
            "Build a canvas that posts a Slack message to the '#deploys' channel on every push to "
            "the main branch of the superplanehq/app GitHub repository. Generate the full YAML and "
            "write it to canvas.yaml — the backend may not have these integrations connected yet, "
            "so just produce a correct YAML that could be applied later."
        ),
        evaluators=(
            BashCommandsInOrder(patterns=[
                r"superplane\s+integrations\s+list",
                r"superplane\s+index\s+components\s+--from\s+slack",
            ]),
            FileWritten(r".*\.ya?ml$"),
            YamlValidatesCanvas(),
            CanvasHasTrigger("github.onPush"),
            CanvasHasNode("slack.sendTextMessage"),
        ),
    ),
    Case(
        name="missing_integration_refusal",
        inputs="Create a canvas that uses Daytona to spin up an ephemeral sandbox on every PR open.",
        evaluators=(
            BashCommandCalled(r"superplane\s+integrations\s+list"),
            ResponseMentions("daytona"),
            FileNotWritten(r".*canvas.*\.ya?ml$"),
        ),
    ),
    Case(
        name="starter_from_template",
        inputs="Scaffold a health check monitor canvas to get me started.",
        evaluators=(
            BashCommandCalled(r"superplane\s+canvases\s+init\s+--template\s+health-check-monitor"),
        ),
    ),
    Case(
        name="draft_update_flag",
        inputs="Update canvas my-canvas to add a manual approval step before deploy.",
        evaluators=(BashCommandCalled(r"superplane\s+canvases\s+update\s+[^\s]+\s+--draft"),),
    ),
    Case(
        name="resource_verification",
        inputs=(
            "Build a canvas YAML that runs a Semaphore workflow on the superplanehq/app repo "
            "every time code is pushed to main. Discover required resources via the CLI even if "
            "nothing is connected yet, and write canvas.yaml."
        ),
        evaluators=(
            BashCommandsInOrder(patterns=[
                r"superplane\s+integrations\s+list",
                r"superplane\s+integrations\s+list-resources",
            ]),
        ),
    ),
])


# A fresh demo has no events/executions. Cases assert command *order* and content
# of the diagnostic flow — the skill teaches a specific sequence
# (events list → list-executions → executions list ...).
monitor_cases = _tagged("superplane-monitor", [
    Case(
        name="why_did_my_run_fail",
        inputs=(
            "A canvas called 'my-canvas' had a failed run. Use the CLI to trace what happened: "
            "find the canvas, list recent events, then show the executions for the most recent event."
        ),
        evaluators=(
            BashCommandsInOrder(patterns=[
                r"superplane\s+events\s+list",
                r"superplane\s+events\s+list-executions",
            ]),
        ),
    ),
    Case(
        name="stuck_execution",
        inputs=(
            "An execution on node deploy-prod in canvas cvs-abc has been running for over an hour. "
            "Use the CLI to find its execution history and diagnose."
        ),
        evaluators=(
            BashCommandCalled(r"superplane\s+executions\s+list\s+.*--node-id\s+deploy-prod"),
        ),
    ),
    Case(
        name="cancel_flow",
        inputs="Cancel execution exec-123 on canvas cvs-9 using the CLI.",
        evaluators=(
            BashCommandCalled(r"superplane\s+executions\s+cancel\s+.*--execution-id\s+exec-123"),
        ),
    ),
    Case(
        name="queue_inspect",
        inputs=(
            "Items are piling up on the 'build' node queue on canvas cvs-abc. "
            "Inspect the queue via the CLI and tell me what's there."
        ),
        evaluators=(BashCommandCalled(r"superplane\s+queue\s+list"),),
    ),
    Case(
        name="payload_envelope_explain",
        inputs="I'm getting null when I access `$['GitHub onPush'].ref` in a downstream node. Why?",
        evaluators=(ResponseMentions("data"), ResponseMentions("envelope")),
    ),
])

dataset = Dataset(
    name="skills",
    cases=[*cli_cases, *canvas_cases, *monitor_cases],
    evaluators=(),
)
