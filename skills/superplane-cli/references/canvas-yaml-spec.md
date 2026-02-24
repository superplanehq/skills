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
  edges: [...]
  nodes: [...]
```

## Nodes

### Trigger Node

```yaml
- id: schedule-trigger-abc
  name: every-5-minutes
  type: TYPE_TRIGGER
  trigger:
    name: schedule
  paused: false
  position: { x: 144, y: 0 }
  configuration:
    type: minutes
    minutesInterval: 5
```

### Component Node

```yaml
- id: http-check-xyz
  name: health-check
  type: TYPE_COMPONENT
  component:
    name: http
  paused: false
  position: { x: 624, y: 0 }
  configuration:
    method: GET
    url: "https://api.example.com/health"
```

### Node Fields

| Field | Required | Description |
| --- | --- | --- |
| `id` | Yes | Unique ID (convention: `<type>-<name>-<random>`) |
| `name` | Yes | Display name |
| `type` | Yes | `TYPE_TRIGGER` or `TYPE_COMPONENT` |
| `trigger.name` | Triggers | Trigger type from the index |
| `component.name` | Components | Component type from the index |
| `paused` | No | Disable without removing (default: `false`) |
| `position.x`, `position.y` | Yes | Canvas UI position |
| `configuration` | Yes | Type-specific config |

### Positioning

Downstream nodes go 480px right: `x = upstream.x + 480`. Parallel branches use different `y` values (offset 120).

## Edges

```yaml
edges:
  - sourceId: trigger-id
    targetId: component-id
    channel: default
```

### Output Channels

| Component | Channels |
| --- | --- |
| Filter | `passed`, `failed` |
| If | `True`, `False` |
| Approval | `approved`, `rejected` |
| Everything else | `default` |

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

```yaml
apiVersion: v1
kind: Canvas
metadata:
  name: Health Check
spec:
  edges:
    - sourceId: sched-t1
      targetId: http-a1
      channel: default
  nodes:
    - id: sched-t1
      name: every-minute
      type: TYPE_TRIGGER
      trigger: { name: schedule }
      paused: false
      position: { x: 144, y: 0 }
      configuration: { type: minutes, minutesInterval: 1 }
    - id: http-a1
      name: ping-api
      type: TYPE_COMPONENT
      component: { name: http }
      paused: false
      position: { x: 624, y: 0 }
      configuration: { method: GET, url: "https://api.example.com/health" }
```
