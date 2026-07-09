# Console YAML Specification

Export with `superplane apps console get <app-name-or-id> -o yaml`, edit locally, then apply with `superplane apps console set -f console.yaml --message "..."` or via staging.

The CLI command group is `apps console`. The user-facing YAML kind is always `Console`.

## Commands

```bash
# Show summary for live console
superplane apps console get <name-or-id>

# Export live console as canonical YAML
superplane apps console get <name-or-id> -o yaml > console.yaml

# Replace the live console and commit immediately
superplane apps console set -f console.yaml --message "Update console"
superplane apps console set <name-or-id> -f console.yaml --message "Update console"

# Read YAML from stdin
superplane apps console set <name-or-id> -f - --message "Update console" < console.yaml

# Stage console changes without committing immediately
superplane apps staging update --file console.yaml
superplane apps staging commit --message "Update console"
```

If an app is active via `superplane apps active`, the app argument may be omitted:

```bash
superplane apps console get -o yaml > console.yaml
superplane apps console set -f console.yaml --message "Update console"
```

## Behavior

- `get` reads the live (committed) console.
- `set --message` writes panels and layout and commits immediately.
- To stage console edits without committing, use `staging update --file console.yaml` then `staging commit`.
- Import is replace-all: the submitted `spec.panels` and `spec.layout` replace all existing console panels and layout entries.
- `metadata.canvasId` and `metadata.name` are informational on import.

## Current Widget Details

Console widgets change frequently. Before authoring or editing non-trivial panel `content`, read the product console guide:

- Mounted agent resource: `ref/docs/prd/console-and-widgets.md`
- Canonical source: https://github.com/superplanehq/superplane/blob/main/docs/prd/console-and-widgets.md

Use that guide as the source of truth for widget content schemas, table data sources, row actions, chart options, number aggregations, field formats, and implementation files that must stay in sync.

## Stable Structure

```yaml
apiVersion: v1
kind: Console
metadata:
  canvasId: <uuid>        # optional, informational
  name: My Canvas         # optional, informational
spec:
  panels:
    - id: intro
      type: markdown
      content:
        title: Overview
        body: "# Deployment runbook"
  layout:
    - i: intro
      x: 0
      y: 0
      w: 12
      h: 6
      minW: 2
      minH: 2
```

## Panels

Every panel needs:

| Field | Required | Description |
| --- | --- | --- |
| `id` | Yes | Unique panel id within this console |
| `type` | Yes | One of the panel types documented in the product console guide |
| `content` | Usually | Type-specific object; read the product console guide before editing widget content |

Stable validation rules:

- Maximum panels: 50.
- Encoded panel payload maximum: 1 MiB.
- Panel ids must be unique.
- Unsupported panel types are rejected.

## Layout

Each `spec.layout` item places one panel in the console grid.

```yaml
layout:
  - i: intro
    x: 0
    y: 0
    w: 12
    h: 6
    minW: 2
    minH: 2
```

| Field | Required | Description |
| --- | --- | --- |
| `i` | Yes | Panel id this layout item controls |
| `x` | Yes | Non-negative grid column |
| `y` | Yes | Non-negative grid row |
| `w` | Yes | Positive grid width |
| `h` | Yes | Positive grid height |
| `minW` | No | Minimum grid width |
| `minH` | No | Minimum grid height |

Layout rules:

- Every layout `i` must reference an existing panel id.
- Layout ids must be unique.
- `x` and `y` must be non-negative.
- `w` and `h` must be positive.
- A newly added panel from the UI commonly starts at `w: 12`, `h: 6`, `minW: 2`, `minH: 2`.
