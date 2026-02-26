# Components & Triggers Reference

This file documents **built-in** (non-integration) components and triggers. For integration-backed components (GitHub, Daytona, etc.), see the per-provider reference files.

> **Note:** The CLI commands `superplane index components --name <name>` and `superplane index triggers --name <name>` return name/label/description but **not** config field schemas. Use this reference and the provider reference files for field formats.

## Built-in Triggers

| Trigger | Key | Configuration |
| --- | --- | --- |
| Schedule | `schedule` | `type`: `minutes`/`hours`/`cron`, plus interval or expression |
| Manual Run | `manual_run` | None — triggered from UI |
| Webhook | `webhook` | Optional `secret` for HMAC validation |

Integration triggers (GitHub, AWS, etc.) are discovered via `superplane index triggers --from <integration>`.

## Built-in Components

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

Channels: `default`

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

Channels: `default`

### No Operation (`noop`)

No configuration. Pass-through.

Channels: `default`
