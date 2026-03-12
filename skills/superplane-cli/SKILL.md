---
name: superplane-cli
description: Use when working with the SuperPlane CLI to discover integrations, components, and triggers, build or troubleshoot canvases, manage secrets, and monitor executions. Covers authentication, list/get commands, interpreting configuration schemas, wiring channels between nodes, resolving integration binding issues, and inspecting runs. Triggers on "superplane", "canvas", "workflow", "CLI", "connect", "integration is required", "execution".
---

# SuperPlane CLI

Operate a SuperPlane instance through the `superplane` CLI.

## Quick Reference

| Task | Command |
| --- | --- |
| Connect to org | `superplane connect <URL> <TOKEN>` |
| Who am I | `superplane whoami` |
| Check versioning mode | `superplane canvases get <canvas_name_or_id> -o json | jq '.metadata.canvasVersioningEnabled'` |
| Set active canvas | `superplane canvases active [canvas-id]` |
| List/switch contexts | `superplane contexts` |
| List canvases | `superplane canvases list` |
| Create canvas | `superplane canvases create <name>` then mode-aware update (`--draft` when versioning is enabled) |
| Create canvas from YAML | `superplane canvases create --file canvas.yaml` then mode-aware update (`--draft` when versioning is enabled) |
| Export canvas | `superplane canvases get <name>` |
| Update canvas in versioning-disabled mode | `superplane canvases update <name-or-id> --file canvas.yaml` |
| Update draft in versioning-enabled mode | `superplane canvases update <name-or-id> --draft --file canvas.yaml` |
| Create change request (versioning enabled) | `superplane canvases change-requests create [name-or-id] [--version-id <id>] [--title <text>] [--description <text>]` |
| List change requests | `superplane canvases change-requests list [name-or-id] [--status <filter>] [--mine] [--query <text>] [--limit <n>] [--before <rfc3339>]` |
| Approve / unapprove change request | `superplane canvases change-requests approve <change-request-id> [name-or-id]` / `superplane canvases change-requests unapprove <change-request-id> [name-or-id]` |
| Publish change request | `superplane canvases change-requests publish <change-request-id> [name-or-id]` |
| Reject / reopen change request | `superplane canvases change-requests reject <change-request-id> [name-or-id]` / `superplane canvases change-requests reopen <change-request-id> [name-or-id]` |
| Resolve conflicted change request | `superplane canvases change-requests resolve <change-request-id> [name-or-id] --file canvas.yaml [--auto-layout horizontal] [--auto-layout-scope <scope>] [--auto-layout-node <id>]` |
| Auto layout full canvas | `superplane canvases update <name-or-id> [--draft] --auto-layout horizontal` |
| Auto layout connected subgraph | `superplane canvases update <name-or-id> [--draft] --auto-layout horizontal --auto-layout-scope connected-component --auto-layout-node <node-id>` |
| Auto layout exact selected set | `superplane canvases update <name-or-id> [--draft] --auto-layout horizontal --auto-layout-scope exact-set --auto-layout-node <node-a> --auto-layout-node <node-b>` |
| List available providers | `superplane index integrations` |
| Describe a provider | `superplane index integrations --name github` |
| List connected integrations | `superplane integrations list` |
| Inspect connected integration | `superplane integrations get <id>` |
| List integration resources | `superplane integrations list-resources --id <id> --type <type>` |
| List components | `superplane index components` |
| Components from provider | `superplane index components --from github` |
| Describe a component | `superplane index components --name semaphore.runWorkflow` |
| List triggers | `superplane index triggers` |
| Triggers from provider | `superplane index triggers --from github` |
| Describe a trigger | `superplane index triggers --name github.onPush` |
| List secrets | `superplane secrets list` |
| Create secret | `superplane secrets create --file secret.yaml` |
| List events | `superplane events list --canvas-id <id>` |
| Trace event executions | `superplane events list-executions --canvas-id <id> --event-id <eid>` |
| List node executions | `superplane executions list --canvas-id <id> --node-id <nid>` |
| Cancel execution | `superplane executions cancel --canvas-id <id> --execution-id <eid>` |

## Verify CLI Is Installed

Before any CLI operation, confirm the CLI is available:

```bash
superplane whoami
```

If this returns `command not found`, the CLI is **not installed**. Stop and tell the user:

> The SuperPlane CLI is not installed. Install it from https://docs.superplane.com/installation/cli and then re-run this task.

Do **not** attempt to install the CLI on behalf of the user. Do **not** continue with doc-based guesswork — the CLI provides exact trigger names, component names, integration IDs, and config schemas that documentation cannot reliably substitute.

## Core Workflow

### 1. Authenticate

Create a service account in the SuperPlane UI, then:

```bash
superplane connect https://superplane.example.com <API_TOKEN>
superplane whoami
```

