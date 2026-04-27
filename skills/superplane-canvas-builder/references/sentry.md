# Sentry Integration Reference

Triggers, payload examples, and gotchas for the Sentry integration in SuperPlane.

All payloads are wrapped in the SuperPlane envelope: `{ data: {...}, timestamp, type }`. **Sentry's webhook body itself contains a `data` field**, so correct expression paths have **two** `.data.` segments — see the [nested-data gotcha](#gotcha--nested-data-keys-double-data) below.

> **Source of truth:** treat CLI schema as authoritative for your org/runtime:
> - `superplane index triggers --name <trigger> --output json`
> - `superplane index actions --name <action> --output json`
> If this reference differs from CLI output, follow CLI output.

## Triggers

| Trigger | Webhook Resource | Type String | Key Payload Fields |
| --- | --- | --- | --- |
| `sentry.onIssueCreated` | `issue` (action: `created`) | `sentry.issue.created` | `data.data.issue`, `data.data.project`, `data.actor` |
| `sentry.onIssueResolved` | `issue` (action: `resolved`) | `sentry.issue.resolved` | `data.data.issue`, `data.data.project`, `data.actor` |
| `sentry.onIssueAssigned` | `issue` (action: `assigned`) | `sentry.issue.assigned` | `data.data.issue`, `data.data.project`, `data.actor` |
| `sentry.onIssueIgnored` | `issue` (action: `ignored`) | `sentry.issue.ignored` | `data.data.issue`, `data.data.project`, `data.actor` |
| `sentry.onErrorEvent` | `error` (action: `created`) | `sentry.error.created` | `data.data.event`, `data.data.project`, `data.actor` |
| `sentry.onCommentCreated` | `comment` (action: `created`) | `sentry.comment.created` | `data.data.comment`, `data.data.issue`, `data.actor` |

### Trigger Configuration

Sentry triggers require an **Organization** (integration-resource field) and accept optional **Project** filters.

```bash
superplane integrations list-resources --id <sentry-integration-id> --type project
```

## Envelope shape (read this before writing expressions)

A Sentry trigger event arrives wrapped in the SuperPlane envelope. The envelope's `data` field contains the **raw Sentry webhook body**, which itself has its own top-level `data` key holding the resource payload:

```json
{
  "data": {                       // ← envelope.data — root().data
    "action": "created",
    "installation": { "uuid": "..." },
    "data": {                     // ← Sentry's own data field — root().data.data
      "issue": {
        "id": "1234567890",
        "title": "TypeError: Cannot read property 'foo' of undefined",
        "level": "error",
        "status": "unresolved",
        "project": { "slug": "backend", "name": "Backend" },
        "metadata": { "type": "TypeError", "value": "Cannot read property 'foo' of undefined" },
        "permalink": "https://sentry.io/organizations/acme/issues/1234567890/"
      }
    },
    "actor": {
      "id": "user-1",
      "name": "Sentry",
      "type": "application"
    }
  },
  "timestamp": "2026-04-27T12:00:00Z",
  "type": "sentry.issue.created"
}
```

`root()` returns the envelope. `root().data` is the Sentry webhook body. `root().data.data` is Sentry's resource payload. **Do not add a third `.data`** — that path does not exist.

## Payload Examples

### `sentry.onIssueCreated`

```
root().data.action                       # "created"
root().data.installation.uuid            # Sentry integration installation id
root().data.data.issue.id                # "1234567890"
root().data.data.issue.title             # error title (string)
root().data.data.issue.level             # "error", "warning", "info", "fatal"
root().data.data.issue.status            # "unresolved", "resolved", "ignored"
root().data.data.issue.permalink         # full Sentry URL to the issue
root().data.data.issue.project.slug      # "backend"
root().data.data.issue.metadata.type     # "TypeError"
root().data.data.issue.metadata.value    # exception message
root().data.actor.name                   # who/what triggered the event ("Sentry" for system)
```

### `sentry.onIssueResolved`

```
root().data.action                       # "resolved"
root().data.data.issue.id                # issue id
root().data.data.issue.title             # error title
root().data.data.issue.status            # "resolved"
root().data.actor.name                   # who resolved it
root().data.actor.type                   # "user" or "application"
```

### `sentry.onErrorEvent`

```
root().data.data.event.event_id          # specific event id (different from issue id)
root().data.data.event.message           # error message
root().data.data.event.level             # severity
root().data.data.event.platform          # "javascript", "python", etc.
root().data.data.event.environment       # "production", "staging"
root().data.data.event.release           # release tag/version
root().data.data.event.exception.values[0].type   # exception class
root().data.data.event.exception.values[0].value  # exception message
root().data.data.project.slug            # project slug
```

### `sentry.onCommentCreated`

```
root().data.data.comment.id              # comment id
root().data.data.comment.body            # comment text
root().data.data.issue.id                # parent issue id
root().data.data.issue.title             # parent issue title
root().data.actor.name                   # commenter name
```

## Gotchas

### Gotcha — nested `data` keys (double-`.data`)

Sentry's webhook body **carries its own top-level `data` field**. Combined with the SuperPlane envelope, the correct expression for an issue title is:

```
root().data.data.issue.title
```

Two `.data` segments — not one, not three.

- `root().data.issue.title` ← **wrong** (skips Sentry's own `data` field)
- `root().data.data.issue.title` ← **correct**
- `root().data.data.data.issue.title` ← **wrong** (double-counts the envelope)

If a Sentry-driven node's expression resolves to `null`, the count of `.data` segments is the first thing to check. Inspect a real execution with `superplane executions list --canvas-id <id> --node-id <nid> -o yaml` and count the `data` keys from the outermost object — every `data` key in the path is one `.data` segment in the expression, and no more.

### `actor` is at the envelope-`data` level, not under Sentry's `data`

`actor` lives at `root().data.actor` (one `.data`), **not** `root().data.data.actor`. It is a sibling of Sentry's `data` field, not inside it.

### `issue.id` vs `event.event_id`

For `sentry.onIssueCreated` and other issue-level triggers, the identifier is `root().data.data.issue.id`. For `sentry.onErrorEvent`, individual error occurrences have a separate `root().data.data.event.event_id` — these are different ids and link to different Sentry URLs.

### `actor.type` distinguishes humans from automation

`root().data.actor.type` is `"user"` for a human action and `"application"` for events triggered by Sentry itself (e.g., automatic resolution). If your canvas should only react to human resolutions, filter on `actor.type == "user"`.
