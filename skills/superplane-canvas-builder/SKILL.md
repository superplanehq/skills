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

## Design Process

### 1. Understand the Workflow

Identify:
- **What starts it?** → trigger (schedule, webhook, GitHub push, manual)
- **What steps happen?** → each step is a component node
- **Any decisions?** → If or Filter components for branching
- **Any waits?** → Approval, Time Gate, Wait components
- **Which external systems?** → each maps to an integration

### 2. Select Components

```bash
superplane index integrations
superplane index components --from github
```

See [Components & Triggers Reference](references/components-and-triggers.md) for the full list.

### 3. Wire the Graph

- Every component needs at least one incoming edge
- Triggers have no incoming edges
- Use named channels for branching (Filter → `passed`/`failed`, If → `True`/`False`)
- Use Merge to fan-in parallel branches

### 4. Configure Expressions

Reference upstream data with Expr language inside `{{ }}`:

| Pattern | Description |
| --- | --- |
| `$['Node Name'].field` | Named node's output |
| `root()` | Trigger event payload |
| `previous()` | Immediate upstream payload |

### 5. Apply

```bash
superplane canvases create --file canvas.yaml
```

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
| Run CLI commands | superplane-cli |
| Debug a failed run | superplane-monitor |

## References

- [Components & Triggers](references/components-and-triggers.md) — All built-in components and trigger types
