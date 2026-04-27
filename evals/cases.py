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
    FileContentMatches,
    FileContentNotMatches,
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
        name="list_actions_github",
        inputs=(
            "List the SuperPlane actions available for the GitHub integration. "
            "Run the CLI, then summarize what you find."
        ),
        evaluators=(BashCommandCalled(r"superplane\s+index\s+actions\s+--from\s+github"),),
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
        name="describe_trigger",
        inputs=(
            "Inspect the github.onPush trigger schema via the CLI and report its configuration "
            "fields and payload shape."
        ),
        evaluators=(BashCommandCalled(r"superplane\s+index\s+triggers\s+--name\s+github\.onPush"),),
    ),
])


# No integrations are connected on the clean demo. Cases here test that the agent
# produces a well-formed YAML referencing actions by exact name (the backend
# may reject the apply, which is fine — we only validate YAML shape).
canvas_cases = _tagged("superplane-canvas-builder", [
    Case(
        name="builtin_components_canvas",
        inputs=(
            "Generate a SuperPlane canvas YAML scaffold using only the built-in components "
            "(no integration providers needed). The canvas should: start from a manual trigger "
            "named `start`, then run a `noop` action, then a `wait` component. Discover what's "
            "available with `superplane index actions` and write the canvas to canvas.yaml. "
            "Do not apply the canvas — this is a YAML-authoring task only."
        ),
        evaluators=(
            BashCommandCalled(r"superplane\s+index\s+actions"),
            FileWritten(r".*\.ya?ml$"),
            YamlValidatesCanvas(),
            CanvasHasNode("noop"),
            CanvasHasNode("wait"),
        ),
    ),
    Case(
        name="missing_integration_refusal",
        inputs=(
            "Create and apply a canvas that uses Daytona to spin up an ephemeral sandbox on "
            "every PR open. The skill's hard-gate says: do not apply YAML if the required "
            "integration is missing."
        ),
        evaluators=(
            BashCommandCalled(r"superplane\s+integrations\s+list"),
            ResponseMentions("daytona"),
            # The agent must not run `canvases create --file` against the backend when
            # the required integration is missing. Scaffolding via `init --output-file`
            # is acceptable; applying is not.
            BashCommandNotCalled(r"superplane\s+canvases\s+create\s+.*--file"),
        ),
    ),
    Case(
        name="starter_from_template",
        inputs=(
            "Scaffold a starter SuperPlane canvas YAML for me. Use the CLI's `canvases init` "
            "to generate it (you can pick any built-in template if one fits, otherwise use the "
            "default starter)."
        ),
        # The available templates change per-release; only assert that the agent reached for
        # `canvases init` (with or without --template).
        evaluators=(BashCommandCalled(r"superplane\s+canvases\s+init\b"),),
    ),
    Case(
        name="draft_update_flag",
        inputs=(
            "Update canvas 'my-canvas' to set its description to 'Eval test canvas'. "
            "Generate a minimal canvas YAML with that change and apply it with the CLI's draft flag "
            "(the skill says always use `--draft` on `canvases update` in this environment)."
        ),
        evaluators=(BashCommandCalled(r"superplane\s+canvases\s+update\s+\S+\s+--draft"),),
    ),
    Case(
        name="resource_verification",
        inputs=(
            "Build a canvas YAML that runs a Semaphore workflow on the superplanehq/app repo "
            "every time code is pushed to main. First check what's connected, then discover "
            "the trigger and action schemas you need."
        ),
        # `list-resources` requires a connected integration — the clean demo has none.
        # We only assert the discovery pattern that does not depend on connected state.
        evaluators=(
            BashCommandsInOrder(patterns=[
                r"superplane\s+integrations\s+list",
                r"superplane\s+index\s+(?:triggers|actions)\s+--from\s+\w+",
            ]),
        ),
    ),
    # Tests the new envelope clarification: agent must teach that `root().data` already
    # unwraps the envelope, so for Sentry's nested-`data` payload the correct path has
    # exactly two `.data.` segments — not three.
    Case(
        name="sentry_double_data_explain",
        inputs=(
            "I'm building a SuperPlane canvas with a sentry.onIssueCreated trigger. In a "
            "downstream action's configuration I wrote `{{ root().data.data.data.issue.title }}` "
            "and it resolves to null. Explain what's wrong and tell me the correct expression."
        ),
        evaluators=(
            # Must produce the correct path with exactly two `.data` segments.
            ResponseMentions("root().data.data.issue"),
        ),
    ),
    # Tests that, when authoring a canvas YAML for a Sentry trigger, the agent looks
    # up the trigger schema and writes expressions with the correct double-`.data.`
    # path — never the triple-`.data.` shape that double-counts the envelope.
    Case(
        name="sentry_canvas_yaml_expression",
        inputs=(
            "Generate a SuperPlane canvas YAML scaffold for me. Use sentry.onIssueCreated as "
            "the trigger and an http action that POSTs the issue title to "
            "https://example.com/notify in the body. Reference the issue title via expression "
            "from the trigger. Write the canvas to canvas.yaml. Do not apply — this is a "
            "YAML-authoring task only."
        ),
        evaluators=(
            FileWritten(r".*\.ya?ml$"),
            YamlValidatesCanvas(),
            # Correct double-`.data.` path appears in the YAML.
            FileContentMatches(r".*\.ya?ml$", r"\.data\.data\.issue"),
            # Triple-`.data.` (the envelope-double-counting bug) must NOT appear.
            FileContentNotMatches(r".*\.ya?ml$", r"\.data\.data\.data\."),
            # No applying the canvas — this is YAML-only, and Sentry isn't connected anyway.
            BashCommandNotCalled(r"superplane\s+canvases\s+create\s+.*--file"),
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
            "list recent events for the canvas and tell me what you see."
        ),
        # `events list-executions` requires an actual event id; the demo has none, so we
        # only assert the first diagnostic step from the skill's debugging flow.
        evaluators=(BashCommandCalled(r"superplane\s+events\s+list\b"),),
    ),
    Case(
        name="stuck_execution",
        inputs=(
            "An execution on a node in canvas 'my-canvas' has been running for over an hour. "
            "Run `superplane executions list --canvas-id <id>` for that canvas to inspect what's "
            "going on, then summarize."
        ),
        evaluators=(BashCommandCalled(r"superplane\s+executions\s+list\b"),),
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
            "Items are piling up on the 'build' node queue on canvas my-canvas — use "
            "`superplane queue list` to inspect what's queued and tell me what's there."
        ),
        evaluators=(BashCommandCalled(r"superplane\s+queue\s+list"),),
    ),
    Case(
        name="payload_envelope_explain",
        inputs=(
            "I'm building a SuperPlane canvas. In a downstream action's configuration I wrote "
            "`{{ $['GitHub onPush'].ref }}` and it resolves to null. Explain the SuperPlane "
            "expression envelope and what the correct accessor should be."
        ),
        # Tests that the agent at least invokes the envelope concept. The deeper
        # `.data.` teaching lives in the canvas-builder skill and isn't always
        # activated for this prompt — that's a separate skill-activation concern.
        evaluators=(ResponseMentions("envelope"),),
    ),
])

dataset = Dataset(
    name="skills",
    cases=[*cli_cases, *canvas_cases, *monitor_cases],
    evaluators=(),
)
