# All-in-docker eval harness. Every `make evals` invocation brings up a fresh
# superplane-demo stack, runs the selected cases inside an eval container on the
# same internal network, and tears everything down (including named volumes).
#
# Requires: Docker + Compose, ANTHROPIC_API_KEY in env.
#
#   make evals                          # all cases
#   make evals CASES=push_to_slack      # single case
#   make evals SKILL=superplane-cli     # all cases for one skill
#   EVAL_MODEL=claude-opus-4-7 make evals
#   make evals.shell                    # drop into the eval container for debugging
#   make evals.list                     # print case names (no stack boot needed? — yes: inside container)

COMPOSE := docker compose -f docker-compose.yml

# CASES/SKILL aliases so the Makefile matches the host-facing UX of the runner,
# while passing into the container as EVAL_CASES/EVAL_SKILL (what the runner reads).
CASES ?=
SKILL ?=
export EVAL_CASES := $(CASES)
export EVAL_SKILL := $(SKILL)

.PHONY: evals evals.list evals.shell evals.down evals.build evals.cli evals.canvas evals.monitor

evals:
	@mkdir -p evals/reports tmp
	@$(COMPOSE) up --build --abort-on-container-exit --exit-code-from evals; \
		status=$$?; \
		$(COMPOSE) down -v --remove-orphans >/dev/null 2>&1 || true; \
		exit $$status

evals.list:
	@mkdir -p evals/reports tmp
	@$(COMPOSE) run --rm --entrypoint="" evals uv run python -m evals.runner --list
	@$(COMPOSE) down -v --remove-orphans >/dev/null 2>&1 || true

evals.shell:
	@mkdir -p evals/reports tmp
	@$(COMPOSE) run --rm --entrypoint="" evals bash

evals.build:
	@$(COMPOSE) build

evals.down:
	@$(COMPOSE) down -v --remove-orphans

# Skill-scoped shortcuts.
evals.cli:
	@$(MAKE) evals SKILL=superplane-cli

evals.canvas:
	@$(MAKE) evals SKILL=superplane-canvas-builder

evals.monitor:
	@$(MAKE) evals SKILL=superplane-monitor
