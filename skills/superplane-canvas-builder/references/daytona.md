# Daytona Integration Reference

Components, payload examples, recipes, and gotchas for the Daytona integration in SuperPlane.

Daytona is **action-only** — it has no triggers. It provides isolated sandbox environments for running code and commands.

All payloads are wrapped in the SuperPlane envelope: `{ data: {...}, timestamp, type }`. Expression paths below include the `.data.` prefix.

> **Source of truth:** treat CLI schema and resources as authoritative for your org/runtime:
> - `superplane index components --name <component> --output json`
> - `superplane integrations list-resources --id <integration-id> --type <resource-type>`
> If this reference differs from CLI output, follow CLI output.

## Components

| Component | Description | Output Type | Channels |
| --- | --- | --- | --- |
| `daytona.createSandbox` | Create an isolated sandbox | `daytona.sandbox` | `default` |
| `daytona.deleteSandbox` | Remove a sandbox | `daytona.delete.response` | `default` |
| `daytona.executeCode` | Run code (Python/TypeScript/JavaScript) in a sandbox | `daytona.execute.response` | `default` |
| `daytona.executeCommand` | Run a shell command in a sandbox | `daytona.command.response` | `success`, `failed` |
| `daytona.getPreviewUrl` | Get a preview URL for a sandbox port | `daytona.preview.response` | `default` |

### Component Configuration (YAML keys)

| Component | Required Fields | Optional Fields |
| --- | --- | --- |
| `daytona.createSandbox` | — | `envVars`, `autoStopInterval`, `target`, `snapshot` |
| `daytona.deleteSandbox` | `sandbox` | `force` |
| `daytona.executeCode` | `sandboxId`, `language` (`python`/`typescript`/`javascript`), `code` | `timeout` (ms) |
| `daytona.executeCommand` | `sandboxId`, `command` | `timeout` (s), `envVars`, `workingDirectory` |
| `daytona.getPreviewUrl` | `sandbox` | `port` (default: 3000), `signedUrl` (default: true), `expiresInSeconds` (default: 60, max: 86400) |

> **Watch the key names.** `executeCommand` and `executeCode` use `sandboxId`. `deleteSandbox` and `getPreviewUrl` use `sandbox`. These are different keys for the same concept.

### Using `workingDirectory` and `envVars` on `executeCommand`

**Always prefer `workingDirectory` over inline `cd` commands.** This reduces shell quoting complexity and eliminates a common failure point.

```yaml
- id: run-tests
  name: Run Tests
  type: TYPE_COMPONENT
  component:
    name: daytona.executeCommand
  integration:
    id: <daytona-integration-id>
    name: ""
  configuration:
    sandboxId: "{{ $['Create Sandbox'].data.id }}"
    command: "bash -lc \"set -eu; npm ci && npm test\""
    workingDirectory: "/home/daytona/repo"
    envVars:
      GITHUB_TOKEN: "{{ secret('github-token') }}"
      NODE_ENV: "test"
    timeout: 900
```

Key points:
- `workingDirectory` sets the `cwd` for the command — no need for `cd` in the shell string
- `envVars` injects environment variables into the command — no need for `export` in the shell string
- Both support expressions (`{{ }}`)
- If `workingDirectory` is omitted, the command runs in the sandbox root directory

### Target vs Snapshot

- **`target`** is the compute region/location (e.g., `us-east-1`).
- **`snapshot`** is the base image/template for the sandbox (e.g., `daytona-small`, `daytona-medium`, `daytona-large`).

These are different concepts. If the user says "use daytona-small", that is a `snapshot`, not a `target`.

### Example `createSandbox` configuration

```yaml
configuration:
  snapshot: daytona-small
  # target: us-east-1          # optional: region from list-resources --type target
  # autoStopInterval: 0        # 0 = disable auto-stop; default is 15 minutes
  envVars:
    GITHUB_TOKEN: "{{ secret('github-token') }}"
    OPENAI_API_KEY: "{{ secret('openai-key') }}"
```

Before applying a canvas, verify selected snapshot/target values exist for the connected integration:

```bash
superplane integrations list-resources --id <daytona-integration-id> --type snapshot
superplane integrations list-resources --id <daytona-integration-id> --type target
```

## Shell Execution Model

