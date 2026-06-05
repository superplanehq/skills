# Actions & Triggers Reference

This file documents **built-in** (non-integration) actions and triggers. For integration-backed actions (GitHub, Daytona, etc.), see the per-provider reference files.

> **Note:** Use `superplane index actions --name <name> --output json` and `superplane index triggers --name <name> --output json` to get the richest machine-readable metadata available from the CLI. Use this reference and provider reference files to capture practical field-format gotchas and real-world examples.

## Built-in Triggers

| Trigger | Key | Configuration |
| --- | --- | --- |
| Schedule | `schedule` | `type`: `minutes`/`hours`/`cron`, plus interval or expression |
| Manual Run | `start` | `templates` (required): at least one `{name, payload}`; optional `parameters` |
| Webhook | `webhook` | Optional `secret` for HMAC validation |

Integration triggers (GitHub, AWS, etc.) are discovered via `superplane index triggers --from <integration>`.

### Manual Run (`start`)

Never use `configuration: {}`. The UI Run button and the `run` hook both require at least one template.

```yaml
- id: trigger-manual
  name: Manual Run
  type: TYPE_TRIGGER
  component: start
  configuration:
    templates:
      - name: default
        payload:
          message: "Hello, World!"
        parameters: []
  position:
    x: 120
    y: 100
  paused: false
  isCollapsed: false
```

Each template needs:

| Field | Required | Description |
| --- | --- | --- |
| `name` | Yes | Template label used by the Run button and `run` hook |
| `payload` | Yes | JSON object emitted on run (supports expressions) |
| `parameters` | No | Run-form fields referenced in payload as `{{ parameters["name"] }}` |

Parameterized example:

```yaml
configuration:
  templates:
    - name: greet
      payload:
        message: '{{ parameters["name"] }}'
      parameters:
        - name: name
          type: string
          defaultString: "World"
```

Channels: `default` (emits `manual.run` events)

## Built-in Actions

### HTTP Request (`http`)

| Field | Required | Description |
| --- | --- | --- |
| `method` | Yes | `GET`, `POST`, `PUT`, `PATCH`, `DELETE` |
| `url` | Yes | Target URL (supports expressions) |
| `headers` | No | List of `{ name, value }` objects (supports expressions in values) |
| `body` | No | Request body (supports expressions) |

Example `headers` configuration:

```yaml
headers:
  - name: Authorization
    value: "Bearer {{ $['Get Token'].data.token }}"
  - name: Content-Type
    value: application/json
```

Channels: `success`, `failure`

### Filter (`filter`)

| Field | Required | Description |
| --- | --- | --- |
| `expression` | Yes | Boolean Expr expression |

Channels: `default` (emits only when expression is true; when false, the event stops — nothing is emitted)

### If (`if`)

| Field | Required | Description |
| --- | --- | --- |
| `expression` | Yes | Boolean Expr expression |

Channels: `true`, `false`

### Approval (`approval`)

| Field | Required | Description |
| --- | --- | --- |
| `approvers` | No | User/group IDs |
| `minApprovals` | No | Minimum required (default: 1) |

Channels: `approved`, `rejected`

### Merge (`merge`)

No configuration. Waits for all incoming edges before continuing.

Channels: `success`, `timeout`, `fail`

### Wait (`wait`)

| Field | Required | Description |
| --- | --- | --- |
| `type` | Yes | `duration` or `timestamp` |
| `duration` | Conditional | e.g. `5m`, `1h` |
| `timestamp` | Conditional | ISO 8601 (supports expressions) |

Channels: `default`

### Time Gate (`timegate`)

| Field | Required | Description |
| --- | --- | --- |
| `timezone` | Yes | IANA timezone |
| `allowedDays` | Yes | `[monday, tuesday, ...]` |
| `startHour` | Yes | 0-23 |
| `endHour` | Yes | 0-23 |

Channels: `default`

### SSH Command (`ssh`)

| Field | Required | Description |
| --- | --- | --- |
| `host` | Yes | Hostname or IP |
| `user` | Yes | SSH username |
| `command` | Yes | Command (supports expressions) |
| `privateKey` | No | Reference a secret |

Channels: `success`, `failed`

### No Operation (`noop`)

No configuration. Pass-through.

Channels: `default`

### Read Memory (`readMemory`)

| Field | Required | Description |
| --- | --- | --- |
| `namespace` | Yes | Memory namespace |
| `matchList` | Yes | List of `{ name, value }` to match |
| `resultMode` | No | `latest` (default) or `all` |

Channels: `found`, `notFound`

### Upsert Memory (`upsertMemory`)

| Field | Required | Description |
| --- | --- | --- |
| `namespace` | Yes | Memory namespace |
| `matchList` | Yes | List of `{ name, value }` to match |
| `valueList` | Yes | List of `{ name, value }` to store |

Channels: `default`

### Delete Memory (`deleteMemory`)

| Field | Required | Description |
| --- | --- | --- |
| `namespace` | Yes | Memory namespace |
| `matchList` | Yes | List of `{ name, value }` to match |

Channels: `deleted`, `notFound`
