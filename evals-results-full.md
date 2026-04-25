# 🧪 Skills Evals — Run Report

- **Model:** `claude-haiku-4-5`
- **Run:** `20260425T041142_622967Z`

## Cases

### `whoami_basic` — ✅ Pass  ·  9.7s  ·  $0.0146

- **Skill:** `superplane-cli`
- **Input:** Check which SuperPlane org I'm currently connected to, then tell me the result.
- **Output:** `/app/evals/reports/20260425T041142_622967Z/whoami_basic.json`
- **Log:** `/app/tmp/evals/622967Z-01-whoami_basic.log`

| toolCalls | inputTokens | outputTokens | cacheRead | cacheWrite | cost |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 2 | 28 | 538 | 73075 | 3339 | $0.0146 |

**Assertions (1/1):**

- ✅ BashCommandCalled: passed - pattern 'superplane\\s+whoami' matched 1 bash call(s) (min 1)

---

### `list_components_github` — ✅ Pass  ·  14.5s  ·  $0.0216

- **Skill:** `superplane-cli`
- **Input:** List the SuperPlane components available for the GitHub integration. Run the CLI, then summarize what you find.
- **Output:** `/app/evals/reports/20260425T041142_622967Z/list_components_github.json`
- **Log:** `/app/tmp/evals/622967Z-02-list_components_github.log`

| toolCalls | inputTokens | outputTokens | cacheRead | cacheWrite | cost |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 3 | 36 | 909 | 98041 | 5397 | $0.0216 |

**Assertions (1/1):**

- ✅ BashCommandCalled: passed - pattern 'superplane\\s+index\\s+components\\s+--from\\s+github' matched 1 bash call(s) (min 1)

---

### `missing_cli_refusal` — ✅ Pass  ·  12.6s  ·  $0.0201

- **Skill:** `superplane-cli`
- **Input:** Create a new SuperPlane canvas named foo.
- **Output:** `/app/evals/reports/20260425T041142_622967Z/missing_cli_refusal.json`
- **Log:** `/app/tmp/evals/622967Z-03-missing_cli_refusal.log`

| toolCalls | inputTokens | outputTokens | cacheRead | cacheWrite | cost |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 3 | 28 | 889 | 72620 | 6366 | $0.0201 |

**Assertions (2/2):**

- ✅ RefusedBecauseMissingCli: passed - agent refused and referenced installing the SuperPlane CLI
- ✅ BashCommandNotCalled: passed - pattern 'superplane\\s+canvases\\s+create' never matched

---

### `connect_flow` — ❌ Fail  ·  22.5s  ·  $0.0229

- **Skill:** `superplane-cli`
- **Input:** Connect me to the SuperPlane instance at https://sp.example.com with token abc123.
- **Output:** `/app/evals/reports/20260425T041142_622967Z/connect_flow.json`
- **Log:** `/app/tmp/evals/622967Z-04-connect_flow.log`

| toolCalls | inputTokens | outputTokens | cacheRead | cacheWrite | cost |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 3 | 36 | 1147 | 98428 | 5464 | $0.0229 |

**Assertions (0/1):**

- ❌ BashCommandsInOrder: failed - Matched 1/2 patterns in order; missing (in order): ['superplane\\s+whoami']. Observed bash calls: ['command -v superplane', 'superplane connect https://sp.example.com abc123']

---

### `describe_trigger` — ✅ Pass  ·  15.8s  ·  $0.0289

- **Skill:** `superplane-cli`
- **Input:** Inspect the github.onPush trigger schema via the CLI and report its configuration fields and payload shape.
- **Output:** `/app/evals/reports/20260425T041142_622967Z/describe_trigger.json`
- **Log:** `/app/tmp/evals/622967Z-05-describe_trigger.log`

| toolCalls | inputTokens | outputTokens | cacheRead | cacheWrite | cost |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 4 | 36 | 1381 | 98382 | 9348 | $0.0289 |

**Assertions (1/1):**

- ✅ BashCommandCalled: passed - pattern 'superplane\\s+index\\s+triggers\\s+--name\\s+github\\.onPush' matched 1 bash call(s) (min 1)

---

### `push_to_slack` — ✅ Pass  ·  35.5s  ·  $0.0560

- **Skill:** `superplane-canvas-builder`
- **Input:** Build a canvas that posts a Slack message to the '#deploys' channel on every push to the main branch of the superplanehq/app GitHub repository. Generate the full YAML and write it to canvas.yaml — the backend may not have these integrations connected yet, so just produce a correct YAML that could be applied later.
- **Output:** `/app/evals/reports/20260425T041142_622967Z/push_to_slack.json`
- **Log:** `/app/tmp/evals/622967Z-06-push_to_slack.log`

