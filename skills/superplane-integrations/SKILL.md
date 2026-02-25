---
name: superplane-integrations
description: Discover, connect, and configure SuperPlane integrations. Covers the full lifecycle from listing available providers to binding integration instances to canvas nodes and resolving integration-resource fields. Use when connecting a new integration, troubleshooting "integration is required" errors, listing resources for a connected integration, or selecting the right provider for a workflow.
---

# SuperPlane Integrations

Manage the lifecycle of integrations that connect SuperPlane to external services.

## Quick Reference

| Task | Command |
| --- | --- |
| List available providers | `superplane index integrations` |
| Describe a provider | `superplane index integrations --name <provider>` |
| List connected integrations | `superplane integrations list` |
| Inspect a connection | `superplane integrations get <id>` |
| List resources | `superplane integrations list-resources --id <id> --type <type>` |
| Provider's triggers | `superplane index triggers --from <provider>` |
| Provider's components | `superplane index components --from <provider>` |

## Integration Lifecycle

### 1. Discover Available Providers

```bash
superplane index integrations
```

This lists all providers SuperPlane supports (GitHub, Slack, AWS, etc.). To see what a specific provider offers:

```bash
superplane index integrations --name github
superplane index triggers --from github
superplane index components --from github
```

### 2. Connect a Provider (UI)

Integrations are connected through the SuperPlane UI:

1. Go to **Settings → Integrations**
2. Select the provider
3. Follow the OAuth flow or enter API credentials
4. The connection gets an **integration ID** — you'll need this for canvas YAML

To find the ID after connecting:

```bash
superplane integrations list
```

### 3. Bind Integration to Canvas Nodes

Any node that uses an integration-backed component or trigger needs the `integration.id` field:

```yaml
- id: my-node
  name: github.onPush
  type: TYPE_TRIGGER
  trigger:
    name: github.onPush
  integration:
    id: <github-integration-id>    # from `superplane integrations list`
    name: ""
  configuration:
    repository: myorg/myapp
```

### 4. Configure Resource Fields

Some configuration fields have type `integration-resource` — their valid values come from the connected integration. For example, `repository` is a GitHub resource, `project` is a Semaphore resource.

```bash
superplane integrations list-resources --id <integration-id> --type <resource-type>
```

Use the returned values in your canvas YAML configuration.

## Binding Integrations to Nodes

### Finding the Integration ID

```bash
superplane integrations list
```

Output shows each connected integration with its ID, provider, and name. Copy the ID for the provider you need.

### Setting integration.id in YAML

Every trigger or component node that uses an external service must have:

```yaml
integration:
  id: <integration-id>
  name: ""
```

Built-in components (filter, if, approval, merge, wait, timegate, http, ssh, noop) do **not** need an integration.

### Multiple Integrations of the Same Provider

You can connect multiple instances of the same provider (e.g., two GitHub orgs). Each gets a unique ID. Nodes reference the specific instance they need.

## Resolving integration-resource Fields

When `superplane index components --name <component>` shows a field with type `integration-resource`, the field's valid values are dynamic — they come from the connected integration.

### Step-by-step

1. Identify the field type:

```bash
superplane index components --name semaphore.runWorkflow
# Look for fields with type: integration-resource
# e.g., "project" has type "integration-resource"
```

2. Find the integration ID:

```bash
superplane integrations list
# Find the Semaphore integration ID
```

3. List available resources:

```bash
superplane integrations list-resources --id <semaphore-id> --type project
```

4. Some resources need parameters (e.g., listing branches requires a project first):

```bash
superplane integrations list-resources --id <id> --type branch --parameters project=<project-id>
```

5. Use the returned value in your canvas YAML configuration.

## Resolving "integration is required"

This is the most common integration error. It appears as a node `errorMessage` when a node uses an integration-backed component but has no `integration.id` set.

### Fix

1. Confirm the provider is connected:

```bash
superplane integrations list
```

2. If not connected, connect it in the UI (Settings → Integrations).

3. Get the integration ID from the list output.

4. Add it to the node in your canvas YAML:

```yaml
integration:
  id: <the-id-from-step-3>
  name: ""
```

5. Apply the fix:

```bash
superplane canvases update --file canvas.yaml
```

6. Verify the error is cleared:

```bash
superplane canvases get <canvas-name>
# Check that errorMessage is empty on the node
```

## Provider Categories

| Category | Providers |
| --- | --- |
| CI/CD | GitHub, GitLab, Bitbucket, Semaphore, CircleCI, Harness, Render |
| Cloud & Infra | AWS (ECR, Lambda, CodeArtifact, CloudWatch, SNS), Cloudflare, DigitalOcean, DockerHub, Google Cloud, Hetzner Cloud |
| Observability | Datadog, Dash0, Grafana, Prometheus |
| Incident | PagerDuty, Rootly, Statuspage, incident.io |
| Communication | Discord, SendGrid, Slack, SMTP, Telegram |
| Ticketing | Jira, ServiceNow |
| AI & LLM | Claude, Cursor, OpenAI |
| Dev Tools | Daytona, JFrog Artifactory |

## References

- [Provider Catalog](references/provider-catalog.md) — All providers with their triggers and components
