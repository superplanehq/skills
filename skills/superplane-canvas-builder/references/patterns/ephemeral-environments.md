# Pattern: Ephemeral Environments

Provision short-lived environments on demand, track their state, and clean them up automatically.

## When to Use

The user wants preview/staging environments that:
- Spin up on demand (or automatically)
- Are tracked so they can be individually destroyed
- Clean themselves up after a TTL or when the triggering event closes
- Post status back to the user

## How to Build It

### Step 1: Discover What's Connected

Don't ask the user what integrations they have. Run:

```bash
superplane integrations list
```

From the output, identify:
- **Source control provider** (GitHub, GitLab, Bitbucket, etc.) — for triggers and notifications
- **Infrastructure provider** (DigitalOcean, Daytona, AWS, etc.) — for provisioning and teardown

Then discover available triggers and components:

```bash
superplane index triggers --from <scm-provider>
superplane index components --from <scm-provider>
superplane index components --from <infra-provider>
```

Look for:
- **Trigger pair:** an "on PR" or "on MR" trigger + a "comment" trigger (for commands)
- **Infra pair:** a "create" component + a matching "delete/destroy" component
- **Notification component:** "create comment", "post message", or similar

If there's no native component for a step, use the `http` component as a fallback.

### Step 2: Decide Trigger Strategy

Now that you know what's available, present the options to the user. The lifecycle (Step 3) stays the same regardless — only the trigger changes.

**Command-based (recommended default):** User comments `/deploy` or `/destroy` on a PR/issue. Opt-in, saves resources.

**Auto on open:** Every PR/MR automatically gets an environment. Zero friction but resource-heavy.

**Hybrid:** Auto-deploy on open + manual `/destroy` command + TTL safety net.

The user might also want chat-triggered (Slack/Discord), API/webhook-triggered, or scheduled environments. Adapt to what makes sense for their workflow.

### Step 3: Build the Lifecycle

This is the skeleton — the same for every implementation. Substitute the concrete components discovered in Step 1.

**Path 1: Provision**
```
[Request Trigger]
  → [Ack] (optional — react to the command)
  → [Check Duplicate] (readMemory → found = already running, stop)
  → [Notify: Provisioning]
  → [Provision Infra]
  → [Save State to Memory] (environments + env-internal namespaces)
  → [Wait + Health Check]
  → [Read Metadata] → found → [Notify: Ready] + [Set Status]
                     → notFound → [Notify: Ready] (skip status)
```

**Path 2: Destroy (manual command)**
```
[Destroy Trigger]
  → [Ack]
  → [Read State] (readMemory → notFound = no env, notify and stop)
  → [Tear Down Infra]
  → [Cleanup Memory: ALL namespaces]
  → [Notify: Destroyed]
```

**Path 3: Auto-destroy (source event closed)**
```
[Close Trigger]
  → [Read State] → found → [Tear Down] → [Cleanup ALL] → [Notify]
                  → notFound → (silent, nothing to clean)
```

**Path 4: TTL reaper**
```
[Schedule Trigger]
  → [Read All Envs] (emitMode: oneByOne)
  → [Check Age > TTL]
  → true → [Tear Down] → [Cleanup ALL]
```

**Path 5: Welcome (optional)**
```
[Open Trigger] → [Save Metadata] → [Notify: Instructions]
```

### Step 4: Configure Memory

Use 3 namespaces with a shared identifier field (e.g., `pr_number`, `issue_id`, `request_id`):

| Namespace | Purpose | Example Fields |
|---|---|---|
| `environments` | User-facing state | identifier, title, url, requested_by |
| `env-internal` | Infra plumbing | identifier, infra_id, created_at |
| `env-metadata` | Source control data (optional) | identifier, commit_sha |

**Storage tips:**
- `created_at`: store as `{{ string(int(now().Unix())) }}`, read back with `int(float(value))`
- Large IDs (infra IDs, etc.): store as `string(int(id))`, read back with `int(float(id))` to avoid scientific notation

### Step 5: Verify

Before calling it done:
- Every destroy path (manual, auto-close, TTL) cleans ALL memory namespaces
- `readMemory` edges handle both `found` and `notFound` channels
- `deleteMemory` edges use the `deleted` channel, not `default`
- Health check runs before the "ready" notification
- No `errorMessage` on any node
- Test one full deploy + destroy cycle

## Critical Rules

These are real bugs found in production. Don't skip them.

1. **Every destroy path cleans ALL namespaces.** If TTL only cleans `env-internal` but not `environments`, you get ghost entries — memory says an environment exists but the infra is gone.

2. **Wire `notFound` fallbacks on memory reads.** If `readMemory` returns `notFound` and there's no edge for that channel, the chain dies silently. The user never gets the URL even though provisioning succeeded.

3. **Duplicate detection before provisioning.** Check `environments` memory first. If an entry already exists, notify the user and stop — don't create a second instance.

4. **Health check before notifying.** Don't post the URL until the environment is actually responding.

5. **`readMemory` emits on `found`/`notFound`**, not `default`. Wire edges accordingly.

6. **`deleteMemory` emits on `deleted`**, not `default`. Wire edges accordingly.

7. **TTL `readMemory` must use `emitMode: oneByOne`** so each environment is processed individually through the age check.

8. **Schedule trigger limits:** `minutesInterval` max is 59. For daily checks, use `type: days` with `daysInterval` (requires `timezone` field).
