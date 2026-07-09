---
name: superplane-cli
description: Use when working with the SuperPlane CLI to discover integrations, actions, and triggers, build or troubleshoot apps and canvases, manage secrets, and monitor executions. Covers authentication, list/get commands, interpreting configuration schemas, wiring channels between nodes, resolving integration binding issues, and inspecting runs. Triggers on "superplane", "app", "canvas", "workflow", "CLI", "connect", "integration is required", "execution".
---

# SuperPlane CLI

Operate a SuperPlane instance through the `superplane` CLI.

## Quick Reference

| Task | Command |
| --- | --- |
| Connect to org | `superplane connect <URL> <TOKEN>` |
| Who am I | `superplane whoami` |
| Set active app | `superplane apps active [app-id]` |
| List/switch contexts | `superplane contexts` |
| List apps | `superplane apps list` |
| Generate starter YAML | `superplane apps canvas init` |
| Generate from template | `superplane apps canvas init --template <name>` |
| List canvas templates | `superplane apps canvas init --list-templates` |
| Create app | `superplane apps create <name>` then export, edit, and apply via staging or `canvas update --message` |
| Create app from canvas YAML | `superplane apps create --canvas-file canvas.yaml` |
| Create app with layout flags | `superplane apps create --canvas-file canvas.yaml --canvas-auto-layout horizontal` |
| Staging status | `superplane apps staging status [name-or-id]` |
| Stage files | `superplane apps staging update --file canvas.yaml [--file console.yaml ...]` |
| Commit staged changes | `superplane apps staging commit --message "..."` |
| Export canvas | `superplane apps canvas get <name-or-id> -o yaml` |
| Update canvas (direct commit) | `superplane apps canvas update -f canvas.yaml --message "..."` |
| Auto layout full canvas | `superplane apps canvas update -f canvas.yaml --message "..." --auto-layout horizontal` |
| Auto layout connected subgraph | `superplane apps canvas update -f canvas.yaml --message "..." --auto-layout horizontal --auto-layout-scope connected-component --auto-layout-node <node-id>` |
| Export console | `superplane apps console get <name-or-id> -o yaml > console.yaml` |
| Update console (direct commit) | `superplane apps console set -f console.yaml --message "..."` |
| List app files | `superplane apps files tree <name-or-id>` |
| Show app file | `superplane apps files show <path> <name-or-id>` |
| List available providers | `superplane index integrations` |
| Describe a provider | `superplane index integrations --name github` |
| List connected integrations | `superplane integrations list` |
| Inspect connected integration | `superplane integrations get <id>` |
| List integration resources | `superplane integrations list-resources --id <id> --type <type>` |
| List actions | `superplane index actions` |
| Actions from provider | `superplane index actions --from github` |
| Describe an action | `superplane index actions --name semaphore.runWorkflow` |
| List triggers | `superplane index triggers` |
| Triggers from provider | `superplane index triggers --from github` |
| Describe a trigger | `superplane index triggers --name github.onPush` |
| List secrets | `superplane secrets list` |
| Create secret | `superplane secrets create --file secret.yaml` |
| List runs | `superplane runs list --app-id <id>` |
| Describe a run | `superplane runs describe <run-id> --app-id <id>` |
| List node executions | `superplane executions list --app-id <id> --node-id <nid>` |
| Cancel execution | `superplane executions cancel --app-id <id> --execution-id <eid>` |

## Verify CLI Is Installed

Before any CLI operation, confirm the CLI binary is available without requiring network access:

```bash
command -v superplane
```

If this does not print a path, the CLI is **not installed**. Stop and tell the user:

> The SuperPlane CLI is not installed. Install it from https://docs.superplane.com/installation/cli and then re-run this task.

Do **not** attempt to install the CLI on behalf of the user. Do **not** continue with doc-based guesswork — the CLI provides exact trigger names, action names, integration IDs, and config schemas that documentation cannot reliably substitute.

Only after confirming the binary exists should you verify the session:

