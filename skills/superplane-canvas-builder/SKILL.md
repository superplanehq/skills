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
| Update canvas | `superplane canvases update -f canvas.yaml` |

## Order of Operations

Always follow this sequence. The CLI is the primary path — it gives exact names, IDs, and schemas that documentation cannot reliably substitute.

### 1. Verify CLI and Connect

```bash
superplane whoami
```

If `command not found`: **stop**. Tell the user to install the CLI from https://docs.superplane.com/cli and re-run the task. Do not attempt to install it on their behalf. Do not silently fall back to doc-based design.

If not yet connected:

```bash
superplane connect <URL> <TOKEN>
superplane whoami
```

### 2. Understand the Workflow

Before running any discovery commands, identify what the workflow needs:

- **What starts it?** → trigger (schedule, webhook, GitHub push, manual)
- **What steps happen?** → each step is a component node
- **Any decisions?** → If or Filter components for branching
- **Any waits?** → Approval, Time Gate, Wait components
- **Which external systems?** → each maps to a provider (e.g., GitHub, Slack, Daytona)

Collect the list of **required providers** from this analysis — you will check them in the next step.

### 3. Discover and Verify Integrations

Run `superplane integrations list` to get all connected integrations in the org. Then compare against the required providers from step 2.

**If any required provider is missing:** stop and tell the user before writing any YAML. Example:

> This canvas needs GitHub and Daytona integrations. Your org has GitHub connected but **Daytona is not connected**. Please connect Daytona in the SuperPlane UI (Settings → Integrations) before proceeding.

Do not generate YAML that references providers the org has not connected — it will fail with "integration is required" on every affected node.

**Once all providers are confirmed connected**, discover exact names and schemas:

```bash
superplane integrations list                          # connected instances → real integration IDs
superplane index triggers --from <provider>           # exact trigger names for each provider
superplane index components --from <provider>         # exact component names for each provider
```

Inspect required config fields and payload shape:

```bash
superplane index triggers --name github.onPush
superplane index components --name semaphore.runWorkflow
```

List runtime options for `integration-resource` fields:

```bash
superplane integrations list-resources --id <id> --type <type>
```

### 4. Select Components and Wire the Graph (using exact names from step 3)

Use the **exact** trigger and component names from step 3 — not guesses from documentation.

- Every component needs at least one incoming edge
- Triggers have no incoming edges
- Use named channels for branching (Filter → `passed`/`failed`, If → `True`/`False`)
- Use Merge to fan-in parallel branches

### 5. Configure Expressions

Reference upstream data with Expr language inside `{{ }}`:

| Pattern | Description |
| --- | --- |
| `$['Node Name'].field` | Named node's output |
| `root()` | Trigger event payload |
| `previous()` | Immediate upstream payload |

### 6. Apply

```bash
superplane canvases create --file canvas.yaml
# or update an existing canvas:
superplane canvases update --file canvas.yaml
```

Then verify:

```bash
superplane canvases get <name>
```

Check for `errorMessage` or `warningMessage` on any node.

## Fallback: When CLI Is Not Available

If the CLI cannot be installed or used (e.g., user declines, environment restriction):

1. Build the canvas YAML from documentation and skill references.
2. Use **placeholders** for integration IDs (e.g., `<GITHUB_INTEGRATION_ID>`) and flag which providers the canvas requires.
3. Add a clear note to the user that they must:
   - Connect any missing integrations in the SuperPlane UI (Settings → Integrations).
   - Install the CLI or use the UI to obtain real integration IDs.
   - Replace all placeholders before applying.
   - Run `superplane canvases create --file canvas.yaml` (or use the UI) to apply.

This path is slower and less reliable. Always prefer the CLI.

## Common Patterns

### Linear: Trigger → A → B → C

```yaml
edges:
  - { sourceId: trigger, targetId: a, channel: default }
  - { sourceId: a, targetId: b, channel: default }
  - { sourceId: b, targetId: c, channel: default }
```

### Branch: Filter → passed / failed

```yaml
edges:
  - { sourceId: trigger, targetId: filter, channel: default }
  - { sourceId: filter, targetId: on-success, channel: passed }
  - { sourceId: filter, targetId: on-failure, channel: failed }
```

### Fan-out / Fan-in

```yaml
edges:
  - { sourceId: trigger, targetId: a, channel: default }
  - { sourceId: trigger, targetId: b, channel: default }
  - { sourceId: a, targetId: merge, channel: default }
  - { sourceId: b, targetId: merge, channel: default }
  - { sourceId: merge, targetId: final, channel: default }
```

### Approval Gate

```yaml
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
| Decision-tree troubleshooting | superplane-troubleshoot |
| Write or fix expressions | superplane-expressions |
| Connect and configure integrations | superplane-integrations |

## References

- [Canvas Patterns](references/canvas-patterns.md) — 6 complete real-world canvas YAML examples
- [Components & Triggers](references/components-and-triggers.md) — All built-in components and trigger types
