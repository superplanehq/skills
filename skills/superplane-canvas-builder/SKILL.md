---
name: superplane-canvas-builder
description: Design and build SuperPlane workflow canvases from requirements. Translates workflow descriptions into canvas YAML with triggers, components, edges, and expressions. Use when the user wants to create a new workflow, build a canvas, design a pipeline, or wire up components. Triggers on "build canvas", "create workflow", "design pipeline", "automate".
---

# SuperPlane Canvas Builder

Translate workflow requirements into SuperPlane canvas YAML.

## Quick Reference

| Task | Command |
| --- | --- |
| List components | `superplane index components` |
| Components from integration | `superplane index components --from <integration>` |
| Describe a component | `superplane index components --name <name>` |
| List triggers | `superplane index triggers --from <integration>` |
| Create canvas | `superplane canvases create --file canvas.yaml` |
| Update canvas (sandbox mode) | `superplane canvases update -f canvas.yaml --auto-layout horizontal` |
| Update draft (versioning mode) | `superplane canvases update <name-or-id> --draft -f canvas.yaml --auto-layout horizontal` |
| Publish draft (versioning mode) | `superplane canvases publish <name-or-id> --title "..." --description "..."` |

## Order of Operations

Always follow this sequence. The CLI is the primary path — it gives exact names, IDs, and schemas that documentation cannot reliably substitute.

### 1. Verify CLI and Connect

```bash
superplane whoami
```

If `command not found`: **stop**. Tell the user to install the CLI from https://docs.superplane.com/installation/cli and re-run the task. Do not attempt to install it on their behalf. Do not silently fall back to doc-based design.

If not yet connected:

```bash
superplane connect <URL> <TOKEN>
superplane whoami
```

If connection details are not available, **stop** and ask the user to connect/provide the required URL and token. Do not continue without a working CLI session.

### 2. Understand the Workflow

Before running discovery commands, identify what the workflow needs:

- **What starts it?** → trigger (schedule, webhook, GitHub push, manual)
- **What steps happen?** → each step is a component node
- **Any decisions?** → If or Filter components for branching
- **Any waits?** → Approval, Time Gate, Wait components
- **Which external systems?** → each maps to a provider (e.g., GitHub, Slack, Daytona)

Collect the list of **required providers** from this analysis — you will check them in the next step.

### 3. Discover and Verify Integrations

Run `superplane integrations list` to get all connected integrations in the org. Compare against the required providers from step 2.

**If any required provider is missing:** stop and tell the user before writing any YAML. Example:

> This canvas needs GitHub and Daytona integrations. Your org has GitHub connected but **Daytona is not connected**. Please connect it in the SuperPlane UI (Settings → Integrations) before proceeding.

Do not generate YAML that references providers the org has not connected — it will fail with "integration is required" on every affected node.

**Once all providers are confirmed connected**, discover exact names and schemas:

```bash
superplane integrations list                          # connected instances → real integration IDs
superplane index triggers --from <provider>           # exact trigger names
superplane index components --from <provider>         # exact component names
```

Inspect required config fields, output channels, and payload shape:

```bash
superplane index triggers --name github.onPush --output json
superplane index components --name semaphore.runWorkflow --output json
```

List runtime options for `integration-resource` fields:

```bash
superplane integrations list-resources --id <id> --type <type>
```

**Hard gate before writing/applying YAML:** for every `integration-resource` field value you set (for example: `repository`, `snapshot`, `sandbox`, `project`), verify the exact value exists in `list-resources` output for that integration. If it does not exist, stop and ask the user which valid value to use.

**Schema precedence rule:** if provider reference examples conflict with CLI schema output (`superplane index ... --output json`) or current `list-resources` values, follow CLI output. References are helper material; CLI is source of truth.

### 4. Select Components and Wire the Graph

Use the **exact** trigger and component names from step 3 — not guesses from documentation.

- If the trigger supports built-in filtering (content filter, action filter, ref filter), configure it at the trigger level. Only add a separate Filter or If node when you need logic the trigger's native config cannot express.
- Every component needs at least one incoming edge
- Triggers have no incoming edges
- Use named channels for branching (If → `true`/`false`, Approval → `approved`/`rejected`)
- Filter only emits to `default` when the expression is true; false events stop silently
- Use Merge to fan-in parallel branches

