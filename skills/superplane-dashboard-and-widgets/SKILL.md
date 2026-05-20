---
name: superplane-dashboard-and-widgets
description: Create, export, and update SuperPlane canvas dashboards through the SuperPlane CLI. Use when the user asks to build a dashboard, add markdown/node/table/chart/number widgets, configure widget data sources, export dashboard YAML, or apply a dashboard to a canvas.
---

# SuperPlane dashboard and widgets

Use this skill to create or change a **canvas dashboard** with the `superplane` CLI. Do not edit application source code unless the user explicitly asks for product implementation work.

## Quick reference

| Task | Command |
| --- | --- |
| Verify CLI session | `superplane whoami` |
| List canvases | `superplane canvases list` |
| Export dashboard | `superplane canvases dashboard get <canvas> -o yaml > dashboard.yaml` |
| Create or replace dashboard | `superplane canvases dashboard create <canvas> --file dashboard.yaml` |
| Update dashboard | `superplane canvases dashboard update <canvas> --file dashboard.yaml` |
| Export as JSON | `superplane canvases dashboard get <canvas> -o json` |

`create`, `update`, and `apply` are equivalent for dashboards: one dashboard exists per canvas, and importing a dashboard replaces all panels and layout items.

## Required workflow

1. Confirm the CLI is installed and authenticated:

```bash
superplane whoami
```

If this fails because the command is missing, stop and tell the user to install the SuperPlane CLI. If it fails due auth/network, ask the user to connect first.

2. Resolve the target canvas:

```bash
superplane canvases list
```

Use the exact canvas name or ID in all dashboard commands.

3. Export the current dashboard before changing it:

```bash
superplane canvases dashboard get <canvas> -o yaml > dashboard.yaml
```

If the dashboard is empty, keep the exported skeleton and add panels under `spec.panels` plus matching layout items under `spec.layout`.

4. Apply the dashboard:

```bash
superplane canvases dashboard update <canvas> --file dashboard.yaml
```

5. Verify:

```bash
superplane canvases dashboard get <canvas> -o yaml
```

## Dashboard YAML shape

```yaml
apiVersion: v1
kind: Dashboard
metadata:
  name: Deploy overview
spec:
  panels:
    - id: status
      type: markdown
      content:
        title: Status
        body: "Current deploy health"
  layout:
    - i: status
      x: 0
      y: 0
      w: 4
      h: 3
```

Rules:
- `layout[].i` must match a panel `id`.
- Dashboard import is replace-all.
- Maximum 50 panels.
- `metadata.canvasId` from exports is informational; the command target decides which canvas is updated.
- User-facing name is **SuperPlane**.

## Panel types

### Markdown

```yaml
- id: notes
  type: markdown
  content:
    title: Notes
    body: |
      ## Release checklist
      - Build passed
      - Approval pending
```

### Node

Shows node status and optionally lets users run a trigger node.

```yaml
- id: deploy-node
  type: node
  content:
    node: Deploy
    showRun: true
    triggerName: run
```

Use the node ID or exact node name from the canvas.

### Table

Use tables for memory rows, executions, or runs. Row actions can only trigger trigger nodes.

```yaml
- id: incidents
  type: table
  content:
    dataSource:
      kind: memory
      namespace: incidents
    render:
      kind: table
      columns:
        - field: title
          label: Incident
        - field: status
          label: Status
          format: status
      where:
        - field: status
          op: neq
          value: closed
      actions:
        - label: Acknowledge
          kind: trigger
          node: acknowledge-incident
          payload:
            incidentId: "{{ row.id }}"
```

### Chart

```yaml
- id: failures-by-node
  type: chart
  content:
    dataSource:
      kind: executions
      limit: 100
    render:
      kind: chart
      type: bar
      xField: nodeName
      series:
        - label: Failures
```

### Number

```yaml
- id: total-runs
  type: number
  content:
    dataSource:
      kind: runs
    render:
      kind: number
      aggregation: count
      label: Runs
```

## Data sources

```yaml
dataSource:
  kind: memory
  namespace: incidents
  fieldPath: items
```

```yaml
dataSource:
  kind: executions
  node: Deploy
  limit: 50
```

```yaml
dataSource:
  kind: runs
  limit: 50
```

Notes:
- Memory `namespace` must match canvas memory keys.
- `fieldPath` flattens nested lists for memory tables.
- Execution rows include `status`, `nodeName`, and `durationMs`.
- Status values are `passed`, `failed`, `running`, `pending`, `cancelled`, `unknown`.

## Layout

Dashboards use a 12-column grid. Common sizes:
- KPI number: `w: 3`, `h: 2`
- Node status: `w: 4`, `h: 3`
- Markdown: `w: 4`, `h: 3`
- Table: `w: 12`, `h: 6`
- Chart: `w: 6`, `h: 4`

Example:

```yaml
layout:
  - i: total-runs
    x: 0
    y: 0
    w: 3
    h: 2
  - i: failures-by-node
    x: 0
    y: 2
    w: 6
    h: 4
  - i: incidents
    x: 0
    y: 6
    w: 12
    h: 6
```

## Agent behavior

- Use CLI export/apply loops, not source-code edits.
- Preserve existing panels unless the user asks to replace the dashboard.
- Prefer stable panel IDs (`deploy-status`, `failure-chart`) instead of generated UUIDs.
- Keep tables actionable only through trigger nodes.
- When uncertain about node names, export the canvas with `superplane canvases get <canvas> -o yaml` and inspect node IDs/names before writing dashboard YAML.
