# Console YAML Specification

Export with `superplane apps console get <app-name-or-id> -o yaml`, edit locally, then apply with `superplane apps console set --draft-id <draft-id> -f console.yaml`.

The CLI command group is `apps console`. The user-facing YAML kind is always `Console`.

## Draft id

Resolve the target draft before read/write:

```bash
superplane apps drafts list <name-or-id>
superplane apps drafts create <name-or-id> [--name "..."]
```

Use the returned id as `--draft-id` on every console command below.

## Commands

```bash
# Show summary for live console
superplane apps console get <name-or-id>

# Export live console as canonical YAML
superplane apps console get <name-or-id> -o yaml > console.yaml

# Export a specific draft console
superplane apps console get <name-or-id> --draft-id <draft-id> -o yaml > console.yaml

# Replace a draft console from a file
superplane apps console set --draft-id <draft-id> -f console.yaml
superplane apps console set <name-or-id> --draft-id <draft-id> -f console.yaml

# Read YAML from stdin
superplane apps console set <name-or-id> --draft-id <draft-id> -f - < console.yaml
```

If an app is active via `superplane apps active`, the app argument may be omitted:

```bash
superplane apps drafts list
superplane apps console get -o yaml > console.yaml
superplane apps console set --draft-id <draft-id> -f console.yaml
```

## Behavior

- `get` without `--draft-id` reads the live console.
- `get --draft-id` reads that draft's console and errors if the id is invalid or not a draft you own.
- `set --draft-id` writes panels and layout to the specified draft version.
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
