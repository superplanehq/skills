# Canvas YAML Specification

Export with `superplane canvases get <name>`, or author from scratch.

## Structure

```yaml
apiVersion: v1
kind: Canvas
metadata:
  id: <uuid>           # assigned on create, required for update
  name: My Canvas
spec:
  nodes: [...]
  edges: [...]
```

## Nodes

### Trigger Node

```yaml
- id: trigger-main
  name: github.onPush
  type: TYPE_TRIGGER
  trigger:
    name: github.onPush
  integration:
    id: <github-integration-id>
    name: ""
  configuration:
    repository: owner/repo
    refs:
      - type: equals
        value: refs/heads/main
  position:
    x: 120
    y: 100
  paused: false
  isCollapsed: false
```

### Component Node

```yaml
- id: component-ci
  name: semaphore.runWorkflow
  type: TYPE_COMPONENT
  component:
    name: semaphore.runWorkflow
  integration:
    id: <semaphore-integration-id>
    name: ""
  configuration:
    project: <project-id>
    pipelineFile: .semaphore/semaphore.yml
    ref: refs/heads/main
  position:
    x: 720
    y: 100
  paused: false
  isCollapsed: false
```

### Built-in Component (no integration)

```yaml
- id: approval-gate
  name: approval
  type: TYPE_COMPONENT
  component:
    name: approval
  configuration: {}
  position:
    x: 1320
    y: 100
  paused: false
  isCollapsed: false
```

### Node Fields

| Field | Required | Description |
| --- | --- | --- |
| `id` | Yes | Unique ID within the canvas |
| `name` | Yes | Display name — keep unique to avoid warnings |
| `type` | Yes | `TYPE_TRIGGER` or `TYPE_COMPONENT` |
| `trigger.name` | Triggers | Trigger type (e.g. `github.onPush`) |
| `component.name` | Components | Component type (e.g. `semaphore.runWorkflow`) |
| `integration.id` | Integration nodes | Connected integration instance ID |
| `integration.name` | No | Can be empty string |
| `paused` | No | Disable without removing (default: `false`) |
| `isCollapsed` | No | Collapse in UI (default: `false`) |
| `position.x`, `position.y` | Yes | Canvas UI position |
| `configuration` | Yes | Type-specific config |
| `errorMessage` | Read-only | Server-set validation error |
| `warningMessage` | Read-only | Server-set warning (e.g. duplicate names) |

### Positioning

Nodes are rendered on a canvas at `position.x` and `position.y`. Proper spacing prevents overlapping in the UI.

**Node dimensions:** each node card is approximately **515px wide × 215px tall**.

**Layout rules:**

| Direction | Spacing | Rule |
| --- | --- | --- |
| Horizontal (x) | **600px** between columns | Each sequential step adds 600 to x (515 node width + 85 gap) |
| Vertical (y) | **300px** between rows | Each parallel branch adds 300 to y (215 node height + 85 gap) |

**Linear pipeline** — all nodes share the same y, increment x by 600:

```
Node 1: { x: 120, y: 100 }
Node 2: { x: 720, y: 100 }
Node 3: { x: 1320, y: 100 }
Node 4: { x: 1920, y: 100 }
```

**Branching (fan-out)** — branches spread vertically from a shared x column. Center the source node vertically relative to its branches:

```
                          ┌─ Branch A: { x: 1320, y: 100 }
Source: { x: 720, y: 250 } ─┤
                          └─ Branch B: { x: 1320, y: 400 }
```

For 3 branches, use y values like 100, 400, 700 with the source at y: 400.

**Fan-in (Merge)** — place the merge node at the same x as the next column after the branches, with y centered between the branch rows:

```
Branch A: { x: 1320, y: 100 } ─┐
                                ├─ Merge: { x: 1920, y: 250 }
Branch B: { x: 1320, y: 400 } ─┘
```

**Starting position:** use `{ x: 120, y: 100 }` for the first node (the trigger).

## Edges

```yaml
edges:
  - sourceId: trigger-main
    targetId: component-ci
    channel: default
```

### Output Channels

| Component | Channels |
| --- | --- |
| Filter | `passed`, `failed` |
| If | `true`, `false` |
| Approval | `approved`, `rejected` |
| Everything else | `default` |

Typical gated flow:

```
Trigger → CI component
CI (passed) → Approval
Approval (approved) → Deploy component
```

## Expressions

Use [Expr language](https://expr-lang.org) inside `{{ }}`.

Every node output and `root()` returns an **envelope**: `{ data: {...}, timestamp, type }`. Access actual payload fields via `.data`:

```yaml
url: "https://api.example.com/repos/{{ $['GitHub Push'].data.repository.full_name }}"
```

| Pattern | Description |
| --- | --- |
| `$['Node Name'].data.field` | Named node's output field |
| `root().data.field` | Root trigger event field |
| `previous().data.field` | Immediate upstream field |
| `previous(n).data.field` | N levels upstream |

## Complete Example

GitHub push triggers Semaphore CI, then requires approval before deploy:

```yaml
apiVersion: v1
kind: Canvas
metadata:
  id: <canvas-id>
  name: Deploy Pipeline
spec:
  nodes:
    - id: trigger-main
      name: github.onPush
      type: TYPE_TRIGGER
      trigger:
        name: github.onPush
      integration:
        id: <github-integration-id>
        name: ""
      configuration:
        repository: myorg/myapp
        refs:
          - type: equals
            value: refs/heads/main
      position: { x: 120, y: 100 }
      paused: false
      isCollapsed: false

    - id: component-ci
      name: semaphore.runWorkflow
      type: TYPE_COMPONENT
      component:
        name: semaphore.runWorkflow
      integration:
        id: <semaphore-integration-id>
        name: ""
      configuration:
        project: myapp
        pipelineFile: .semaphore/semaphore.yml
        ref: "{{ $['github.onPush'].data.ref }}"
      position: { x: 720, y: 100 }
      paused: false
      isCollapsed: false

    - id: approval-gate
      name: approval
      type: TYPE_COMPONENT
      component:
        name: approval
      configuration: {}
      position: { x: 1320, y: 100 }
      paused: false
      isCollapsed: false

  edges:
    - sourceId: trigger-main
      targetId: component-ci
      channel: default
    - sourceId: component-ci
      targetId: approval-gate
      channel: passed
```