See [Components & Triggers Reference](references/components-and-triggers.md) for the full list.

### 5. Position Nodes

Every node needs a `position: { x, y }`. Nodes are **515px wide × 215px tall** — use these spacing rules to prevent overlap:

| Direction | Increment | Why |
| --- | --- | --- |
| Horizontal (x) | **+600px** per column | 515 width + 85 gap |
| Vertical (y) | **+300px** per row | 215 height + 85 gap |

Start the first node (trigger) at `{ x: 120, y: 100 }`.

**Linear pipeline** — same y, increment x:

```
Trigger: { x: 120, y: 100 }  →  Step A: { x: 720, y: 100 }  →  Step B: { x: 1320, y: 100 }
```

**Branching** — branches share the same x column, spread on y. Center the source node vertically relative to its branches:

```
                                ┌─ Branch A: { x: 1320, y: 100 }
Source: { x: 720, y: 250 }  ───┤
                                └─ Branch B: { x: 1320, y: 400 }
```

**Fan-in (Merge)** — next x column after branches, y centered between them:

```
Branch A: { x: 1320, y: 100 } ──┐
                                 ├── Merge: { x: 1920, y: 250 }
Branch B: { x: 1320, y: 400 } ──┘
```

For 3+ branches, keep adding 300 to y for each branch and center the source/merge accordingly.

### 6. Configure Expressions

> **STOP** before writing any expression that references payload fields you have not confirmed. Do not guess field paths from trigger or component names.

#### Envelope

Every node output is wrapped in an envelope: `{ data: {...}, timestamp, type }`. All three access patterns return this envelope, so you always need `.data.` to reach the actual payload:

| Pattern | Description |
| --- | --- |
| `$['Node Name'].data.field` | Access any upstream node's output by name |
| `root().data.field` | Access the root event that started the run |
| `previous().data.field` | Access the immediate upstream node's output |

> **Common mistake:** writing `$['Create Sandbox'].id` instead of `$['Create Sandbox'].data.id`. Always include `.data.`.

Use double curly braces `{{ }}` for expressions in configuration fields:

```
{{ $['GitHub onPush'].data.ref }}
```

#### How to confirm payload fields

Check these sources in order — use the first one available:

1. **Existing executions** — inspect real payloads from prior runs (most reliable):
   ```bash
   superplane executions list --canvas-id <id> --node-id <nid> -o yaml
   ```

2. **Provider reference files in this skill** — check the `references/` directory for the provider you are using. These contain payload examples and known gotchas.

3. **SuperPlane docs** — fetch the provider's component page from the LLM-friendly docs:
   - Compact index: https://docs.superplane.com/llms.txt
   - Full content: https://docs.superplane.com/llms-full.txt

After the first real execution, always go back to source 1 to verify and correct expressions. The trigger name does not map 1:1 to payload structure — always check the provider reference file or docs for the actual webhook event a trigger maps to.

### 6b. Command Node Best Practices

When a component executes shell commands (e.g., `daytona.executeCommand`, `ssh`):

- **Use the component's native `workingDirectory` / `envVars` config** instead of inline `cd` or `export` in the shell string. This reduces quoting complexity and failure surface.
- **Redirect verbose output to a file** and emit a concise status marker to stdout (e.g., `STEP_OK` / `STEP_FAILED`). Large or binary stdout can cause node processing issues.
- **Check the provider reference file** (`references/` directory) for the shell execution model, hardened command templates, and known failure patterns specific to that integration.
- For long multi-step scripts, prefer YAML block scalar (`command: |-`) over folded single-line strings to avoid whitespace/newline parse artifacts in `bash -lc`.
- Before shipping, run one manual trigger and inspect node `outputs` in execution YAML to confirm expected channel routing (`success` vs `failed`) matches your edge wiring.

### 7. Apply

```bash
superplane canvases create --file canvas.yaml
# or update an existing canvas:
superplane canvases update <name-or-id> [--draft] --file canvas.yaml --auto-layout horizontal
```

When creating a new canvas from YAML, **always** run a follow-up auto-layout update:

```bash
superplane canvases create --file canvas.yaml
superplane canvases update <name-or-id> [--draft] --auto-layout horizontal
# if --draft was used (versioning mode):
superplane canvases publish <name-or-id> --title "Initial publish"
```

