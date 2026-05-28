# Console YAML Specification

Export with `superplane console get <name-or-id> -o yaml`, edit locally, then apply with `superplane console set <name-or-id> -f console.yaml`.

The CLI command group is `console`. The user-facing YAML kind is always `Console`.

## Commands

```bash
# Show summary for live console
superplane console get <name-or-id>

# Export live console as canonical YAML
superplane console get <name-or-id> -o yaml > console.yaml

# Export the current user's existing draft console
superplane console get <name-or-id> --draft -o yaml > console.yaml

# Replace the current user's console draft from a file
superplane console set <name-or-id> -f console.yaml

# Same, but keep the operation explicitly draft-only
superplane console set <name-or-id> -f console.yaml --draft

# Read YAML from stdin
superplane console set <name-or-id> -f - < console.yaml
```

If a canvas is active via `superplane canvases active`, the canvas argument may be omitted:

```bash
superplane console get -o yaml > console.yaml
superplane console set -f console.yaml
```

## Behavior

- `get` reads the live console by default.
- `get --draft` reads the current user's existing draft console and errors if no draft exists.
- `set` always writes to the current user's draft version.
- `set --draft` keeps the operation explicitly draft-only.
- Import is replace-all: the submitted `spec.panels` and `spec.layout` replace all existing console panels and layout entries.
- `metadata.canvasId` and `metadata.name` are informational on import.

## Structure

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
| `type` | Yes | One of `markdown`, `node`, `nodes`, `table`, `chart`, `number` |
| `content` | Usually | Type-specific object; markdown may be empty |

Limits and validation:

- Maximum panels: 50.
- Encoded panel payload maximum: 1 MiB.
- Panel ids must be unique.
- Unsupported panel types are rejected.

### Markdown Panel

```yaml
- id: intro
  type: markdown
  content:
    title: Overview
    body: "# Runbook\nUse this console during deploys."
```

Content fields:

| Field | Required | Description |
| --- | --- | --- |
| `title` | No | String title |
| `body` | No | Markdown body |

### Node Panel

```yaml
- id: deploy-node
  type: node
  content:
    title: Deploy
    node: deploy-production
    showRun: true
    triggerName: manual
```

Content fields:

| Field | Required | Description |
| --- | --- | --- |
| `node` | Yes | Canvas node id or name; may be an empty string while unconfigured |
| `title` | No | String title |
| `showRun` | No | Boolean; shows a manual-run button when allowed |
| `triggerName` | No | Trigger template name for nodes with multiple triggers |

### Nodes Panel

```yaml
- id: key-nodes
  type: nodes
  content:
    title: Key Nodes
    nodes:
      - node: build
        label: Build
        description: Compile and test
      - node: deploy-production
        label: Deploy
        showRun: true
        triggerName: manual
```

Content fields:

| Field | Required | Description |
| --- | --- | --- |
| `nodes` | Yes | Array; may be empty while unconfigured |
| `title` | No | String title |

Each `nodes[]` entry needs a non-empty `node` string. Optional entry fields: `label`, `description`, `showRun`, `triggerName`.

### Shared Data Sources

Table and chart panels use the shared data-source shapes. Number panels use these too, plus a composite memory form.

```yaml
dataSource:
  kind: memory
  namespace: deployment
  fieldPath: items
```

```yaml
dataSource:
  kind: executions
  node: deploy-production
  limit: 100
```

```yaml
dataSource:
  kind: runs
  limit: 100
```

Supported kinds:

| Kind | Fields |
| --- | --- |
| `memory` | `namespace` string, optional `fieldPath` string |
| `executions` | Optional `node` string, optional `limit` number |
| `runs` | Optional `limit` number |

### Table Panel

```yaml
- id: recent-failures
  type: table
  content:
    title: Recent Failures
    dataSource:
      kind: executions
      node: deploy-production
      limit: 50
    render:
      kind: table
      columns:
        - field: status
          label: Status
        - field: ref
          label: Ref
      where:
        - field: status
          op: eq
          value: failed
      sort:
        field: createdAt
        order: desc
```

Required render fields:

| Field | Required | Description |
| --- | --- | --- |
| `kind` | Yes | Must be `table` |
| `columns` | Yes | Array of objects with non-empty `field` |

Optional render fields:

- `where`: array of filters. Supported ops: `eq`, `neq`, `contains`, `not_contains`, `gt`, `lt`, `exists`, `not_exists`.
- `sort`: object with non-empty `field` and optional `order` of `asc` or `desc`.
- `rowActions`: array of trigger actions. Each action must have `kind: trigger` and a `node` or `target`.

### Chart Panel

```yaml
- id: runs-by-status
  type: chart
  content:
    title: Runs by Status
    dataSource:
      kind: runs
      limit: 100
    render:
      kind: chart
      type: bar
      xField: status
      series:
        - field: count
          label: Runs
      legend: auto
      sort:
        field: status
        order: asc
```

Required render fields:

| Field | Required | Description |
| --- | --- | --- |
| `kind` | Yes | Must be `chart` |
| `type` | Yes | `bar`, `stacked-bar`, `line`, `area`, or `donut` |
| `xField` | Yes | Non-empty field name |
| `series` | Yes | Non-empty array |

Optional render fields:

- `series[]` may include string fields `field`, `label`, `color`, `format`, `prefix`, `suffix`.
- `legend`: `auto`, `show`, or `hide`.
- `sort`: object with non-empty `field` and optional `order` of `asc` or `desc`.

### Number Panel

```yaml
- id: failed-runs
  type: number
  content:
    title: Failed Runs
    dataSource:
      kind: runs
      limit: 100
    render:
      kind: number
      aggregation: count
      label: Failed
      prefix: ""
      suffix: " runs"
```

Required render fields for normal data sources:

| Field | Required | Description |
| --- | --- | --- |
| `kind` | Yes | Must be `number` |
| `aggregation` | Yes | `count`, `sum`, `avg`, `min`, `max`, `first`, or `last` |
| `field` | For non-`count` aggregations | Field to aggregate |

Optional render fields: `prefix`, `suffix`.

Composite memory number panels put aggregation on each source and omit render-level `aggregation` and `field`:

```yaml
- id: total-errors
  type: number
  content:
    title: Total Errors
    dataSource:
      kind: memory
      combine: sum
      sources:
        - namespace: api-errors
          aggregation: sum
          field: count
        - namespace: worker-errors
          aggregation: sum
          field: count
    render:
      kind: number
      suffix: " errors"
```

Composite memory rules:

- `dataSource.sources` must be a non-empty array.
- `dataSource.combine` must be `sum`, `min`, `max`, or `avg`.
- Each source needs `namespace` and `aggregation`.
- Source aggregation supports `count`, `sum`, `avg`, `min`, `max`, `first`, `last`.
- Each non-`count` source aggregation needs `field`.
- `fieldPath` is optional per source.

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