### 1b. Detect Canvas Mode (Required Before Any Update/Change Request Action)

Always determine mode first, then choose update commands.

```bash
superplane canvases get <canvas_name_or_id> -o json | jq '.metadata.canvasVersioningEnabled'
```

Interpretation:
- `true`: effective versioning enabled for this canvas. Use `superplane canvases update --draft ...`, then create/publish via `superplane canvases change-requests ...`.
- `false`: effective versioning disabled for this canvas. Use `superplane canvases update ...` (no `--draft`) and do not use `canvases change-requests`.

Behavior-based fallback:
- `--draft cannot be used when effective canvas versioning is disabled` => versioning disabled.
- `effective canvas versioning is enabled for this canvas; use --draft` => versioning enabled.
- `effective canvas versioning is disabled for this canvas` when running `canvases change-requests ...` => change requests unavailable for this canvas.

Org override rule:
- If organization versioning is enabled, all canvases are effectively versioned.
- If organization versioning is disabled, each canvas can still enable/disable versioning independently.

### 1c. Change Request Lifecycle (Versioning Enabled)

When effective canvas versioning is enabled:

1. Update the draft version (`superplane canvases update --draft ...`).
2. Create a change request from that draft.
3. Review and collect approvals.
4. Publish the change request.

Status model:
- `STATUS_OPEN`
- `STATUS_REJECTED`
- `STATUS_PUBLISHED`
- Conflict is tracked separately via `is_conflicted` (there is no `STATUS_CONFLICTED`).

Action rules:
- `approve`: only open + non-conflicted.
- `unapprove`: only if the current user has an active approval on an open change request.
- `publish`: only open + non-conflicted + all configured approver requirements actively approved.
- `reject`: allowed for open change requests (including conflicted); invalidates active approvals.
- `reopen`: only rejected; recomputes diff/conflicts and invalidates active approvals.
- `resolve`: updates the change-request version with a resolved canvas payload.

Commands:

```bash
superplane canvases change-requests list [name-or-id] [--status <filter>] [--mine] [--query <text>] [--limit <n>] [--before <rfc3339>]
superplane canvases change-requests get <change-request-id> [name-or-id]
superplane canvases change-requests create [name-or-id] [--version-id <id>] [--title <text>] [--description <text>]
superplane canvases change-requests approve <change-request-id> [name-or-id]
superplane canvases change-requests unapprove <change-request-id> [name-or-id]
superplane canvases change-requests publish <change-request-id> [name-or-id]
superplane canvases change-requests reject <change-request-id> [name-or-id]
superplane canvases change-requests reopen <change-request-id> [name-or-id]
superplane canvases change-requests resolve <change-request-id> [name-or-id] --file <canvas.yaml> [--auto-layout horizontal] [--auto-layout-scope <scope>] [--auto-layout-node <id>]
```

Notes:
- `name-or-id` is optional when an active canvas is set with `superplane canvases active`.
- `--status` supports `all`, `open`, `conflicted`, `rejected`, `published`.

### 2. Discover What Exists

Run these first to understand what's available:

```bash
superplane index integrations          # available providers
superplane integrations list           # connected instances in this org
superplane index triggers              # all trigger types
superplane index components            # all component types
```

Narrow to one provider:

```bash
superplane index triggers --from github
superplane index components --from github
```

Inspect required config fields and payload shapes:

```bash
superplane index triggers --name github.onPush
superplane index components --name semaphore.runWorkflow
```

List runtime options for `integration-resource` fields (e.g., repos, projects):

```bash
superplane integrations list-resources --id <integration-id> --type <type> --parameters key1=value1,key2=value2
```

Use `superplane integrations list` first to find valid integration IDs.

### 3. Build a Canvas Incrementally

Create a blank canvas, then iterate:

```bash
superplane canvases create my-canvas
# versioning disabled:
superplane canvases update my-canvas
# versioning enabled:
superplane canvases update my-canvas --draft
superplane canvases change-requests create my-canvas --title "Initial publish"
# if required by approver rules:
superplane canvases change-requests approve <change-request-id> my-canvas
# publish once required approvals are active and the CR is non-conflicted:
superplane canvases change-requests publish <change-request-id> my-canvas
superplane canvases get my-canvas > canvas.yaml
# edit canvas.yaml
# versioning disabled:
superplane canvases update --file canvas.yaml
# versioning enabled:
superplane canvases update my-canvas --draft --file canvas.yaml
superplane canvases change-requests create my-canvas --title "Update canvas"
# if required by approver rules:
superplane canvases change-requests approve <change-request-id> my-canvas
superplane canvases change-requests publish <change-request-id> my-canvas
```

If you create a canvas from YAML, apply the same rule:

