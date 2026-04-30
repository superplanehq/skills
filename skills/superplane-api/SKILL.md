---
name: superplane-api
description: Use when calling the SuperPlane REST API directly (without the CLI), or when an agent or script needs the machine-readable OpenAPI spec to generate or verify HTTP requests. Covers the spec endpoint, cookie-based token authentication, base URL conventions, pagination, and resource overview. Triggers on "API", "REST", "OpenAPI", "Swagger", "HTTP request", "service account token", "superplane API".
---

# SuperPlane API

Call the SuperPlane API over HTTPS. Use this skill when the CLI is unavailable or when you need programmatic HTTP access — for example, from scripts, CI jobs, or coding agents that generate requests from the OpenAPI spec.

## OpenAPI Spec Endpoint

The machine-readable API spec is served at a public URL:

```
GET https://app.superplane.com/api/v1/docs/superplane.swagger.json
```

- **Format:** Swagger 2.0 (application/json)
- **Auth to read:** None
- **Versioning:** The spec ships with the API, so it matches the running service

### Fetching the spec

Use any HTTP client. Examples:

```bash
curl -s https://app.superplane.com/api/v1/docs/superplane.swagger.json -o superplane.swagger.json
```

```python
import urllib.request, json

spec = json.loads(
    urllib.request.urlopen(
        "https://app.superplane.com/api/v1/docs/superplane.swagger.json"
    ).read()
)
print(spec["info"]["title"], spec["info"]["version"])
```

Agents should fetch the spec **once per session** and cache it in memory.

### Self-hosted instances

For on-prem or self-hosted SuperPlane, replace the host:

```
GET https://<your-superplane-host>/api/v1/docs/superplane.swagger.json
```

The path is the same on every deployment.

## Authentication

The spec endpoint is public, but **all other API endpoints require authentication**.

### Obtaining a token

1. **Service account** — create one in the SuperPlane UI, then use its token for automation.
2. **Personal token** — regenerate via `POST /api/v1/me/token` (requires an existing session).

### Header construction

SuperPlane does **not** use the `Authorization: Bearer` header. Pass the token in the **`Cookie`** header:

```
Cookie: token=<API_TOKEN>
```

Do not send `Authorization: Bearer <token>` — the API will ignore it and return `401`.

### Example: authenticated request

```bash
curl -s https://app.superplane.com/api/v1/canvases \
  -H "Cookie: token=$SUPERPLANE_TOKEN"
```

```python
import urllib.request, json

req = urllib.request.Request(
    "https://app.superplane.com/api/v1/canvases",
    headers={"Cookie": f"token={TOKEN}"},
)
canvases = json.loads(urllib.request.urlopen(req).read())
```

### Verifying a token

```bash
curl -s https://app.superplane.com/api/v1/me \
  -H "Cookie: token=$SUPERPLANE_TOKEN"
```

A `200` response with user details confirms the token is valid. Any `401` or connection error means the token or host is incorrect.

## Base URL and Conventions

| Property | Value |
| --- | --- |
| Base URL (SaaS) | `https://app.superplane.com` |
| API prefix | `/api/v1/` |
| Content-Type | `application/json` (request and response) |
| Schemes | HTTPS (production), HTTP (local dev) |
| Success status | `200` for all methods including POST and DELETE (gRPC-gateway convention) |
| Pagination | Cursor-based: `?limit=<int>&before=<RFC 3339 timestamp>` on list endpoints |

### Pagination

List endpoints that support pagination accept two optional query parameters:

- `limit` (integer) — max items to return
- `before` (date-time, RFC 3339) — return items created before this timestamp

To page forward, take the timestamp of the last item in the current response and pass it as `before` in the next request. When the response contains fewer items than `limit`, you have reached the end.

### Error responses

Errors follow the gRPC-gateway status shape. The `code` field is a **gRPC status integer**, not an HTTP status code.

```json
{
  "code": 5,
  "message": "canvas not found",
  "details": []
}
```

Common codes: `3` = invalid argument, `5` = not found, `7` = permission denied, `16` = unauthenticated.

## Resource Overview

The API is organized into these resource groups. Every path is under `/api/v1/`.

| Resource | Key Paths | Operations |
| --- | --- | --- |
| **Actions** | `actions`, `actions/{name}` | List, describe |
| **Agents** | `agents/chats`, `agents/chats/{chatId}`, `.../messages`, `.../resume` | List, create, describe, delete, list messages, resume |
| **Blueprints** | `blueprints`, `blueprints/{id}` | CRUD |
| **Canvases** | `canvases`, `canvases/{id}` | CRUD |
| **Canvas Versions** | `canvases/{canvasId}/versions`, `.../versions/{versionId}`, `.../publish`, `.../validate` | List, create, describe, update, delete, publish, validate |
| **Change Requests** | `canvases/{canvasId}/change-requests`, `.../{changeRequestId}`, `.../actions`, `.../resolve` | List, create, describe, act (approve/reject/publish), resolve conflicts |
| **Canvas Events** | `canvases/{canvasId}/events`, `.../events/{eventId}/executions` | List events, list executions per event |
| **Node Executions** | `canvases/{canvasId}/nodes/{nodeId}/executions`, `.../events`, `.../pause`, `.../queue` | List, cancel, invoke hooks, manage queue |
| **Memory** | `canvases/{canvasId}/memory`, `.../memory/{memoryId}` | Get, delete |
| **Groups** | `groups`, `groups/{groupName}`, `.../users`, `.../users/remove` | CRUD, manage members |
| **Integrations** | `integrations`, `organizations/{id}/integrations`, `.../{integrationId}`, `.../resources` | List available, CRUD connected, list resources |
| **Invitations** | `organizations/{id}/invitations`, `.../{invitationId}`, `invite-links/{token}/accept` | List, create, revoke, accept |
| **Me** | `me`, `me/token` | Get current user, regenerate token |
| **Organizations** | `organizations/{id}`, `.../agent-settings`, `.../usage`, `.../users/{userId}` | Describe, update, manage agent settings, usage |
| **Roles** | `roles`, `roles/{roleName}`, `.../users` | CRUD, list members |
| **Secrets** | `secrets`, `secrets/{idOrName}`, `.../keys/{keyName}`, `.../name` | CRUD, manage keys, rename |
| **Service Accounts** | `service-accounts`, `service-accounts/{id}`, `.../token` | CRUD, regenerate token |
| **Triggers** | `triggers`, `triggers/{name}` | List, describe |
| **Users** | `users` | List |
| **Widgets** | `widgets`, `widgets/{name}` | List, describe |

## Typical Agent Workflow

1. **Fetch the spec** — one GET to the public endpoint, cache for the session.
2. **Authenticate** — set `Cookie: token=<TOKEN>` on all subsequent requests.
3. **Verify** — `GET /api/v1/me` to confirm the token works.
4. **Discover** — list canvases, integrations, triggers, or components to understand what exists.
5. **Operate** — create/update/delete resources as needed.

## When to Use Other Skills

| Need | Use Skill |
| --- | --- |
| Operate via CLI instead of HTTP | superplane-cli |
| Design a canvas from requirements | superplane-canvas-builder |
| Debug a failed execution | superplane-monitor |
| Write expressions in canvas configs | superplane-expressions |

## Documentation

For agents that can fetch URLs, the full SuperPlane docs are available in LLM-friendly format:

- Compact index: https://docs.superplane.com/llms.txt
- Full content: https://docs.superplane.com/llms-full.txt