```bash
superplane whoami
```

Interpret failures carefully:
- `command not found` from `whoami` still means the CLI is missing.
- Authentication, DNS, timeout, or connection errors mean the CLI exists but the current session cannot reach SuperPlane yet. In that case, tell the user the CLI is installed but the session/network/auth is not working, and ask them to connect or allow network access as needed.

## Core Workflow

### 1. Authenticate

Create a service account in the SuperPlane UI, then:

```bash
superplane connect https://superplane.example.com <API_TOKEN>
superplane whoami
```

### 1b. Staging and Commits

App versions are immutable commits on the main branch. To iterate before committing, use the **staging area** (like a git working tree). To apply in one step, pass `--message` on a direct canvas or console write.

**Stage, then commit** (preferred for iterative edits):

```bash
superplane apps staging status [name-or-id]

superplane apps staging update \
  --file canvas.yaml \
  --file console.yaml \
  --file README.md

superplane apps staging commit --message "Commit message"
```

**Direct commit** (stage + commit in one command):

```bash
superplane apps canvas update -f canvas.yaml --message "Commit message"
superplane apps console set -f console.yaml --message "Commit message"
```

Rules:
- `canvas get` and `console get` read the **live** (committed) app only.
- `--message` is required on `canvas update` and `console set`; without it, use `staging update` and `staging commit` instead.
- `staging update` maps each `--file` to a repository path by **basename** only (`canvas.yaml`, `console.yaml`, `README.md`, etc.).
- `canvas.yaml` staged via `staging update` must include `metadata.id` matching the target app.
- Reuse staged paths from `staging status` or agent `[Staging Status]` context when continuing work.

### 2. Discover What Exists

Run these first to understand what's available:

```bash
superplane index integrations          # available providers
superplane integrations list           # connected instances in this org
superplane index triggers              # all trigger types
superplane index actions            # all action types
```

Narrow to one provider:

```bash
superplane index triggers --from github
superplane index actions --from github
```

Inspect required config fields and payload shapes:

```bash
superplane index triggers --name github.onPush
superplane index actions --name semaphore.runWorkflow
```

List runtime options for `integration-resource` fields (e.g., repos, projects):

```bash
superplane integrations list-resources --id <integration-id> --type <type> --parameters key1=value1,key2=value2
```

Use `superplane integrations list` first to find valid integration IDs.

### 3. Build a Canvas Incrementally

Generate a starter YAML, then create and iterate:

```bash
superplane apps canvas init --output-file canvas.yaml
# or start from a template:
superplane apps canvas init --template health-check-monitor --output-file canvas.yaml
# edit canvas.yaml, then create:
superplane apps create --canvas-file canvas.yaml
# or create a blank canvas and iterate:
superplane apps create my-canvas
superplane apps canvas get my-canvas -o yaml > canvas.yaml
# edit canvas.yaml (ensure metadata.id is set)
superplane apps staging update --file canvas.yaml
superplane apps staging commit --message "Initial canvas"
# or commit directly:
superplane apps canvas update -f canvas.yaml --message "Initial canvas"
```

If you create an app from canvas YAML, `apps create --canvas-file` already sends the full canvas payload. Do not assume a second update is required just to apply the graph:

```bash
superplane apps create --canvas-file canvas.yaml
```

Workflow rules:
- `superplane apps create --canvas-file canvas.yaml` accepts the same resource-style Canvas YAML described in the spec (`apiVersion`, `kind`, `metadata`, `spec`).
- On `superplane apps create`, canvas layout flags are prefixed with `canvas-`: `--canvas-auto-layout`, `--canvas-auto-layout-scope`, and repeated `--canvas-auto-layout-node`.
- Run a follow-up `superplane apps canvas update ...` only when you are intentionally changing the canvas after create, for example to apply additional edits from a file that includes `metadata.id`, or to run auto-layout with different flags than the defaults used on create.
- Use `apps staging update` + `apps staging commit` for iterative edits, or `canvas update` / `console set` with `--message` to commit directly.

