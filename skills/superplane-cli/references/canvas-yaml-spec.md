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
    x: 600
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
    x: 1080
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

Downstream nodes go ~480px right. Parallel branches use different `y` values.

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
| If | `True`, `False` |
| Approval | `approved`, `rejected` |
| Everything else | `default` |

Typical gated flow:

```
Trigger → CI component
CI (passed) → Approval
Approval (approved) → Deploy component
```

## Expressions

Use [Expr language](https://expr-lang.org) inside `{{ }}`:

```yaml
url: "https://api.example.com/repos/{{ $['GitHub Push'].repository.full_name }}"
```

| Pattern | Description |
| --- | --- |
| `$['Node Name'].field` | Named node's output |
| `root()` | Root trigger payload |
| `previous()` | Immediate upstream payload |
| `previous(n)` | N levels upstream |

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
        ref: "{{ $['github.onPush'].ref }}"
      position: { x: 600, y: 100 }
      paused: false
      isCollapsed: false

    - id: approval-gate
      name: approval
      type: TYPE_COMPONENT
      component:
        name: approval
      configuration: {}
      position: { x: 1080, y: 100 }
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
