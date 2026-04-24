#!/usr/bin/env bash
# Bootstrap a fresh superplane-demo instance and hand off a working CLI session.
#
# Runs inside the eval container. Assumes:
#   - SUPERPLANE_URL points at the superplane service on the internal compose network
#   - The demo container is freshly booted (no prior owner configured)
#   - `superplane` CLI and `curl`/`jq` are on PATH (provided by docker/Dockerfile)
#
# Flow:
#   1. Wait for /api/v1/health (or the SPA root) to respond.
#   2. POST /api/v1/setup-owner — creates the first owner, returns organization_id
#      and sets a session cookie.
#   3. POST /api/v1/service-accounts — creates a service account.
#   4. POST /api/v1/service-accounts/{id}/token — returns the API token.
#   5. superplane connect $SUPERPLANE_URL $TOKEN — persists CLI session to ~/.superplane/.
#
# On success: `superplane whoami` works for any subsequent process inheriting $HOME.
set -euo pipefail

: "${SUPERPLANE_URL:?SUPERPLANE_URL must be set (e.g. http://superplane:3000)}"

OWNER_EMAIL="${EVAL_OWNER_EMAIL:-eval@evals.local}"
OWNER_PASSWORD="${EVAL_OWNER_PASSWORD:-Password1}"
SA_NAME="${EVAL_SA_NAME:-skills-evals}"
COOKIE_JAR="$(mktemp -t sp-cookies.XXXXXX)"
trap 'rm -f "$COOKIE_JAR"' EXIT

log() { echo "[bootstrap] $*" >&2; }

# --- 1. wait for readiness --------------------------------------------------
log "waiting for $SUPERPLANE_URL ..."
for i in $(seq 1 120); do
  if curl -fsS --max-time 2 "$SUPERPLANE_URL/" >/dev/null 2>&1; then
    log "up after ${i}s"
    break
  fi
  if [ "$i" = 120 ]; then
    log "FAIL: $SUPERPLANE_URL did not become ready in 120s"
    exit 1
  fi
  sleep 1
done

# --- 2. setup-owner ----------------------------------------------------------
setup_payload=$(cat <<JSON
{
  "email": "$OWNER_EMAIL",
  "first_name": "Eval",
  "last_name": "Bot",
  "password": "$OWNER_PASSWORD",
  "smtp_enabled": false,
  "smtp_host": "",
  "smtp_port": 0,
  "smtp_username": "",
  "smtp_password": "",
  "smtp_from_name": "",
  "smtp_from_email": "",
  "smtp_use_tls": false,
  "allow_private_network_access": false
}
JSON
)

log "POST /api/v1/setup-owner"
setup_status=$(curl -sS -o /tmp/setup.json -w "%{http_code}" \
  -c "$COOKIE_JAR" \
  -H "Content-Type: application/json" \
  -X POST "$SUPERPLANE_URL/api/v1/setup-owner" \
  -d "$setup_payload")

if [ "$setup_status" = "409" ]; then
  log "instance already initialized (409). Falling back to login with configured creds."
  # If the instance was booted with tmpfs we expect a fresh setup every time, so 409
  # means something's off. Still try to proceed via login for resilience.
  login_payload=$(printf '{"email":"%s","password":"%s"}' "$OWNER_EMAIL" "$OWNER_PASSWORD")
  login_status=$(curl -sS -o /tmp/login.json -w "%{http_code}" \
    -c "$COOKIE_JAR" \
    -H "Content-Type: application/json" \
    -X POST "$SUPERPLANE_URL/api/v1/login" \
    -d "$login_payload")
  if [ "$login_status" != "200" ]; then
    log "FAIL: login returned $login_status"
    cat /tmp/login.json >&2 || true
    exit 1
  fi
  ORG_ID=$(jq -r '.organization_id // empty' /tmp/login.json)
elif [ "$setup_status" != "200" ] && [ "$setup_status" != "201" ]; then
  log "FAIL: setup-owner returned $setup_status"
  cat /tmp/setup.json >&2 || true
  exit 1
else
  ORG_ID=$(jq -r '.organization_id // empty' /tmp/setup.json)
fi

if [ -z "${ORG_ID:-}" ]; then
  log "FAIL: no organization_id in setup response"
  cat /tmp/setup.json >&2 || true
  exit 1
fi
log "organization_id=$ORG_ID"

# --- 3. create service account ----------------------------------------------
# NOTE: scoped endpoints require an `x-organization-id` header (see
# web_src/src/lib/withOrganizationHeader.ts in the superplane repo).
sa_payload=$(printf '{"name":"%s","description":"Used by skill evals","role":"org_admin"}' "$SA_NAME")
log "POST /api/v1/service-accounts (name=$SA_NAME)"
sa_status=$(curl -sS -o /tmp/sa.json -w "%{http_code}" \
  -b "$COOKIE_JAR" \
  -H "Content-Type: application/json" \
  -H "x-organization-id: $ORG_ID" \
  -X POST "$SUPERPLANE_URL/api/v1/service-accounts" \
  -d "$sa_payload")

if [ "$sa_status" != "200" ] && [ "$sa_status" != "201" ]; then
  log "FAIL: create service-account returned $sa_status"
  cat /tmp/sa.json >&2 || true
  exit 1
fi

SA_ID=$(jq -r '.serviceAccount.id // .service_account.id // .id // .data.id // empty' /tmp/sa.json)
# Create returns { serviceAccount: {...}, token: "..." } per the real backend response.
SA_TOKEN=$(jq -r '.token // .data.token // .api_token // .serviceAccount.token // empty' /tmp/sa.json)

if [ -z "$SA_ID" ]; then
  log "FAIL: no service-account id in response"
  cat /tmp/sa.json >&2 || true
  exit 1
fi
log "service_account_id=$SA_ID"

# --- 4. get/regenerate token -------------------------------------------------
if [ -z "$SA_TOKEN" ]; then
  log "POST /api/v1/service-accounts/$SA_ID/token"
  token_status=$(curl -sS -o /tmp/token.json -w "%{http_code}" \
    -b "$COOKIE_JAR" \
    -H "Content-Type: application/json" \
    -H "x-organization-id: $ORG_ID" \
    -X POST "$SUPERPLANE_URL/api/v1/service-accounts/$SA_ID/token")
  if [ "$token_status" != "200" ] && [ "$token_status" != "201" ]; then
    log "FAIL: regenerate-token returned $token_status"
    cat /tmp/token.json >&2 || true
    exit 1
  fi
  SA_TOKEN=$(jq -r '.token // .api_token // empty' /tmp/token.json)
fi

if [ -z "$SA_TOKEN" ]; then
  log "FAIL: no token in response"
  exit 1
fi
log "got API token (${#SA_TOKEN} chars)"

# --- 5. superplane connect ---------------------------------------------------
log "superplane connect $SUPERPLANE_URL"
superplane connect "$SUPERPLANE_URL" "$SA_TOKEN"
superplane whoami

# Export for child processes (runner inherits these).
export SUPERPLANE_URL
export SUPERPLANE_API_TOKEN="$SA_TOKEN"
export SUPERPLANE_ORGANIZATION_ID="$ORG_ID"

log "bootstrap complete"