| toolCalls | inputTokens | outputTokens | cacheRead | cacheWrite | cost |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 11 | 68 | 3001 | 233300 | 13642 | $0.0560 |

**Assertions (5/5):**

- ✅ BashCommandsInOrder: passed - All 2 pattern(s) matched in order at indices [1, 3]
- ✅ FileWritten: passed - file(s) matching '.*\\.ya?ml$': ['/tmp/canvas.yaml']
- ✅ YamlValidatesCanvas: passed - YAML parses as a Canvas resource
- ✅ CanvasHasTrigger: passed - trigger 'github.onPush' found in canvas
- ✅ CanvasHasNode: passed - node 'slack.sendTextMessage' found 1 time(s) as expected

---

### `missing_integration_refusal` — ✅ Pass  ·  16.0s  ·  $0.0286

- **Skill:** `superplane-canvas-builder`
- **Input:** Create a canvas that uses Daytona to spin up an ephemeral sandbox on every PR open.
- **Output:** `/app/evals/reports/20260425T041142_622967Z/missing_integration_refusal.json`
- **Log:** `/app/tmp/evals/622967Z-07-missing_integration_refusal.log`

| toolCalls | inputTokens | outputTokens | cacheRead | cacheWrite | cost |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 4 | 44 | 1272 | 129313 | 7031 | $0.0286 |

**Assertions (3/3):**

- ✅ BashCommandCalled: passed - pattern 'superplane\\s+integrations\\s+list' matched 1 bash call(s) (min 1)
- ✅ ResponseMentions: passed - response mentions 'daytona'
- ✅ FileNotWritten: passed - no file matched '.*canvas.*\\.ya?ml$'

---

### `starter_from_template` — ❌ Fail  ·  84.3s  ·  $0.1526

- **Skill:** `superplane-canvas-builder`
- **Input:** Scaffold a health check monitor canvas to get me started.
- **Output:** `/app/evals/reports/20260425T041142_622967Z/starter_from_template.json`
- **Log:** `/app/tmp/evals/622967Z-08-starter_from_template.log`

| toolCalls | inputTokens | outputTokens | cacheRead | cacheWrite | cost |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 20 | 164 | 8889 | 716833 | 28723 | $0.1526 |

**Assertions (0/1):**

- ❌ BashCommandCalled: failed - pattern 'superplane\\s+canvases\\s+init\\s+--template\\s+health-check-monitor' matched 0 bash call(s); expected at least 1. Observed: ['command -v superplane && superplane whoami', 'superplane integrations list', 'superplane index triggers', 'superplane index components | head -50', 'superplane index triggers --name schedule --output json', 'superplane index components --name http --output json', 'superplane index components --name if --output json && superplane index components --name sendEmail --output json', 'superplane canvases create --file health-check-monitor.yaml', 'superplane canvases init --output-file /tmp/canvas-template.yaml && cat /tmp/canvas-template.yaml', 'ls -la /tmp/skills-eval-wiq0iao8/.claude/skills/superplane-canvas-builder/references/ 2>/dev/null | head -20']

---

### `draft_update_flag` — ❌ Fail  ·  18.1s  ·  $0.0296

- **Skill:** `superplane-canvas-builder`
- **Input:** Update canvas my-canvas to add a manual approval step before deploy.
- **Output:** `/app/evals/reports/20260425T041142_622967Z/draft_update_flag.json`
- **Log:** `/app/tmp/evals/622967Z-09-draft_update_flag.log`

| toolCalls | inputTokens | outputTokens | cacheRead | cacheWrite | cost |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 5 | 52 | 1233 | 152558 | 6197 | $0.0296 |

**Assertions (0/1):**

- ❌ BashCommandCalled: failed - pattern 'superplane\\s+canvases\\s+update\\s+[^\\s]+\\s+--draft' matched 0 bash call(s); expected at least 1. Observed: ['command -v superplane', 'superplane whoami', 'superplane canvases get my-canvas', 'superplane canvases list']

---

### `resource_verification` — ❌ Fail  ·  42.5s  ·  $0.0721

- **Skill:** `superplane-canvas-builder`
- **Input:** Build a canvas YAML that runs a Semaphore workflow on the superplanehq/app repo every time code is pushed to main. Discover required resources via the CLI even if nothing is connected yet, and write canvas.yaml.
- **Output:** `/app/evals/reports/20260425T041142_622967Z/resource_verification.json`
- **Log:** `/app/tmp/evals/622967Z-10-resource_verification.log`

| toolCalls | inputTokens | outputTokens | cacheRead | cacheWrite | cost |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 11 | 92 | 3748 | 324672 | 16277 | $0.0721 |

**Assertions (0/1):**

