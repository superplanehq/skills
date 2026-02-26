# Daytona Integration Reference

Components, payload examples, and gotchas for the Daytona integration in SuperPlane.

Daytona is **action-only** — it has no triggers. It provides isolated sandbox environments for running code and commands.

All payloads are wrapped in the SuperPlane envelope: `{ data: {...}, timestamp, type }`. Expression paths below include the `.data.` prefix.

## Components

| Component | Description | Output Type | Channels |
| --- | --- | --- | --- |
| `daytona.createSandbox` | Create an isolated sandbox | `daytona.sandbox` | `default` |
| `daytona.deleteSandbox` | Remove a sandbox | `daytona.delete.response` | `default` |
| `daytona.executeCode` | Run code (Python/TypeScript/JavaScript) in a sandbox | `daytona.execute.response` | `default` |
| `daytona.executeCommand` | Run a shell command in a sandbox | `daytona.command.response` | `success`, `failed` |
| `daytona.getPreviewUrl` | Get a preview URL for a sandbox port | `daytona.preview.response` | `default` |

### Component Configuration

| Component | Required Fields | Optional Fields |
| --- | --- | --- |
| `daytona.createSandbox` | — | Environment Variables, Auto Stop Interval, Target, Snapshot |
| `daytona.deleteSandbox` | Sandbox (ID) | Force |
| `daytona.executeCode` | Sandbox ID, Language (`python`/`typescript`/`javascript`), Code | Timeout (ms) |
| `daytona.executeCommand` | Sandbox ID, Command | Timeout (s), Environment Variables, Working Directory |
| `daytona.getPreviewUrl` | Sandbox (ID) | Port (default: 3000), Signed URL (default: true), Expires In Seconds (default: 60, max: 86400) |

## Typical Flow

```
Trigger → Create Sandbox → Execute Command(s) → Get Preview URL → ... → Delete Sandbox
```

The sandbox `id` from `createSandbox` is required by all subsequent Daytona components. Pass it via expression:

```
{{ $['Create Sandbox'].data.id }}
```

## Payload Examples

### `daytona.createSandbox`

```
$['Create Sandbox'].data.id              # "sandbox-abc123def456"
$['Create Sandbox'].data.state           # "started"
```

### `daytona.executeCommand`

```
$['Run Install'].data.exitCode           # 0 (success) or non-zero (failure)
$['Run Install'].data.result             # stdout output
```

### `daytona.executeCode`

```
$['Run Script'].data.exitCode            # 0 (success) or non-zero (failure)
$['Run Script'].data.result              # stdout output
```

### `daytona.getPreviewUrl`

```
$['Get Preview URL'].data.url            # "https://3000-signed-token-abc123.preview.daytona.app"
$['Get Preview URL'].data.port           # 3000
$['Get Preview URL'].data.token          # signed token (if signed=true)
$['Get Preview URL'].data.signed         # true/false
$['Get Preview URL'].data.expiresInSeconds  # 3600
$['Get Preview URL'].data.sandbox        # "sandbox-abc123def456"
```

### `daytona.deleteSandbox`

```
$['Delete Sandbox'].data.id              # "sandbox-abc123def456"
$['Delete Sandbox'].data.deleted         # true
```

## Gotchas

### `executeCommand` has two output channels, `executeCode` does not

`daytona.executeCommand` routes to `success` (exit code 0) or `failed` (non-zero). Wire edges to the correct channel. `daytona.executeCode` only has `default`.

### Sandbox ID must be passed to every subsequent step

Every Daytona component after `createSandbox` needs the sandbox ID. Use `{{ $['Create Sandbox'].data.id }}` — not `$['Create Sandbox'].id` (missing `.data.`).

### Preview URL types

With `signed: true` (default), the URL includes a token and works without extra headers. With `signed: false`, the URL requires an `x-daytona-preview-token` header — if you're posting the URL for a human to click, use signed.

### Auto-stop interval

If `autoStopInterval` is set on `createSandbox`, the sandbox will stop after that many minutes of inactivity. For long-running canvases with waits or approvals in between Daytona steps, either set a high interval or disable it.
