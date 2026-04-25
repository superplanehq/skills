"""Eval cases for the three SuperPlane skills.

Each Case has ``metadata.skill`` so the runner can filter with ``--skill <name>``.
Cases that need the CLI to appear uninstalled set ``metadata.strip_cli=True``.
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

# ---------- superplane-cli ----------
cli_cases = [
    Case(
        name="whoami_basic",
        inputs="Check which SuperPlane org I'm currently connected to, then tell me the result.",
        evaluators=(BashCommandCalled(r"superplane\s+whoami"),),
        metadata={"skill": "superplane-cli"},
    ),
    Case(
        name="list_components_github",
        inputs=(
            "List the SuperPlane components available for the GitHub integration. "
            "Run the CLI, then summarize what you find."
        ),
        evaluators=(BashCommandCalled(r"superplane\s+index\s+components\s+--from\s+github"),),
        metadata={"skill": "superplane-cli"},
    ),
    Case(
        name="missing_cli_refusal",
        inputs="Create a new SuperPlane canvas named foo.",
        evaluators=(
            RefusedBecauseMissingCli(),
            BashCommandNotCalled(r"superplane\s+canvases\s+create"),
        ),
        metadata={"skill": "superplane-cli", "strip_cli": True},
    ),
    Case(
        name="connect_flow",
        inputs="Connect me to the SuperPlane instance at https://sp.example.com with token abc123.",
        evaluators=(
            BashCommandsInOrder(
                patterns=[r"superplane\s+connect\s+https://sp\.example\.com", r"superplane\s+whoami"]
            ),
        ),
        metadata={"skill": "superplane-cli"},
    ),
    Case(
        name="describe_trigger",
        inputs=(
            "Inspect the github.onPush trigger schema via the CLI and report its configuration fields "
            "and payload shape."
        ),
        evaluators=(
            BashCommandCalled(r"superplane\s+index\s+triggers\s+--name\s+github\.onPush"),
        ),
        metadata={"skill": "superplane-cli"},
    ),
]

# ---------- superplane-canvas-builder ----------
# No integrations are connected on the clean demo; agents should produce well-formed
# canvas YAMLs that *reference* integration components, even if the backend would
# reject the create. Evaluators validate YAML shape only.
canvas_cases = [
    Case(
        name="push_to_slack",
        inputs=(
            "Build a canvas that posts a Slack message to the '#deploys' channel on every push to "
            "the main branch of the superplanehq/app GitHub repository. Generate the full YAML and "
            "write it to canvas.yaml — the backend may not have these integrations connected yet, "
            "so just produce a correct YAML that could be applied later."
        ),
        evaluators=(
            BashCommandsInOrder(
                patterns=[
                    r"superplane\s+integrations\s+list",
                    r"superplane\s+index\s+components\s+--from\s+slack",
                ]
            ),
            FileWritten(r".*\.ya?ml$"),
            YamlValidatesCanvas(),
            CanvasHasTrigger("github.onPush"),
            CanvasHasNode("slack.sendTextMessage"),
        ),
        metadata={"skill": "superplane-canvas-builder"},
    ),
    Case(
        name="missing_integration_refusal",
        inputs=(
            "Create a canvas that uses Daytona to spin up an ephemeral sandbox on every PR open."
        ),
        evaluators=(
            BashCommandCalled(r"superplane\s+integrations\s+list"),
            # Match common phrasings of "the integration isn't available yet."
            ResponseMentions("daytona"),
            FileNotWritten(r".*canvas.*\.ya?ml$"),
        ),
        metadata={"skill": "superplane-canvas-builder"},
    ),
    Case(
        name="starter_from_template",
        inputs="Scaffold a health check monitor canvas to get me started.",
        evaluators=(
            BashCommandCalled(r"superplane\s+canvases\s+init\s+--template\s+health-check-monitor"),
        ),
        metadata={"skill": "superplane-canvas-builder"},
    ),
    Case(
        name="draft_update_flag",
        inputs="Update canvas my-canvas to add a manual approval step before deploy.",
        evaluators=(
            BashCommandCalled(r"superplane\s+canvases\s+update\s+[^\s]+\s+--draft"),
        ),
        metadata={"skill": "superplane-canvas-builder"},
    ),
    Case(
        name="resource_verification",
        inputs=(
            "Build a canvas YAML that runs a Semaphore workflow on the superplanehq/app repo "
            "every time code is pushed to main. Discover required resources via the CLI even if "
            "nothing is connected yet, and write canvas.yaml."
        ),
        evaluators=(
            BashCommandsInOrder(
                patterns=[
                    r"superplane\s+integrations\s+list",
                    r"superplane\s+integrations\s+list-resources",
                ]
            ),
        ),
        metadata={"skill": "superplane-canvas-builder"},
    ),
]

# ---------- superplane-monitor ----------
# A fresh demo has no events/executions. We assert command *order*, not content —
# the skill teaches a specific debugging sequence (events list → list-executions → etc.).
monitor_cases = [
    Case(
        name="why_did_my_run_fail",
        inputs=(
            "A canvas called 'my-canvas' had a failed run. Use the CLI to trace what happened: "
            "find the canvas, list recent events, then show the executions for the most recent event."
        ),
        evaluators=(
            BashCommandsInOrder(
                patterns=[
                    r"superplane\s+events\s+list",
                    r"superplane\s+events\s+list-executions",
                ]
            ),
        ),
        metadata={"skill": "superplane-monitor"},
    ),
    Case(
        name="stuck_execution",
        inputs=(
            "An execution on node deploy-prod in canvas cvs-abc has been running for over an hour. "
            "Use the CLI to find its execution history and diagnose."
        ),
        evaluators=(
            BashCommandCalled(
                r"superplane\s+executions\s+list\s+.*--node-id\s+deploy-prod"
            ),
        ),
        metadata={"skill": "superplane-monitor"},
    ),
    Case(
        name="cancel_flow",
        inputs="Cancel execution exec-123 on canvas cvs-9 using the CLI.",
        evaluators=(
            BashCommandCalled(
                r"superplane\s+executions\s+cancel\s+.*--execution-id\s+exec-123"
            ),
        ),
        metadata={"skill": "superplane-monitor"},
    ),
    Case(
        name="queue_inspect",
        inputs=(
            "Items are piling up on the 'build' node queue on canvas cvs-abc. "
            "Inspect the queue via the CLI and tell me what's there."
        ),
        evaluators=(BashCommandCalled(r"superplane\s+queue\s+list"),),
        metadata={"skill": "superplane-monitor"},
    ),
    Case(
        name="payload_envelope_explain",
        inputs=(
            "I'm getting null when I access `$['GitHub onPush'].ref` in a downstream node. Why?"
        ),
        evaluators=(
            ResponseMentions("data"),
            ResponseMentions("envelope"),
        ),
        metadata={"skill": "superplane-monitor"},
    ),
]

dataset = Dataset(
    name="skills",
    cases=[*cli_cases, *canvas_cases, *monitor_cases],
    evaluators=(),
)
