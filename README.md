# SuperPlane Skills

Agent skills for operating [SuperPlane](https://github.com/superplanehq/superplane) — the open source DevOps control plane for event-driven workflows.

## Install

```bash
npx skills add superplanehq/skills
```

Or install a specific skill:

```bash
npx skills add superplanehq/skills --skill superplane-cli
```

## Skills

| Skill | Description |
| --- | --- |
| **superplane-api** | Call the SuperPlane REST API directly — OpenAPI spec, auth, HTTP requests |
| **superplane-cli** | Operate SuperPlane via CLI — auth, canvases, secrets, runs |
| **superplane-canvas-builder** | Design workflow canvases from requirements |
| **superplane-monitor** | Debug and inspect workflow executions |

## Running Evals

Regression tests for the skills. Each eval spawns a real Claude Code session with a skill loaded, gives it a task, and asserts the bash commands / canvas YAML / response Claude produces.

### Run

```bash
export ANTHROPIC_API_KEY=sk-ant-...

make evals                              # all 15 cases
make evals CASES=push_to_slack          # one case
make evals SKILL=superplane-cli         # all cases for one skill
make evals.list                         # list case names without running
```

That's it. `make evals` builds the eval image, boots a fresh `superplane-demo` container alongside it on an internal Docker network, runs the cases, then tears the whole stack down.

### Common knobs

```bash
EVAL_MODEL=claude-sonnet-4-5 make evals       # different model (default: claude-haiku-4-5)
EVAL_REPORT_FORMAT=markdown make evals        # markdown table only on stdout
EVAL_REPORT_FORMAT=text make evals            # superplane-style text report only
make evals.shell                              # bash inside the eval container for debugging
make evals.down                               # nuke leftover stack
```

### Where to find results

After every run:

- `evals/reports/<run_id>/report.md` — per-case detail + summary table (open in any markdown viewer)
- `evals/reports/<run_id>/summary.json` — machine-readable totals + per-case stats
- `evals/reports/<run_id>/<case_name>.json` — full per-case detail (bash commands, files written, response text)
- `tmp/evals/<run_id>-NN-<case_name>.log` — timestamped event log per case