- ❌ BashCommandsInOrder: failed - Matched 1/2 patterns in order; missing (in order): ['superplane\\s+integrations\\s+list-resources']. Observed bash calls: ['command -v superplane', 'superplane whoami', 'superplane integrations list', 'superplane index triggers --from github 2>&1', 'superplane index components --from semaphore 2>&1', 'superplane index triggers --name github.onPush --output json', 'superplane index components --name semaphore.runWorkflow --output json', 'cat > /tmp/canvas.yaml << \'EOF\'\napiVersion: canvases.superplane.com/v1\nkind: Canvas\nmetadata:\n  name: github-to-semaphore-workflow\n  description: Trigger Semaphore workflow on push to main branch of superplanehq/app\nspec:\n  nodes:\n    - id: github-push-trigger\n      type: trigger\n      trigger:\n        name: github.onPush\n        configuration:\n          repository: superplanehq/app\n          refs:\n            - type: equals\n              value: refs/heads/main\n          customName: "Semaphore: {{ $.data.repository.name }} @ {{ $.data.head_commit.id }}"\n      position:\n        x: 120\n        y: 100\n\n    - id: semaphore-run-workflow\n      type: component\n      component:\n        name: semaphore.runWorkflow\n        configuration:\n          project: ""\n          pipelineFile: .semaphore/semaphore.yml\n          ref: "{{ $[\'github-push-trigger\'].data.ref }}"\n          commitSha: "{{ $[\'github-push-trigger\'].data.head_commit.id }}"\n      position:\n        x: 720\n        y: 100\n\n  edges:\n    - sourceId: github-push-trigger\n      targetId: semaphore-run-workflow\n      channel: default\nEOF\n', 'cat /tmp/canvas.yaml']

---

### `why_did_my_run_fail` — ❌ Fail  ·  16.3s  ·  $0.0269

- **Skill:** `superplane-monitor`
- **Input:** A canvas called 'my-canvas' had a failed run. Use the CLI to trace what happened: find the canvas, list recent events, then show the executions for the most recent event.
- **Output:** `/app/evals/reports/20260425T041142_622967Z/why_did_my_run_fail.json`
- **Log:** `/app/tmp/evals/622967Z-11-why_did_my_run_fail.log`

| toolCalls | inputTokens | outputTokens | cacheRead | cacheWrite | cost |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 4 | 44 | 1297 | 125068 | 5926 | $0.0269 |

**Assertions (0/1):**

- ❌ BashCommandsInOrder: failed - Matched 0/2 patterns in order; missing (in order): ['superplane\\s+events\\s+list', 'superplane\\s+events\\s+list-executions']. Observed bash calls: ['command -v superplane && superplane whoami', 'superplane canvases list', 'superplane contexts']

---

### `stuck_execution` — ❌ Fail  ·  19.2s  ·  $0.0304

- **Skill:** `superplane-monitor`
- **Input:** An execution on node deploy-prod in canvas cvs-abc has been running for over an hour. Use the CLI to find its execution history and diagnose.
- **Output:** `/app/evals/reports/20260425T041142_622967Z/stuck_execution.json`
- **Log:** `/app/tmp/evals/622967Z-12-stuck_execution.log`

| toolCalls | inputTokens | outputTokens | cacheRead | cacheWrite | cost |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 7 | 52 | 1607 | 146252 | 5755 | $0.0304 |

**Assertions (0/1):**

- ❌ BashCommandCalled: failed - pattern 'superplane\\s+executions\\s+list\\s+.*--node-id\\s+deploy-prod' matched 0 bash call(s); expected at least 1. Observed: ['command -v superplane && echo "✓ CLI found" || echo "✗ CLI not found"', 'superplane whoami', 'superplane events list --canvas-id cvs-abc', 'superplane canvases list', 'superplane org list', 'cat ~/.superplane.yaml 2>/dev/null || echo "No config file found"']

---

### `cancel_flow` — ✅ Pass  ·  18.8s  ·  $0.0373

- **Skill:** `superplane-monitor`
- **Input:** Cancel execution exec-123 on canvas cvs-9 using the CLI.
- **Output:** `/app/evals/reports/20260425T041142_622967Z/cancel_flow.json`
- **Log:** `/app/tmp/evals/622967Z-13-cancel_flow.log`

| toolCalls | inputTokens | outputTokens | cacheRead | cacheWrite | cost |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 7 | 68 | 1580 | 208526 | 6455 | $0.0373 |

**Assertions (1/1):**

- ✅ BashCommandCalled: passed - pattern 'superplane\\s+executions\\s+cancel\\s+.*--execution-id\\s+exec-123' matched 1 bash call(s) (min 1)

---

### `queue_inspect` — ❌ Fail  ·  17.6s  ·  $0.0307

