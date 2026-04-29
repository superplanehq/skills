---
name: superplane-monitor
description: Monitor and debug SuperPlane workflow executions. Inspect runs, diagnose failures, and manage execution queues. Use when a workflow fails, an execution is stuck, or the user wants to check run status. Triggers on "debug", "failed", "failure", "execution", "output channel", "passed but failed", "run status", "stuck", "queue", "troubleshoot".
---

# SuperPlane Monitor

Inspect, debug, and manage workflow executions.

## Quick Reference

| Task | Command |
| --- | --- |
| List events for canvas | `superplane events list --canvas-id <id>` |
| Trace an event's executions | `superplane events list-executions --canvas-id <id> --event-id <eid>` |
| List node executions | `superplane executions list --canvas-id <id> --node-id <nid>` |
| Cancel execution | `superplane executions cancel --canvas-id <id> --execution-id <eid>` |
| List queued items | `superplane queue list --canvas-id <id> --node-id <nid>` |
| Delete queued item | `superplane queue delete --canvas-id <id> --node-id <nid> --item-id <iid>` |

## Verify CLI Is Installed

Before any debugging, confirm the CLI binary is available without requiring network access:

```bash
command -v superplane
```

If this does not print a path: stop and tell the user to install the CLI from https://docs.superplane.com/installation/cli. Debugging requires the CLI to inspect events, executions, and queues.

Then verify the current session:

```bash
superplane whoami
```

If `whoami` fails because of authentication, DNS, timeout, or connection issues, the CLI is installed but the session is not usable yet. Tell the user to connect, fix the context, or allow network access as needed before debugging through the CLI.

If debugging will require canvas edits, apply them as draft updates:

```bash
superplane canvases update <name-or-id> --draft --file canvas.yaml
```

## Debugging Workflow

### 1. Find the Canvas

```bash
superplane canvases list
```

### 2. List Recent Events

```bash
superplane events list --canvas-id <canvas_id>
```

Each event is a trigger firing that starts a run.

### 3. Trace the Execution Chain

```bash
superplane events list-executions --canvas-id <canvas_id> --event-id <event_id>
```

Look for:
- **Failed** — the node that errored
- **Pending/Running** — possibly stuck
- **Skipped** — bypassed by a branch (If/Filter)

### 4. Inspect a Node's History and Payloads

```bash
superplane executions list --canvas-id <canvas_id> --node-id <node_id> -o yaml
```

Check if failures are recurring. For expression errors, inspect the actual payload structure:

- `rootEvent.data.data` — the trigger's real event payload (the double `.data` is the event envelope wrapping the webhook payload)
- `input` — what the node received from its upstream node (also has `{ data, timestamp, type }` envelope)
- `resultMessage` — the exact error, including which expression field was nil

Use these real payloads to fix expression paths rather than guessing from documentation.

For branching/channel issues, inspect `outputs` in execution YAML (not just top-level `result`):
- A node can show `result: RESULT_PASSED` while routing onto a `failure` channel — these are independent (runtime health vs. semantic routing). See [Execution result vs. output channel](https://docs.superplane.com/concepts/data-flow#execution-result-vs-output-channel) before flagging this as a bug.
- Confirm emitted channel names under `outputs` match edge wiring (`success`, `failed`, `default`, etc.)
- If downstream behavior looks inconsistent with `events list-executions`, trust the node's `outputs` block for routing truth

### 5. Fix and Re-run

Update the canvas, then trigger a new run from the UI or via a manual_run trigger.

```bash
superplane canvases update <name-or-id> --draft --file canvas.yaml
```

## Common Failure Patterns

### Auth Failure

Node fails immediately with permission error. Check:
```bash
superplane integrations list
superplane secrets list
```
Verify the integration is connected and the secret is valid.

### Expression Error

Node fails referencing a missing field. Check:
- Node name matches exactly (case-sensitive) in `$['Node Name']`
- Upstream node actually emits the expected field
- Root payload contains the expected data

### Stuck Queue

Executions pile up without progressing:
```bash
superplane queue list --canvas-id <id> --node-id <nid>
```

Causes: node is paused, Approval waiting for human input, Time Gate holding, external service unresponsive.

Clear stuck items:
```bash
superplane queue delete --canvas-id <id> --node-id <nid> --item-id <iid>
```

### Merge Never Fires

Merge waits for ALL incoming edges. If one branch is stuck, filtered out, or failed, Merge blocks. Check every upstream branch.

## When to Use Other Skills

| Need | Use Skill |
| --- | --- |
| Create or modify a canvas | superplane-canvas-builder |
| CLI commands and authentication | superplane-cli |

## Documentation

For agents that can fetch URLs, the full SuperPlane docs are available in LLM-friendly format:

- Compact index: https://docs.superplane.com/llms.txt
- Full content: https://docs.superplane.com/llms-full.txt
