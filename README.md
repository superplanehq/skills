# SuperPlane Skills

Agent skills for operating [SuperPlane](https://github.com/superplanehq/superplane) — the open source DevOps control plane for event-driven workflows.

## Install

### Agent Skills CLI

```bash
npx skills add superplanehq/skills
```

Or install a specific skill:

```bash
npx skills add superplanehq/skills --skill superplane-cli
```

### Cursor Marketplace

This repo is also available as a Cursor plugin. Install from the Cursor Marketplace or add manually:

```bash
npx skills add superplanehq/skills -a cursor -g -y
```

## Skills

| Skill | Description |
| --- | --- |
| **superplane-cli** | Operate SuperPlane via CLI — auth, canvases, secrets, runs |
| **superplane-canvas-builder** | Design workflow canvases from requirements |
| **superplane-monitor** | Debug and inspect workflow executions |
| **superplane-expressions** | Write and debug Expr language expressions in canvas configs |
| **superplane-integrations** | Discover, connect, and configure integration providers |
| **superplane-troubleshoot** | Decision-tree troubleshooting for canvas and execution problems |

## Validation

```bash
node scripts/validate.mjs
```

Checks SKILL.md frontmatter, naming conventions, plugin manifests, and broken references.

## Contributing

Skills follow the [Agent Skills specification](https://agentskills.io/specification). Each skill is a directory under `skills/` containing a `SKILL.md` with YAML frontmatter (`name` and `description` required). See [AGENTS.md](AGENTS.md) for repo conventions.

## License

Apache-2.0
