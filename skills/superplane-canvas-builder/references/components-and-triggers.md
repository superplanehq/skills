# Components & Triggers Reference

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
| `headers` | No | Key-value pairs |
| `body` | No | Request body (supports expressions) |

Channels: `default`

### Filter (`filter`)

| Field | Required | Description |
| --- | --- | --- |
| `expression` | Yes | Boolean Expr expression |

Channels: `passed`, `failed`

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

Channels: `default`

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
