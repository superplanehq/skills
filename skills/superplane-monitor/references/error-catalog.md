# Error Catalog

Known SuperPlane error messages, their causes, and resolution steps.

## Node Errors

### "integration is required"

**Where:** Node `errorMessage` field after canvas update.

**Cause:** The node uses an integration-backed component or trigger but has no `integration.id` set in the canvas YAML.

**Fix:**
1. `superplane integrations list` — find the integration ID for the provider
2. Add `integration: { id: <id>, name: "" }` to the node
3. `superplane canvases update --file canvas.yaml`
4. `superplane canvases get <name>` — verify `errorMessage` is cleared

### Permission / Auth Errors

**Where:** Execution output on a failed node. Messages include "unauthorized", "forbidden", "401", "403", "invalid token".

**Cause:** The integration's credentials are expired, revoked, or lack the required permissions/scopes.

**Fix:**
1. `superplane integrations get <id>` — check the connection status
2. Reconnect the integration in the UI (Settings → Integrations) if expired
3. On the provider side, verify the OAuth app or API token has the required scopes (e.g., GitHub needs `repo` scope for private repositories)
4. Trigger a new execution to test

### Expression Evaluation Errors

**Where:** Execution output on a failed node. Messages include "expression error", "undefined variable", "cannot access field", "type mismatch".

**Cause:** The expression in a configuration field has a syntax error, references a non-existent node name, accesses a missing field, or returns the wrong type.

**Common messages and fixes:**

| Message | Cause | Fix |
| --- | --- | --- |
| `undefined variable` | `$['Node Name']` doesn't match any node | Check exact node name casing |
| `cannot access field X of nil` | Upstream node output is nil or missing field | Add nil check: `value ?? "default"` |
| `expected bool, got string` | Filter/If expression returns non-boolean | Change to `field == "value"` |
| `unexpected token` | Syntax error in expression | Check for missing quotes, brackets, operators |

## Canvas Validation Errors

### Duplicate Node Names

**Where:** Node `warningMessage` field after canvas update.

**Message:** Warning about duplicate node names.

**Cause:** Two or more nodes have the same `name` field. While not a hard error, it causes ambiguity in `$['Node Name']` references — only one node's output will be accessible.

**Fix:** Rename one of the duplicate nodes to be unique. Use descriptive names like `"CI Lint"` and `"CI Tests"` instead of both being `"CI"`.

### Missing Required Configuration

**Where:** Node `errorMessage` field after canvas update.

**Cause:** A required configuration field is missing from the node.

**Fix:**
1. `superplane index components --name <component>` — see all required fields
2. Add the missing fields to the node's `configuration` block
3. Update the canvas

### Invalid Edge Channel

**Where:** Canvas update fails or edges don't route correctly.

**Cause:** Using the wrong channel name for a component's output. Each component type has specific channels:

| Component | Valid Channels |
| --- | --- |
| Filter | `passed`, `failed` |
| If | `True`, `False` |
| Approval | `approved`, `rejected` |
| Everything else | `default` |

**Fix:** Change the edge's `channel` field to a valid value for the source component type. Note: `True`/`False` are capitalized for If nodes.

## Execution Errors

### Timeout

**Where:** Node shows `Failed` after a long `Running` period.

**Cause:** The external service (CI system, API endpoint, etc.) didn't respond within the timeout window.

**Fix:**
1. Check the external service's health independently
2. If the service is slow but functional, the operation may need to be restructured (e.g., use async polling instead of synchronous wait)
3. For HTTP components, check if the target URL is correct and reachable from the SuperPlane server

### External Service Errors

**Where:** Node shows `Failed` with HTTP status codes (4xx, 5xx) or provider-specific error messages.

**Common patterns:**

| Status | Meaning | Action |
| --- | --- | --- |
| 400 | Bad request | Check the request body/parameters in node configuration |
| 401/403 | Auth failure | See Permission / Auth Errors above |
| 404 | Not found | Check the resource identifier (repo name, project ID, etc.) |
| 429 | Rate limited | Reduce execution frequency or add Wait nodes between API calls |
| 500/502/503 | Server error | External service issue — retry later or check service status |

### Queue Overflow

**Where:** Multiple executions pile up on a node, visible in the queue.

**Symptoms:** Node shows many pending items, new executions queue instead of running.

**Cause:** Executions arrive faster than the node can process them. Common with high-frequency triggers or slow external services.

**Fix:**
1. Inspect the queue:
   ```bash
   superplane queue list --canvas-id <id> --node-id <nid>
   ```
2. Clear stuck items if needed:
   ```bash
   superplane queue delete --canvas-id <id> --node-id <nid> --item-id <iid>
   ```
3. Consider reducing trigger frequency, adding debouncing, or optimizing the slow node