**`daytona.executeCommand` runs commands under POSIX `sh`, not `bash`.** This is the single most common source of failures.

### What breaks under `sh`

- `set -o pipefail` — invalid option
- `${VAR/find/replace}` — parameter substitution not supported
- Process substitution `<(...)` — not available
- Arrays `arr=(a b c)` — not available
- `[[ ... ]]` double brackets — not available (use `[ ... ]`)

### Mandatory wrapping pattern

**Always wrap multi-step commands in `bash -lc "..."`:**

```yaml
command: >-
  bash -lc "set -eu; echo hello; echo world"
```

For longer scripts, prefer YAML block scalar to reduce folding/escaping risks:

```yaml
command: |-
  bash -lc 'set -eu
  echo hello
  echo world'
```

### Hardened command template

For any non-trivial command, use this pattern to ensure reliable output and debuggability:

```yaml
command: >-
  bash -lc "set -eu; LOG=/tmp/step-name.log; your_command >\"$LOG\" 2>&1 || { code=$?; echo \"STEP_FAILED:$code\"; tail -n 120 \"$LOG\"; exit $code; }; echo \"STEP_OK\""
```

This pattern:
- Redirects verbose output to a log file (avoids output volume issues — see below)
- On failure: prints a marker, the last 120 lines of the log, and exits non-zero
- On success: prints a concise marker (`STEP_OK`)
- Downstream nodes can match on the marker string

### Output volume guardrail

**Large or binary stdout from commands can cause `RESULT_UNKNOWN` state in SuperPlane.** The node output processor has limits on volume and control characters.

Always redirect verbose tool output (npm, codex, test runners, build tools) to a file and print only a concise status marker to stdout. The hardened template above implements this.

### Output cleanliness

Command output is passed **verbatim** to downstream nodes, including trailing newlines. When a downstream node parses the output (e.g., as a number for `issueNumber`), a trailing `\n` will cause parsing failures.

- Use `sys.stdout.write()` instead of `print()` in Python
- Use `printf '%s'` instead of `echo` in shell
- When extracting values for downstream use, always strip whitespace

### Expression quoting in shell commands

The `$['Node Name']` expression syntax conflicts with shell quoting when used inside `bash -lc "..."`. The single quotes around the node name collide with shell string delimiters.

**Prefer `previous().data.field` or `root().data.field`** over `$['Node Name']` inside shell command strings. If you must reference a non-adjacent node, extract the value in a preceding lightweight node and pass it forward.

### JSON construction in shell

Never construct JSON with string concatenation or heredocs inside shell commands — the quoting layers (YAML -> Expr -> bash) make it fragile.

**Use Python for JSON construction:**

```yaml
command: >-
  bash -lc "set -eu; PAYLOAD=$(python3 -c \"import json; print(json.dumps({'title':'My PR','head':'branch','base':'main'}))\"); curl -sS -X POST -H 'Authorization: Bearer $TOKEN' -H 'Content-Type: application/json' 'https://api.github.com/repos/owner/repo/pulls' --data \"$PAYLOAD\""
```

## Typical Flow

```
Trigger → Create Sandbox → Execute Command(s) → Get Preview URL → ... → Delete Sandbox
```

The sandbox `id` from `createSandbox` is required by all subsequent Daytona components. Pass it via expression:

```
{{ $['Create Sandbox'].data.id }}
```

## Custom Snapshots

For workflows that repeatedly install the same tools, create a custom snapshot to eliminate per-run setup time.

### When to use custom snapshots

- The workflow installs global tools (`npm install -g`, `pip install`) in a setup step
- Setup takes >30 seconds
- The same tools are needed across multiple canvases

### Creating a snapshot

Via CLI:
```bash
daytona snapshot create codex-node-agent --image node:20-slim --cpu 2 --memory 4
```

Via declarative builder (Python SDK):
```python
image = (
    Image.base("node:20-slim")
    .run_commands(
        "apt-get update && apt-get install -y git python3 curl",
        "npm install -g @openai/codex"
    )
    .workdir("/home/daytona")
)
daytona.snapshot.create(
    CreateSnapshotParams(name="codex-node-agent", image=image),
    on_logs=print,
)
```

Then reference it in the canvas:
```yaml
configuration:
  snapshot: codex-node-agent
  autoStopInterval: 0
```

