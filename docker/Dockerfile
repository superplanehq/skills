# Eval runner image: runs inside docker-compose on the same network as superplane-demo.
# Contains python + uv, node + claude CLI, and the real superplane CLI.
#
# Runs as a non-root `eval` user because the Claude Code CLI refuses
# --dangerously-skip-permissions (our permission_mode="bypassPermissions")
# when invoked as root.

FROM python:3.11-slim

ARG TARGETARCH=amd64

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1

# System deps.
RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates curl jq bash make git \
        nodejs npm \
    && rm -rf /var/lib/apt/lists/*

# Install uv into /usr/local/bin so it's available to all users.
RUN curl -LsSf https://astral.sh/uv/install.sh | sh \
    && cp /root/.local/bin/uv /usr/local/bin/uv \
    && cp /root/.local/bin/uvx /usr/local/bin/uvx \
    && rm -rf /root/.local

# Install Claude Code CLI — claude-agent-sdk spawns this as a subprocess.
RUN npm install -g @anthropic-ai/claude-code

# Install latest superplane CLI from GitHub releases. The /releases/latest/download/
# URL is a permanent redirect that always resolves to the most recent release asset.
RUN curl -fL "https://github.com/superplanehq/superplane/releases/latest/download/superplane-cli-linux-${TARGETARCH}" \
        -o /usr/local/bin/superplane \
    && chmod +x /usr/local/bin/superplane

# Non-root user. Home dir is where `superplane connect` will persist config and
# where Claude CLI will cache auth.
RUN useradd --create-home --shell /bin/bash --uid 1001 eval

WORKDIR /app
# Chown the app dir so bind-mounted volumes at runtime stay writable for us.
RUN chown -R eval:eval /app

USER eval
ENV HOME=/home/eval \
    PATH="/home/eval/.local/bin:${PATH}"

# Copy only the dependency manifest first — dep install stays cached across source changes.
COPY --chown=eval:eval pyproject.toml /app/
RUN uv sync --no-install-project

# Source is bind-mounted at runtime via docker-compose — no COPY . here.
# Default command runs bootstrap then evals; override with `docker compose run --rm evals bash`.
CMD ["bash", "-c", "scripts/bootstrap-token.sh && uv run python -m evals.runner"]