See [Canvas YAML Spec](references/canvas-yaml-spec.md) for the full format.

### Console YAML via CLI

Use `superplane apps console` to read and replace the app console: panels plus grid layout.

Commands:

```bash
# With an explicit app name or id
superplane apps console get <name-or-id>
superplane apps console get <name-or-id> -o yaml > console.yaml
superplane apps console set -f console.yaml --message "Update console"
superplane apps console set <name-or-id> -f console.yaml --message "Update console"
superplane apps console set <name-or-id> -f - --message "Update console" < console.yaml

# Stage console changes without committing immediately
superplane apps staging update --file console.yaml
superplane apps staging commit --message "Update console"

# With the active app from `superplane apps active`
superplane apps console get
superplane apps console set -f console.yaml --message "Update console"
```

Behavior:
- `get` reads the live (committed) console.
- `set --message` replaces panels and layout and commits immediately.
- To stage console edits without committing, use `staging update --file console.yaml` then `staging commit`.
- Console import is replace-all: the YAML replaces every panel and layout entry.
- Use `-o yaml` when exporting a file intended for editing/import.

See [Console YAML Spec](references/console-yaml-spec.md) for the stable YAML envelope, layout fields, and where to find current widget details.

### Auto Layout via CLI

Use `apps canvas update` with auto-layout flags:

Default agent behavior:
- Auto layout is applied by default on `superplane apps canvas update` when no auto-layout flags are provided.
- Use `--auto-layout` flags when you need explicit scope/seed-node control.
- Include `--message` on direct `canvas update` commands, or use `staging update` + `staging commit`.

```bash
# connected component around one seed node (recommended default for existing canvases)
superplane apps canvas update \
  -f canvas.yaml \
  --message "Re-layout canvas" \
  --auto-layout horizontal \
  --auto-layout-scope connected-component \
  --auto-layout-node <node-id>

# full canvas (use sparingly; see policy below)
superplane apps canvas update -f canvas.yaml --message "Re-layout canvas" --auto-layout horizontal
```

Rules and behavior:
- `--auto-layout` is required when using `--auto-layout-scope` or `--auto-layout-node`.
- `--message` is required on direct `canvas update` commands.
- Supported algorithm: `horizontal`.
- Supported scopes: `full-canvas`, `connected-component`.
- Default scope behavior:
  - If no seed nodes are provided: behaves like `full-canvas`.
  - If seed nodes are provided and scope omitted: behaves like `connected-component`.
- Recommended policy for agents:
  - Prefer `connected-component` for existing/disconnected canvases.
  - Use `full-canvas` only when creating from scratch, when the graph is one connected component, or when the user explicitly asks for full-canvas layout.
- Scope selection default:
  - If a changed/selected node ID is known, use `connected-component` + `--auto-layout-node`.
  - If a set of changed node IDs is known, use `connected-component` + repeated `--auto-layout-node`.
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
superplane runs list --app-id <id>
superplane runs describe <run-id> --app-id <id>
```

### 6. Troubleshooting Checklist

Run after every canvas update:

```bash
superplane apps canvas get <name>
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
5. `superplane apps canvas update -f canvas.yaml --message "Fix integration"` — apply the fix (or use `staging update` + `staging commit`)
6. `superplane apps canvas get <name-or-id>` — verify errors are cleared

## When to Use Other Skills

| Need | Use Skill |
| --- | --- |
| Design a canvas from requirements | superplane-app-builder |
| Debug a failed execution | superplane-monitor |

## Documentation

For agents that can fetch URLs, the full SuperPlane docs are available in LLM-friendly format:

- Compact index: https://docs.superplane.com/llms.txt
- Full content: https://docs.superplane.com/llms-full.txt

## References

- [Canvas YAML Spec](references/canvas-yaml-spec.md) — Full YAML format with examples
- [Console YAML Spec](references/console-yaml-spec.md) — Stable console YAML envelope and layout format