```bash
superplane canvases create --file canvas.yaml
# preferred immediately after create (does not require metadata.id in local YAML):
superplane canvases update <name-or-id> [--draft]
# use --file only when your local YAML includes metadata.id:
superplane canvases update --file canvas.yaml
```

Mode rules:
- **Versioning enabled**: `superplane canvases update ...` must include `--draft`; then create a change request and publish it to apply live.
- `change-requests publish` requires the change request to be open, non-conflicted, and fully approved by configured approver rules.
- **Versioning disabled**: `superplane canvases update ...` updates live directly; `canvases change-requests ...` is unavailable.
- Live updates without draft/version are blocked when versioning is enabled.

See [Canvas YAML Spec](references/canvas-yaml-spec.md) for the full format.

### Auto Layout via CLI

Use `canvases update` with auto-layout flags:

Default agent behavior:
- Auto layout is applied by default on `superplane canvases update` when no auto-layout flags are provided.
- Use `--auto-layout` flags when you need explicit scope/seed-node control.
- In versioning mode, include `--draft` on update. Draft changes go live only after `canvases change-requests create` and `canvases change-requests publish`.

```bash
# connected component around one seed node (recommended default for existing canvases)
superplane canvases update <name-or-id> [--draft] \
  --auto-layout horizontal \
  --auto-layout-scope connected-component \
  --auto-layout-node <node-id>

# exact node set only (best when the user selected nodes)
superplane canvases update <name-or-id> [--draft] \
  --auto-layout horizontal \
  --auto-layout-scope exact-set \
  --auto-layout-node <node-a> \
  --auto-layout-node <node-b>

# full canvas (use sparingly; see policy below)
superplane canvases update <name-or-id> [--draft] --auto-layout horizontal
```

Rules and behavior:
- `--auto-layout` is required when using `--auto-layout-scope` or `--auto-layout-node`.
- `--draft` is required when versioning is enabled.
- Supported algorithm: `horizontal`.
- Supported scopes: `full-canvas`, `connected-component`, `exact-set`.
- Default scope behavior:
  - If no seed nodes are provided: behaves like `full-canvas`.
  - If seed nodes are provided and scope omitted: behaves like `connected-component`.
- Recommended policy for agents:
  - Prefer `connected-component` for existing/disconnected canvases.
  - Prefer `exact-set` when the user selected specific nodes.
  - Use `full-canvas` only when creating from scratch, when the graph is one connected component, or when the user explicitly asks for full-canvas layout.
- Scope selection default:
  - If a changed/selected node ID is known, use `connected-component` + `--auto-layout-node`.
  - If a set of changed node IDs is known, use `exact-set` + repeated `--auto-layout-node`.
  - If no node IDs are available, use `full-canvas`.
- Positioning is anchor-preserving: the laid-out region keeps its top-left anchor relative to current canvas coordinates to avoid large jumps.

### 4. Manage Secrets

```bash
superplane secrets create --file secret.yaml
superplane secrets list
superplane secrets update --file secret.yaml
superplane secrets delete <name_or_id>
```

### 5. Monitor Runs

```bash
superplane events list --canvas-id <id>
superplane events list-executions --canvas-id <id> --event-id <eid>
```

### 6. Troubleshooting Checklist

Run after every canvas update:

```bash
superplane canvases get <name>
```

Check:
- All required `configuration` fields are present
- Edges use the correct output channels
- No node `errorMessage` remains (especially "integration is required")
- No `warningMessage` about duplicate names
- Expressions reference existing node names (case-sensitive)

## Resolving "integration is required"

When a field type is `integration-resource` (like `repository` or `project`), the node needs a connected integration instance.

1. `superplane integrations list` — confirm the provider is connected
2. `superplane integrations get <id>` — inspect the connection
3. Add `integration.id` to the node in the canvas YAML
4. `superplane integrations list-resources --id <id> --type <type>` — find valid resource values
5. `superplane canvases update <name-or-id> [--draft] --file canvas.yaml` — apply the fix
6. If `--draft` was used: `superplane canvases change-requests create <name-or-id> --title "Fix integration binding"`
7. If needed: `superplane canvases change-requests approve <change-request-id> <name-or-id>`
8. If `--draft` was used: `superplane canvases change-requests publish <change-request-id> <name-or-id>`
9. `superplane canvases get <name>` — verify errors are cleared

## When to Use Other Skills

| Need | Use Skill |
| --- | --- |
| Design a canvas from requirements | superplane-canvas-builder |
| Debug a failed execution | superplane-monitor |

## Documentation

For agents that can fetch URLs, the full SuperPlane docs are available in LLM-friendly format:

- Compact index: https://docs.superplane.com/llms.txt
- Full content: https://docs.superplane.com/llms-full.txt

## References

- [Canvas YAML Spec](references/canvas-yaml-spec.md) — Full YAML format with examples
