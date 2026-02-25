# SuperPlane Skills Repository

This repo contains agent skills for [SuperPlane](https://github.com/superplanehq/superplane) — the open source DevOps control plane for event-driven workflows.

## Repo Structure

```
skills/                  # All skills live here (Agent Skills spec format)
  <skill-name>/
    SKILL.md             # Required — frontmatter + instructions
    references/          # Optional — detailed docs loaded on demand
.cursor-plugin/          # Cursor Marketplace plugin manifests
scripts/                 # Validation and build tooling
```

## Adding or Editing Skills

Every skill directory must contain a `SKILL.md` with YAML frontmatter:

```yaml
---
name: skill-name
description: What this skill does and when to use it.
---
```

Rules:
- `name` must be lowercase, letters/numbers/hyphens only, max 64 chars
- `name` must match the parent directory name exactly
- `description` max 1024 chars, must include both WHAT and WHEN
- Keep `SKILL.md` body under 500 lines; move heavy reference to `references/`
- Reference files must be one level deep from `SKILL.md`

## Validation

Before committing, run:

```bash
node scripts/validate.mjs
```

This checks frontmatter, naming, plugin manifests, and broken references.

## SuperPlane Domain Context

**Canvas**: A directed graph of steps (nodes) and dependencies (edges) that models a workflow.

**Component nodes**: Each step in a canvas. Can be built-in (Filter, If, Approval, Merge, Wait, Time Gate, HTTP, SSH, Noop) or integration-backed (GitHub, Semaphore, Slack, AWS, etc.).

**Triggers**: Entry points that start canvas executions — schedule, manual_run, webhook, or integration events (e.g. github.onPush).

**Edges**: Connections between nodes with output channels (default, passed/failed, True/False, approved/rejected).

**Expressions**: Expr language inside `{{ }}` for referencing upstream data — `$['Node Name'].field`, `root()`, `previous()`.

**Integrations**: Connected external service instances (GitHub org, Slack workspace, AWS account). Nodes that use integrations need an `integration.id`.

## Distribution Channels

- **Agent Skills CLI**: `npx skills add superplanehq/skills`
- **Cursor Marketplace**: `.cursor-plugin/` manifests (single-plugin layout)

Both channels read from the same `skills/` directory.

## Docs References

- SuperPlane docs: https://docs.superplane.com/
- LLM-friendly docs index: https://docs.superplane.com/llms.txt
- LLM-friendly full docs: https://docs.superplane.com/llms-full.txt
- Agent Skills spec: https://agentskills.io/specification