## Sandbox Lifecycle

### `autoStopInterval`

Stops the sandbox after N minutes of **inactivity**. Default: 15 minutes.

**What resets the timer:**
- Daytona Toolbox SDK API calls
- Active SSH connections
- Accessing sandbox previews (network requests through preview URLs)

**What does NOT reset the timer:**
- Background processes (`npm start`, long-running scripts)
- Internal process activity without external interaction

Set to `0` to disable auto-stop entirely. **For workflows with long-running steps (LLM inference, large builds), always set `autoStopInterval: 0`** to prevent mid-workflow stops.

### `autoDeleteInterval`

Deletes the sandbox after N minutes of being **continuously stopped**. Default: never.

- `0` = delete immediately when stopped (same as `ephemeral: true`)
- `-1` = disable auto-deletion
- Any positive value = minutes after stop before deletion

### `ephemeral`

Setting `ephemeral: true` on `createSandbox` deletes the sandbox automatically once it stops. Equivalent to `autoDeleteInterval: 0`.

### Recommended configurations

| Use Case | `autoStopInterval` | `autoDeleteInterval` | Notes |
| --- | --- | --- | --- |
| Quick task (<15 min) | default (15) | — | Default works fine |
| Long workflow (>15 min) | `0` | — | Disable auto-stop; delete via canvas node |
| Keep alive then delete | `0` | — | Use `wait` + `deleteSandbox` nodes |
| Fire-and-forget | default | `0` | Auto-stop + immediate delete |

## Git Operations in Sandboxes

### Native Git API (via `executeCode`)

Daytona provides a structured Git API accessible through the Python/TypeScript SDK. When using `daytona.executeCode`, you get:

- `sandbox.git.clone(url, path, branch, username, password)` — handles auth natively
- `sandbox.git.create_branch(path, name)` — no shell needed
- `sandbox.git.push(path, username, password)` — auth handled cleanly
- `sandbox.git.status(path)` — returns structured data: `{ current_branch, ahead, behind, branch_published, file_status }`
- `sandbox.git.add(path, files)`, `sandbox.git.commit(path, message, author, email)`

**Prefer the native Git API over shell git commands** when possible. It avoids URL construction, credential management, and output parsing issues.

### Shell git patterns (via `executeCommand`)

When you must use shell git (e.g., because the workflow needs `executeCommand` for other reasons), use these hardened patterns:

**Clone with token authentication:**
```bash
CLONE_URL="$(printf '%s' "$REPO_URL" | sed "s#https://#https://x-access-token:${GITHUB_TOKEN}@#")"
git clone "$CLONE_URL" "$WORKDIR"
```

**Check for committed changes (not working tree dirtiness):**
```bash
# WRONG: git status --porcelain (checks working tree, empty after commit)
# RIGHT: count commits ahead of main
git fetch origin main
AHEAD="$(git rev-list --count origin/main..HEAD)"
[ "$AHEAD" -gt 0 ] || { echo "NO_COMMITS"; exit 1; }
```

**Push with timeout guard:**
```bash
timeout 60 git push -u origin "$BRANCH" || { echo "GIT_PUSH_TIMEOUT"; exit 1; }
```

## Preview URLs

### Signed vs Unsigned

| Type | Auth Mechanism | Use Case |
| --- | --- | --- |
| Signed (`signedUrl: true`) | Token embedded in URL | Sharing with humans, iframes, emails |
| Unsigned (`signedUrl: false`) | `x-daytona-preview-token` header | Programmatic access, API integrations |

### Configuration

```yaml
configuration:
  sandbox: "{{ $['Create Sandbox'].data.id }}"
  port: 3000
  signedUrl: true
  expiresInSeconds: 86400    # max: 86400 (24 hours)
```

- `expiresInSeconds` max is **86400** (24 hours) for signed URLs
- Signed URL tokens persist across sandbox restarts until expiry
- Tokens can be revoked early via `expireSignedPreviewUrl` SDK method

## Codex CLI in Daytona

Recipe for running OpenAI Codex CLI in non-interactive mode inside a Daytona sandbox.

### Environment variables

Codex CLI requires `CODEX_API_KEY` in non-interactive mode — **not** `OPENAI_API_KEY`. Map it explicitly:

```yaml
envVars:
  CODEX_API_KEY: "{{ secret('openai-key') }}"
```