- **Skill:** `superplane-monitor`
- **Input:** Items are piling up on the 'build' node queue on canvas cvs-abc. Inspect the queue via the CLI and tell me what's there.
- **Output:** `/app/evals/reports/20260425T041142_622967Z/queue_inspect.json`
- **Log:** `/app/tmp/evals/622967Z-14-queue_inspect.log`

| toolCalls | inputTokens | outputTokens | cacheRead | cacheWrite | cost |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 5 | 52 | 1372 | 152203 | 6505 | $0.0307 |

**Assertions (0/1):**

- ❌ BashCommandCalled: failed - pattern 'superplane\\s+queue\\s+list' matched 0 bash call(s); expected at least 1. Observed: ['command -v superplane', 'superplane whoami', 'superplane canvases get cvs-abc', 'superplane canvases list']

---

### `payload_envelope_explain` — ❌ Fail  ·  10.1s  ·  $0.0083

- **Skill:** `superplane-monitor`
- **Input:** I'm getting null when I access `$['GitHub onPush'].ref` in a downstream node. Why?
- **Output:** `/app/evals/reports/20260425T041142_622967Z/payload_envelope_explain.json`
- **Log:** `/app/tmp/evals/622967Z-15-payload_envelope_explain.log`

| toolCalls | inputTokens | outputTokens | cacheRead | cacheWrite | cost |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 10 | 717 | 21728 | 1649 | $0.0083 |

**Assertions (1/2):**

- ✅ ResponseMentions: passed - response mentions 'data'
- ❌ ResponseMentions: failed - response does not mention 'envelope'. Preview: "I'd like to help you debug this! To better understand the issue, I need a bit more context:\n\n1. **What platform are you using?** (e.g., SuperPlane, n8n, Make, GitHub Actions, etc.)\n2. **What's the actual data structure?** Can you show me:\n   - The incoming webhook payload or trigger output\n   - How "

---

## 📊 Summary

- **Cases:** 7/15 passed  ·  **Assertions:** 15/23 passed
- **Total time:** 437.9s  ·  **Total cost:** $0.5806  ·  **Tool calls:** 89  ·  **Tokens (in/out):** 810/29580

| 🧩 Test | 🛠️ Skill | ✅ Result | Assertions | Duration | Cost | Tools | InTok | OutTok |
| --- | --- | :---: | :---: | ---: | ---: | ---: | ---: | ---: |
| `whoami_basic` | superplane-cli | ✅ Pass | 1/1 | 9.7s | $0.0146 | 2 | 28 | 538 |
| `list_components_github` | superplane-cli | ✅ Pass | 1/1 | 14.5s | $0.0216 | 3 | 36 | 909 |
| `missing_cli_refusal` | superplane-cli | ✅ Pass | 2/2 | 12.6s | $0.0201 | 3 | 28 | 889 |
| `connect_flow` | superplane-cli | ❌ Fail | 0/1 | 22.5s | $0.0229 | 3 | 36 | 1147 |
| `describe_trigger` | superplane-cli | ✅ Pass | 1/1 | 15.8s | $0.0289 | 4 | 36 | 1381 |
| `push_to_slack` | superplane-canvas-builder | ✅ Pass | 5/5 | 35.5s | $0.0560 | 11 | 68 | 3001 |
| `missing_integration_refusal` | superplane-canvas-builder | ✅ Pass | 3/3 | 16.0s | $0.0286 | 4 | 44 | 1272 |
| `starter_from_template` | superplane-canvas-builder | ❌ Fail | 0/1 | 84.3s | $0.1526 | 20 | 164 | 8889 |
| `draft_update_flag` | superplane-canvas-builder | ❌ Fail | 0/1 | 18.1s | $0.0296 | 5 | 52 | 1233 |
| `resource_verification` | superplane-canvas-builder | ❌ Fail | 0/1 | 42.5s | $0.0721 | 11 | 92 | 3748 |
| `why_did_my_run_fail` | superplane-monitor | ❌ Fail | 0/1 | 16.3s | $0.0269 | 4 | 44 | 1297 |
| `stuck_execution` | superplane-monitor | ❌ Fail | 0/1 | 19.2s | $0.0304 | 7 | 52 | 1607 |
| `cancel_flow` | superplane-monitor | ✅ Pass | 1/1 | 18.8s | $0.0373 | 7 | 68 | 1580 |
| `queue_inspect` | superplane-monitor | ❌ Fail | 0/1 | 17.6s | $0.0307 | 5 | 52 | 1372 |
| `payload_envelope_explain` | superplane-monitor | ❌ Fail | 1/2 | 10.1s | $0.0083 | 0 | 10 | 717 |
| **Total** | — | **7/15** | **15/23** | **437.9s** | **$0.5806** | **89** | **810** | **29580** |