Mode rules:
- Sandbox mode enabled: update applies to live directly (no `--draft`).
- Sandbox mode disabled: update requires `--draft`; publish is required to make changes live.

Then verify:

```bash
superplane canvases get <name>
```

Check for `errorMessage` or `warningMessage` on any node.

### 8. Definition of Done (Canvas Creation)

Before calling the canvas "ready", confirm all of the following:

- Integration IDs resolved from `superplane integrations list`
- Every `integration-resource` value verified via `superplane integrations list-resources`
- Canvas created and follow-up auto-layout update applied
- `superplane canvases get <name> -o yaml` shows empty `errorMessage` and `warningMessage` on all nodes
- At least one real trigger run checked, including channel-level `outputs` from critical branching nodes

## Common Patterns

### Linear: Trigger → A → B → C

```yaml
nodes:
  - { id: trigger, ..., position: { x: 120, y: 100 } }
  - { id: a, ..., position: { x: 720, y: 100 } }
  - { id: b, ..., position: { x: 1320, y: 100 } }
  - { id: c, ..., position: { x: 1920, y: 100 } }
edges:
  - { sourceId: trigger, targetId: a, channel: default }
  - { sourceId: a, targetId: b, channel: default }
  - { sourceId: b, targetId: c, channel: default }
```

### Branch: If → true / false

```yaml
nodes:
  - { id: trigger, ..., position: { x: 120, y: 250 } }
  - { id: check, ..., component: { name: if }, position: { x: 720, y: 250 } }
  - { id: on-true, ..., position: { x: 1320, y: 100 } }
  - { id: on-false, ..., position: { x: 1320, y: 400 } }
edges:
  - { sourceId: trigger, targetId: check, channel: default }
  - { sourceId: check, targetId: on-true, channel: true }
  - { sourceId: check, targetId: on-false, channel: false }
```

### Gate: Filter (pass or stop)

Filter only emits to `default` when true. False events stop — no edge needed.

```yaml
nodes:
  - { id: trigger, ..., position: { x: 120, y: 100 } }
  - { id: filter, ..., component: { name: filter }, position: { x: 720, y: 100 } }
  - { id: next-step, ..., position: { x: 1320, y: 100 } }
edges:
  - { sourceId: trigger, targetId: filter, channel: default }
  - { sourceId: filter, targetId: next-step, channel: default }
```

### Fan-out / Fan-in

```yaml
nodes:
  - { id: trigger, ..., position: { x: 120, y: 250 } }
  - { id: a, ..., position: { x: 720, y: 100 } }
  - { id: b, ..., position: { x: 720, y: 400 } }
  - { id: merge, ..., position: { x: 1320, y: 250 } }
  - { id: final, ..., position: { x: 1920, y: 250 } }
edges:
  - { sourceId: trigger, targetId: a, channel: default }
  - { sourceId: trigger, targetId: b, channel: default }
  - { sourceId: a, targetId: merge, channel: default }
  - { sourceId: b, targetId: merge, channel: default }
  - { sourceId: merge, targetId: final, channel: default }
```

### Approval Gate

```yaml
nodes:
  - { id: ci-done, ..., position: { x: 120, y: 100 } }
  - { id: timegate, ..., position: { x: 720, y: 100 } }
  - { id: approval, ..., position: { x: 1320, y: 100 } }
  - { id: deploy, ..., position: { x: 1920, y: 100 } }
edges:
  - { sourceId: ci-done, targetId: timegate, channel: default }
  - { sourceId: timegate, targetId: approval, channel: default }
  - { sourceId: approval, targetId: deploy, channel: approved }
```

## When to Use Other Skills

| Need | Use Skill |
| --- | --- |
| CLI commands and authentication | superplane-cli |
| Debug a failed run | superplane-monitor |

## Documentation

For agents that can fetch URLs, the full SuperPlane docs are available in LLM-friendly format:

- Compact index: https://docs.superplane.com/llms.txt
- Full content: https://docs.superplane.com/llms-full.txt

## References

- [Components & Triggers](references/components-and-triggers.md) — Built-in components and trigger types
- [GitHub](references/github.md) — Triggers, components, payload examples, gotchas
- [Daytona](references/daytona.md) — Components, payload examples, gotchas
