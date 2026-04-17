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
| Set active canvas | `superplane canvases active [canvas-id]` |
| List/switch contexts | `superplane contexts` |
| List canvases | `superplane canvases list` |
| Generate starter YAML | `superplane canvases init` |
| Generate from template | `superplane canvases init --template <name>` |
| List canvas templates | `superplane canvases init --list-templates` |
| Create canvas | `superplane canvases create <name>` then `superplane canvases update <name> --draft` |
| Create canvas from YAML | `superplane canvases create --file canvas.yaml` |
| Export canvas | `superplane canvases get <name>` |
| Update canvas | `superplane canvases update <name-or-id> --draft --file canvas.yaml` |
| Auto layout full canvas | `superplane canvases update <name-or-id> --draft --auto-layout horizontal` |
| Auto layout connected subgraph | `superplane canvases update <name-or-id> --draft --auto-layout horizontal --auto-layout-scope connected-component --auto-layout-node <node-id>` |
| Auto layout exact selected set | `superplane canvases update <name-or-id> --draft --auto-layout horizontal --auto-layout-scope exact-set --auto-layout-node <node-a> --auto-layout-node <node-b>` |
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

Before any CLI operation, confirm the CLI binary is available without requiring network access:

```bash
command -v superplane
```

If this does not print a path, the CLI is **not installed**. Stop and tell the user:

> The SuperPlane CLI is not installed. Install it from https://docs.superplane.com/installation/cli and then re-run this task.

Do **not** attempt to install the CLI on behalf of the user. Do **not** continue with doc-based guesswork — the CLI provides exact trigger names, component names, integration IDs, and config schemas that documentation cannot reliably substitute.

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

### 1b. Apply Canvas Changes as Drafts

Versioning is always on in this environment. Do not branch on a canvas mode flag; use the draft update path for every canvas edit.

```bash
superplane canvases update <name-or-id> --draft --file canvas.yaml
```

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

Generate a starter YAML, then create and iterate:

```bash
superplane canvases init --output-file canvas.yaml
# or start from a template:
superplane canvases init --template health-check-monitor --output-file canvas.yaml
# edit canvas.yaml, then create:
superplane canvases create --file canvas.yaml
# or create a blank canvas and iterate:
superplane canvases create my-canvas
superplane canvases update my-canvas --draft
superplane canvases get my-canvas > canvas.yaml
# edit canvas.yaml
superplane canvases update my-canvas --draft --file canvas.yaml
```

If you create a canvas from YAML, `create --file` already sends the full canvas payload. Do not assume a second update is required just to apply the graph:

```bash
superplane canvases create --file canvas.yaml
```

Workflow rules:
- `superplane canvases create --file canvas.yaml` accepts the same resource-style Canvas YAML described in the spec (`apiVersion`, `kind`, `metadata`, `spec`).
- Run a follow-up `superplane canvases update ...` only when you are intentionally changing the canvas after create, for example to apply additional edits from a file that includes `metadata.id`, or to run auto-layout with different flags than the defaults used on create.
- In this environment, every `superplane canvases update ...` command should include `--draft`.

See [Canvas YAML Spec](references/canvas-yaml-spec.md) for the full format.

### Auto Layout via CLI

Use `canvases update` with auto-layout flags:

Default agent behavior:
- Auto layout is applied by default on `superplane canvases update` when no auto-layout flags are provided.
- Use `--auto-layout` flags when you need explicit scope/seed-node control.
- Include `--draft` on every update command in this environment.

```bash
# connected component around one seed node (recommended default for existing canvases)
superplane canvases update <name-or-id> --draft \
  --auto-layout horizontal \
  --auto-layout-scope connected-component \
  --auto-layout-node <node-id>

# exact node set only (best when the user selected nodes)
superplane canvases update <name-or-id> --draft \
  --auto-layout horizontal \
  --auto-layout-scope exact-set \
  --auto-layout-node <node-a> \
  --auto-layout-node <node-b>

# full canvas (use sparingly; see policy below)
superplane canvases update <name-or-id> --draft --auto-layout horizontal
```

Rules and behavior:
- `--auto-layout` is required when using `--auto-layout-scope` or `--auto-layout-node`.
- `--draft` is required on update commands in this environment.
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
5. `superplane canvases update <name-or-id> --draft --file canvas.yaml` — apply the fix
6. `superplane canvases get <name>` — verify errors are cleared

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
