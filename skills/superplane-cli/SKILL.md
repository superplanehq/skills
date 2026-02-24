---
name: superplane-cli
description: Operate SuperPlane via CLI — authenticate, manage canvases, secrets, integrations, events, and executions. Use when the user wants to interact with a SuperPlane instance, run CLI commands, create or update workflows, or manage configuration. Triggers on "superplane", "canvas", "workflow", "CLI", "connect".
---

# SuperPlane CLI

Operate a SuperPlane instance through the `superplane` CLI.

## Quick Reference

| Task | Command |
| --- | --- |
| Connect to org | `superplane connect <URL> <TOKEN>` |
| Who am I | `superplane whoami` |
| List/switch contexts | `superplane contexts` |
| List canvases | `superplane canvases list` |
| Create canvas from YAML | `superplane canvases create --file canvas.yaml` |
| Export canvas | `superplane canvases get <name>` |
| Update canvas | `superplane canvases update -f canvas.yaml` |
| List integrations | `superplane index integrations` |
| List components | `superplane index components` |
| Describe a component | `superplane index components --name <name>` |
| List triggers | `superplane index triggers --from <integration>` |
| List secrets | `superplane secrets list` |
| Create secret | `superplane secrets create --file secret.yaml` |
| List events | `superplane events list --canvas-id <id>` |
| List executions | `superplane executions list --canvas-id <id> --node-id <nid>` |
| Cancel execution | `superplane executions cancel --canvas-id <id> --execution-id <eid>` |

## Core Workflow

### 1. Authenticate

Create a service account in the SuperPlane UI, then:

```bash
superplane connect https://superplane.example.com <API_TOKEN>
superplane whoami
```

### 2. Discover Components

```bash
superplane index integrations
superplane index components --from github
superplane index triggers --from github
```

### 3. Create or Update a Canvas

Export-edit-apply:

```bash
superplane canvases get my-canvas > canvas.yaml
# edit canvas.yaml
superplane canvases update -f canvas.yaml
```

Or create from scratch:

```bash
superplane canvases create --file canvas.yaml
```

See [Canvas YAML Spec](references/canvas-yaml-spec.md) for the format.

### 4. Manage Secrets

```bash
superplane secrets create --file secret.yaml
superplane secrets list
superplane secrets update --file secret.yaml
superplane secrets delete <name_or_id>
```

### 5. Monitor Runs

```bash
superplane events list --canvas-id <id>
superplane events list-executions --canvas-id <id> --event-id <eid>
```

## CLI Installation

```bash
curl -L https://install.superplane.com/superplane-cli-darwin-arm64 -o superplane
chmod +x superplane && sudo mv superplane /usr/local/bin/superplane
```

Binaries: `darwin-arm64`, `darwin-amd64`, `linux-amd64`.

## When to Use Other Skills

| Need | Use Skill |
| --- | --- |
| Design a canvas from requirements | superplane-canvas-builder |
| Debug a failed execution | superplane-monitor |

## References

- [Canvas YAML Spec](references/canvas-yaml-spec.md) — Full YAML format with examples
