# Pattern: Ephemeral Environments

Provision short-lived environments on demand, track their state, and clean them up automatically.

This is a **reference architecture**, not a template. Adapt triggers, infra, and notification components to whatever integrations the user has connected.

## When to Use

The user wants preview/staging environments that:
- Spin up on demand (or automatically per PR, issue, chat command, etc.)
- Are tracked so they can be individually destroyed
- Clean themselves up after a TTL or when the triggering event closes
- Post status back to the user (comment, message, commit status)

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    EPHEMERAL ENVIRONMENTS                        │
│                                                                  │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────────┐ │
│  │ TRIGGERS │──▶│LIFECYCLE │──▶│  MEMORY  │──▶│ NOTIFICATION │ │
│  │ (Layer 2)│   │(Layer 1) │   │ (Layer 1)│   │  (Layer 3)   │ │
│  └──────────┘   └──────────┘   └──────────┘   └──────────────┘ │
│                                                                  │
│  Layer 1: Fixed skeleton (same for everyone)                     │
│  Layer 2: Trigger strategy (user's choice)                       │
│  Layer 3: Infra + notifications (user's integrations)            │
└─────────────────────────────────────────────────────────────────┘
```

## Layer 1: Lifecycle Core (Always the Same)

These are the 5 workflow paths every ephemeral environment system needs. The skeleton is identical regardless of trigger source or infra provider.

### Path 1: Environment Requested
```
[Trigger] → [Ack/React] → [Check Duplicate] →found→ [Already Exists notice]
                                              →notFound→ [Status: Provisioning]
                                                → [Provision Infra]
                                                → [Save State to Memory] (2 namespaces)
                                                → [Wait for Boot]
                                                → [Health Check]
                                                → [Read Metadata] →found→ [Notify: Ready] + [Set Status]
                                                                  →notFound→ [Notify: Ready] (skip status)
```

### Path 2: Environment Requested to Destroy
```
[Trigger] → [Ack/React] → [Read State from Memory]
              →found→ [Tear Down Infra] → [Cleanup Memory: ALL namespaces] → [Notify: Destroyed]
              →notFound→ [Notify: No Environment Found]
```

### Path 3: Source Event Closed (auto-destroy)
```
[Close Trigger] → [Read State from Memory]
                    →found→ [Tear Down Infra] → [Cleanup Memory: ALL namespaces] → [Notify: Auto-Destroyed]
                    →notFound→ (silent, nothing to clean)
```

### Path 4: TTL Reaper (scheduled)
```
[Schedule Trigger] → [Read All Envs (emit one-by-one)]
                       →found→ [Check Age > TTL] →true→ [Tear Down] → [Cleanup Memory: ALL namespaces]
                       →notFound→ (nothing to reap)
```

### Path 5: Source Event Opened (optional welcome/metadata)
```
[Open Trigger] → [Save Metadata to Memory] → [Notify: Welcome/Instructions]
```

### Memory Design (3 Namespaces)

This is critical. Every destroy path (manual, auto-close, TTL) MUST clean ALL 3 namespaces. Partial cleanup causes ghost entries and orphan state.

| Namespace | Purpose | Fields | Who reads it |
|---|---|---|---|
| `environments` | User-facing state | identifier, title, url, source_url, requested_by | Duplicate check, user dashboards |
| `env-internal` | Infrastructure plumbing | identifier, infra_id, created_at, source | Destroy paths (need infra ID), TTL reaper (need created_at) |
| `env-metadata` | Source control metadata | identifier, commit_sha (or equivalent) | Status/check reporters (optional) |

**Key field:** Every namespace uses a shared identifier field (e.g., `pr_number`, `issue_id`, `request_id`) to correlate entries across namespaces.

**`created_at` format:** Store as Unix timestamp string: `{{ string(int(now().Unix())) }}`. Read back with `int(float(value))` to handle string→number conversion.

**Large IDs:** Infrastructure IDs can be large integers. Always store with `string(int(id))` and read back with `int(float(id))` to avoid scientific notation rendering (e.g., `5.66e+08`).

### Critical Rules

1. **Every destroy path cleans ALL 3 namespaces.** This is the #1 source of bugs. If TTL only cleans `env-internal` but not `environments`, you get ghost entries. If destroy doesn't clean `env-metadata`, you get orphan SHAs.

2. **Wire `notFound` fallbacks.** When reading memory (e.g., to get a commit SHA), the `notFound` channel must still route to notification. Otherwise the chain dies silently — infra is provisioned but the user never gets the URL.

3. **Duplicate detection before provisioning.** Check `environments` memory for an existing entry. If found, notify the user and stop. Don't create a second instance.

4. **Health check before notifying.** Don't post the URL until the environment is actually responding. Use a wait + SSH/HTTP check, or poll a readiness endpoint.

5. **`readMemory` outputs on `found`/`notFound` channels**, not `default`. Wire edges accordingly.

6. **`deleteMemory` outputs on `deleted` channel**, not `default`. Wire edges accordingly.

7. **TTL `readMemory` must use `emitMode: oneByOne`** so each environment is processed individually through the age check and destroy path.

## Layer 2: Trigger Strategy

Ask the user: **"How should environments be triggered?"**

Then configure the appropriate trigger. The lifecycle core (Layer 1) stays the same — only the trigger node and its payload expressions change.

### Option A: Command-Based (PR/Issue Comment)
**Trigger:** `{scm}.onPRComment` or `{scm}.onIssueComment` with content filter
**Deploy:** User comments `/deploy` → provisions environment
**Destroy:** User comments `/destroy` → tears down environment
**Auto-close:** `{scm}.onPullRequest(closed)` or `{scm}.onIssue(closed)`

Expressions use: `root().data.issue.number`, `root().data.comment.user.login`

**Pros:** Opt-in, saves resources. User controls when to spin up.
**Cons:** Requires user action per PR.

### Option B: Auto on PR/MR Open
**Trigger:** `{scm}.onPullRequest(opened, reopened)` or equivalent
**Deploy:** Automatic on every PR open
**Destroy:** Auto on PR close, or TTL
**No manual deploy command needed.**

Expressions use: `root().data.pull_request.number`, `root().data.pull_request.head.sha`

**Pros:** Zero friction, every PR gets a preview.
**Cons:** Resource-heavy if many PRs are opened. Consider adding label filters.

### Option C: Chat-Triggered (Discord, Slack, etc.)
**Trigger:** Chat integration trigger (message match, mention, slash command)
**Deploy:** User says "deploy PR 42" or "/preview 42"
**Destroy:** User says "destroy PR 42" or "/teardown 42"

Expressions need to parse the identifier from the message body.

**Pros:** Non-developers can trigger environments.
**Cons:** Requires parsing, less structured than SCM events.

### Option D: Manual / API
**Trigger:** `manual_run` or generic `webhook`
**Deploy:** Triggered via API call or SuperPlane UI
**Destroy:** Same, or TTL

**Pros:** Maximum flexibility, works with any external system.
**Cons:** No built-in context — user must provide all parameters.

### Option E: Hybrid
Combine triggers on a single canvas. For example:
- Auto-deploy on PR open (Option B)
- `/destroy` command for manual teardown (Option A)
- TTL reaper as safety net (always included)

Multiple triggers can coexist on one canvas — each starts its own workflow path.

## Layer 3: Integration Substitution

Ask the user: **"What integrations do you have connected?"**

Run `superplane integrations list` to discover what's available, then map abstract steps to concrete components.

### Infrastructure (Provision / Tear Down)

| Provider | Provision | Tear Down | Notes |
|---|---|---|---|
| DigitalOcean | `digitalocean.createDroplet` | `digitalocean.deleteDroplet` | Use cloud-init for setup. Delete needs numeric ID. |
| AWS | `http` (EC2 RunInstances API) | `http` (EC2 TerminateInstances) | Or use SSH to run Terraform/CDK |
| Daytona | `daytona.createSandbox` | `daytona.deleteSandbox` | Native sandbox lifecycle |
| Kubernetes | `ssh` (kubectl apply) | `ssh` (kubectl delete) | Create/delete namespace or deployment |
| Docker | `ssh` (docker run) | `ssh` (docker rm -f) | On a shared host |

### Source Control (Triggers + Notifications)

| Provider | PR Trigger | Comment Trigger | Post Comment | Commit Status |
|---|---|---|---|---|
| GitHub | `github.onPullRequest` | `github.onPRComment` | `github.createIssueComment` | `github.publishCommitStatus` |
| GitLab | `gitlab.onMergeRequest` | Check available triggers | Use `http` component | Use `http` component |
| Bitbucket | Check available triggers | Check available triggers | Use `http` component | Use `http` component |

### Notifications (Non-SCM)

| Channel | Component | Notes |
|---|---|---|
| Slack | `slack.postMessage` | Post URL to a channel |
| Discord | `http` (Discord webhook) | Or native component if available |
| Email | `http` (email API) | SendGrid, SES, etc. |

**Always verify** exact component names with `superplane index actions --from <provider>` — don't assume from this table.

## Assembly Checklist

When building an ephemeral environments canvas:

1. **Discover integrations:** `superplane integrations list`
2. **Pick trigger strategy** (Layer 2) based on user preference
3. **Map infra components** (Layer 3) based on connected integrations
4. **Map notification components** (Layer 3) based on where user wants updates
5. **Build the 5 paths** from Layer 1, substituting concrete components
6. **Configure 3 memory namespaces** with a shared identifier field
7. **Wire ALL destroy paths** to clean ALL 3 namespaces
8. **Wire `notFound` fallbacks** on memory reads
9. **Set TTL schedule** — ask user for duration (default: 72h, check every 24h)
10. **Verify:** no `errorMessage` on any node, test one deploy+destroy cycle

## Lessons Learned (From Production Use)

These are real bugs encountered while building and operating this pattern:

- **Ghost entries:** TTL reaper deleted infra but only cleaned 1 of 3 memory namespaces. User-facing memory showed environments that no longer existed.
- **Silent chain death:** `readMemory` returned `notFound` (missing metadata), no edge wired for that channel, so the deploy succeeded but the user never got the URL.
- **Scientific notation:** Large infrastructure IDs (e.g., DO droplet IDs) rendered as `5.66e+08` in expressions. Fix: `string(int(id))` to store, `int(float(id))` to read back.
- **Output channel mismatch:** Many components emit on named channels (`success`/`failure`, `found`/`notFound`, `deleted`) not `default`. Wiring to `default` = silent failure.
- **Schedule trigger `minutesInterval` max is 59.** For daily checks, use `type: days` with `daysInterval: 1` (requires `timezone` field).