Or in the command:
```bash
CODEX_API_KEY="${OPENAI_API_KEY:-}" codex exec --full-auto -C "$WORKDIR" "$PROMPT"
```

### Command pattern

```yaml
command: >-
  bash -lc "set -eu; WORKDIR=/home/daytona/repo; PROMPT=\"Implement the changes for issue #123. Requirements: ...\"; LOG=/tmp/codex.log; CODEX_API_KEY=\"${OPENAI_API_KEY:-}\" codex exec --full-auto -C \"$WORKDIR\" \"$PROMPT\" >\"$LOG\" 2>&1 || { code=$?; echo \"CODEX_FAILED:$code\"; tail -n 120 \"$LOG\"; exit $code; }; echo \"CODEX_OK\""
```

### Prompt engineering for sandboxes

Include these constraints in the Codex prompt to prevent common issues:

- **"Do not run npm install, npm i, or npm ci"** — dependencies should be handled by a separate workflow step to avoid hangs
- **"Do not push to remote"** — pushing should be handled by a dedicated workflow step with proper auth
- **"Commit changes with a clear message"** — ensures `git rev-list` detects changes downstream
- **"If verification is needed, only run npm test"** — prevents Codex from running arbitrary build commands

### Flag validation

Do not assume CLI flags from documentation or older examples. Validate at runtime:
```bash
codex exec --help 2>/dev/null | head -20
```

Known invalid flags (as of early 2026):
- `--ask-for-approval` — does not exist on `codex exec`

## Payload Examples

### `daytona.createSandbox`

```
$['Create Sandbox'].data.id              # "sandbox-abc123def456"
$['Create Sandbox'].data.state           # "started"
```

### `daytona.executeCommand`

```
$['Run Install'].data.exitCode           # 0 (success) or non-zero (failure)
$['Run Install'].data.result             # stdout output (verbatim, including newlines)
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

### `sandboxId` vs `sandbox` — different keys for the same thing

`executeCommand` and `executeCode` use the key `sandboxId`. `deleteSandbox` and `getPreviewUrl` use the key `sandbox`. Both refer to the sandbox ID from `createSandbox`, but the YAML key name differs. Getting this wrong produces a "field is required" error.

### `executeCommand` has two output channels, `executeCode` does not

`daytona.executeCommand` routes to `success` (exit code 0) or `failed` (non-zero). Wire edges to the correct channel. `daytona.executeCode` only has `default`.

### Sandbox ID must be passed to every subsequent step

Every Daytona component after `createSandbox` needs the sandbox ID. Use `{{ $['Create Sandbox'].data.id }}` — not `$['Create Sandbox'].id` (missing `.data.`).

### Auto-stop interval

If `autoStopInterval` is set on `createSandbox`, the sandbox will stop after that many minutes of inactivity. For long-running canvases with waits or approvals in between Daytona steps, either set `autoStopInterval: 0` or disable it. Background processes do NOT prevent auto-stop.

## Common Failure Patterns

Use this triage table when debugging `daytona.executeCommand` node failures:

| Symptom | Likely Cause | Fix |
| --- | --- | --- |
| Non-zero exit + empty output | Command ran under `sh`, not `bash` | Wrap in `bash -lc "..."` |
| `RESULT_UNKNOWN` but command completed in sandbox | Output too large or contains control characters | Redirect output to file, print concise marker |
| Command hung indefinitely | Interactive prompt (git credential, npm) or network timeout | Add `timeout` to commands; use `envVars` for credentials; add `--non-interactive` flags |
| `401 Unauthorized` from tool inside sandbox | Wrong env var name for the tool | Check tool docs: Codex uses `CODEX_API_KEY`, not `OPENAI_API_KEY` |
| `strconv.Atoi` or parsing error on downstream node | Trailing newline in command output | Use `sys.stdout.write()` or `printf '%s'` instead of `print`/`echo` |
| `422 Validation Failed` from API call | Malformed JSON payload | Use `python3 -c "import json; ..."` for JSON construction |
| `git status --porcelain` empty after agent commits | Checking working tree, not commit history | Use `git rev-list --count origin/main..HEAD` |
| Expression error referencing `$['Node Name']` in shell | Quoting conflict between Expr and shell | Use `previous().data.field` instead |
