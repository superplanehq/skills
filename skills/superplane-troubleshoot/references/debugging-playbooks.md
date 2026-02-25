# Debugging Playbooks

Step-by-step playbooks for specific SuperPlane troubleshooting scenarios. Each playbook is a complete walkthrough from symptom to resolution.

## Playbook: Event Received But No Execution

**Symptom:** `superplane events list` shows events, but `superplane events list-executions` shows no executions for those events.

**Steps:**

1. Get the canvas and check the trigger node:
   ```bash
   superplane canvases get <canvas-name>
   ```

2. Is the trigger `paused: true`? If yes, set to `false` and update.

3. Check the trigger's filter configuration. For `github.onPush`, the `refs` filter may be excluding the event:
   ```yaml
   refs:
     - type: equals
       value: refs/heads/main
   ```
   If the push was to a different branch, it won't match.

4. Check the event payload matches what the trigger expects. The event may be from the right source but wrong action (e.g., PR closed vs PR opened).

5. If using a webhook trigger, verify the `secret` matches between SuperPlane and the sender.

---

## Playbook: Node Fails With Permission Error

**Symptom:** A node shows `Failed` with an error message containing "unauthorized", "forbidden", "403", or "401".

**Steps:**

1. Identify which integration the node uses:
   ```bash
   superplane canvases get <canvas-name>
   # Find the failing node's integration.id
   ```

2. Check the integration connection:
   ```bash
   superplane integrations get <integration-id>
   ```

3. If the integration shows as disconnected or expired, reconnect it in the SuperPlane UI (Settings → Integrations).

4. If the integration is connected but permissions are wrong, check the OAuth scopes or API token permissions on the provider side (e.g., GitHub token needs `repo` scope for private repos).

5. If using secrets in the node configuration, verify the secret exists and has the correct value:
   ```bash
   superplane secrets list
   ```

6. After fixing, trigger a new execution to test.

---

## Playbook: Expression Returns Null

**Symptom:** A node's configuration value evaluates to empty/null, causing unexpected behavior or failures.

**Steps:**

1. Identify the expression. Export the canvas:
   ```bash
   superplane canvases get <canvas-name>
   ```
   Find the node and its configuration fields containing `{{ }}`.

2. Check the referenced node name. If the expression is `$['GitHub Push'].ref`, verify there's a node with `name: GitHub Push` (exact casing).

3. Check the execution to see what the upstream node actually emitted:
   ```bash
   superplane events list-executions --canvas-id <id> --event-id <eid>
   ```
   Look at the upstream node's output payload.

4. If the field doesn't exist in the payload, the expression returns `nil`. Either:
   - Fix the field path to match the actual payload structure
   - Add a nil fallback: `$['Node'].field ?? "default"`

5. If the upstream node failed or was skipped, it has no output. Expressions referencing it return `nil`. Fix the upstream issue first.

---

## Playbook: Approval Gate Stuck

**Symptom:** An Approval node shows `Pending` and the workflow is blocked.

**Steps:**

1. Check if there's a pending approval in the UI. The Approval node shows a button for authorized approvers.

2. Check the queue:
   ```bash
   superplane queue list --canvas-id <id> --node-id <approval-node-id>
   ```

3. If the approval should have been granted but wasn't, check the `approvers` configuration — does it restrict who can approve?

4. To unblock in an emergency, an admin can approve through the UI or clear the queue item:
   ```bash
   superplane queue delete --canvas-id <id> --node-id <nid> --item-id <iid>
   ```
   Note: deleting the queue item cancels that execution branch — it doesn't approve it.

5. To prevent future blocks, consider adding a timeout or auto-approval mechanism for non-critical workflows.

---

## Playbook: Time Gate Not Opening

**Symptom:** A Time Gate node holds execution indefinitely, even during what should be allowed hours.

**Steps:**

1. Export the canvas and check the Time Gate configuration:
   ```bash
   superplane canvases get <canvas-name>
   ```

2. Verify the `timezone` is correct. Common mistake: using `EST` instead of `America/New_York` (IANA format required).

3. Check `allowedDays` — is today included? Values must be lowercase: `monday`, `tuesday`, etc.

4. Check `startHour` and `endHour` — these are in the configured timezone, 0-23 format. If `startHour: 9` and `endHour: 17`, the gate opens at 9am and closes at 5pm in that timezone.

5. If the current time is within the window but the gate isn't opening, check if the execution arrived before the window. The Time Gate holds until the next valid window opens.

6. To bypass in an emergency, temporarily change the Time Gate configuration to allow all hours (`startHour: 0`, `endHour: 23`, all days), update the canvas, then revert after the execution passes.

---

## Playbook: Progressive Delivery Rollback

**Symptom:** A progressive delivery canvas needs to be stopped mid-rollout because a health check failed or an issue was discovered.

**Steps:**

1. Identify the current execution:
   ```bash
   superplane events list --canvas-id <id>
   superplane events list-executions --canvas-id <id> --event-id <eid>
   ```

2. If an execution is currently running on a deploy node, cancel it:
   ```bash
   superplane executions cancel --canvas-id <id> --execution-id <eid>
   ```

3. If the canvas has an Approval gate before the next wave, simply reject the approval in the UI to stop progression.

4. If the rollout already reached a percentage and needs to be reverted, trigger the rollback manually (the canvas should have a rollback path, or trigger it outside SuperPlane).

5. To prevent the canvas from processing more events while you investigate, pause the trigger:
   ```bash
   superplane canvases get <canvas-name> > canvas.yaml
   # Set paused: true on the trigger node
   superplane canvases update --file canvas.yaml
   ```

6. After fixing the issue, unpause the trigger to resume normal operation.
