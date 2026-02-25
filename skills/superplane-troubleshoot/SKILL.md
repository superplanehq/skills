---
name: superplane-troubleshoot
description: Diagnose and fix SuperPlane canvas and execution problems using decision-tree troubleshooting. Covers canvas won't activate, events not triggering executions, nodes stuck in pending, expression errors, merge deadlocks, and integration failures. Use when something isn't working, a workflow is broken, or the user says "it's not running", "stuck", "broken", "why didn't it trigger".
---

# SuperPlane Troubleshoot

Decision-tree troubleshooting for SuperPlane canvas and execution problems.

## Quick Diagnosis

Start here. What's the symptom?

| Symptom | Jump to |
| --- | --- |
| Canvas exists but nothing happens | [No Executions Starting](#no-executions-starting) |
| Execution starts but a node fails | [Node Failure](#node-failure) |
| Execution starts but a node is stuck | [Node Stuck](#node-stuck) |
| Expression returns wrong value | [Expression Problems](#expression-problems) |
| Merge node never fires | [Merge Deadlock](#merge-deadlock) |
| Canvas update rejected | [Canvas Validation Errors](#canvas-validation-errors) |

## No Executions Starting

**Canvas exists but no executions appear when you expect them.**

Check in order:

1. **Is the trigger paused?**
   ```bash
   superplane canvases get <name>
   ```
   Look for `paused: true` on the trigger node. Set to `false` and update.

2. **Is the trigger configured correctly?**
   - Schedule: is the cron expression or interval correct?
   - GitHub: does the `repository` match? Are the `refs` filters correct?
   - Webhook: has the external system been configured to POST to the webhook URL?

3. **Is the integration connected?**
   ```bash
   superplane integrations list
   ```
   If the trigger uses an integration (e.g., `github.onPush`), confirm the integration ID is set and the connection is active.

4. **Was the event actually sent?**
   ```bash
   superplane events list --canvas-id <id>
   ```
   If events appear but no executions, the trigger received the event but filtering may have excluded it. Check trigger `refs` or other filters.

5. **If no events appear at all**, the external system isn't sending to SuperPlane. Check webhook configuration on the source side.

## Node Failure

**An execution started but a node shows `Failed` status.**

```bash
superplane events list-executions --canvas-id <id> --event-id <eid>
```

Check the failed node's error message:

1. **"integration is required"** → The node needs an `integration.id`. See the superplane-integrations skill.

2. **Permission/auth error** → The integration's credentials are expired or lack permissions.
   ```bash
   superplane integrations get <integration-id>
   ```
   Reconnect the integration in the UI if needed.

3. **Expression evaluation error** → The expression references a missing field or has a syntax error. See [Expression Problems](#expression-problems).

4. **HTTP error (4xx/5xx)** → The external service returned an error. Check the response body in the execution details for specifics.

5. **Timeout** → The external service didn't respond in time. Check if the service is healthy independently.

## Node Stuck

**A node shows `Pending` or `Running` for longer than expected.**

1. **Approval node** → Waiting for human approval. Check the SuperPlane UI for pending approvals, or inspect the queue:
   ```bash
   superplane queue list --canvas-id <id> --node-id <nid>
   ```

2. **Time Gate** → Holding until the allowed window. Check the `timezone`, `allowedDays`, `startHour`, `endHour` configuration. The execution will release when the window opens.

3. **Wait node** → Holding for the configured duration or timestamp. This is expected behavior.

4. **Merge node** → Waiting for all incoming edges. See [Merge Deadlock](#merge-deadlock).

5. **External service slow** → The integration component is waiting for a response. Check the external service's health.

6. **Queue backed up** → Multiple executions queued on the same node:
   ```bash
   superplane queue list --canvas-id <id> --node-id <nid>
   ```
   Clear stuck items if needed:
   ```bash
   superplane queue delete --canvas-id <id> --node-id <nid> --item-id <iid>
   ```

## Expression Problems

**An expression returns the wrong value, nil, or causes an error.**

1. **Check node name casing**: `$['Node Name']` is case-sensitive. Run `superplane canvases get <name>` and compare the exact `name` field.

2. **Check the field path**: the upstream node may emit a different payload structure than expected. Inspect the execution output to see what was actually emitted.

3. **Nil from missing field**: if the upstream node didn't emit the expected field, the expression returns `nil`. Use `?? "default"` for fallback values.

4. **Type mismatch**: Filter and If expressions must return a boolean. `$['Node'].status` (a string) is not a boolean — use `$['Node'].status == "success"`.

5. **Missing `{{ }}` delimiters**: the value is treated as a literal string if not wrapped in expression delimiters.

6. **Referencing a parallel node**: you can only reference nodes that are upstream (connected by edges). If node A is parallel to node B, neither can reference the other. Add a Merge node first.

## Merge Deadlock

**A Merge node never fires — execution stops.**

Merge waits for **all** incoming edges to have a completed execution. If any upstream branch doesn't complete, Merge blocks forever.

Common causes:

1. **A branch was filtered out**: If a Filter or If node routed execution to the other channel, the Merge branch never receives an execution.
   - Fix: ensure all branches that feed into Merge will always execute, or restructure to avoid the Merge dependency.

2. **An upstream node failed**: a failed node doesn't propagate to downstream nodes, so Merge never gets that branch's input.
   - Fix: add error handling or restructure so failures are handled before the Merge.

3. **An upstream node is stuck**: see [Node Stuck](#node-stuck) for that branch.

4. **Wrong edge wiring**: an edge is missing between an upstream node and the Merge.
   ```bash
   superplane canvases get <name>
   ```
   Verify that every branch intended to feed into the Merge has an edge with `targetId` pointing to the Merge node.

## Canvas Validation Errors

**`superplane canvases update` rejects the YAML, or nodes show `errorMessage`/`warningMessage`.**

1. **Duplicate node names**: each node's `name` must be unique within the canvas. The server sets a `warningMessage` on duplicates. Rename one of the nodes.

2. **Missing required configuration**: run `superplane index components --name <component>` to see required fields. Add the missing fields to the node's `configuration`.

3. **Invalid edge channel**: each component type has specific output channels. Using `default` on a Filter (which uses `passed`/`failed`) will fail. See the channel table:

   | Component | Valid Channels |
   | --- | --- |
   | Filter | `passed`, `failed` |
   | If | `True`, `False` |
   | Approval | `approved`, `rejected` |
   | Everything else | `default` |

4. **Missing integration.id**: integration-backed nodes need `integration.id`. See the superplane-integrations skill.

5. **Invalid YAML syntax**: check for indentation errors, missing quotes around expressions with special characters, or malformed arrays.

## References

- [Debugging Playbooks](references/debugging-playbooks.md) — Step-by-step playbooks for specific scenarios
