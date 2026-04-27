#!/usr/bin/env bash
# Bootstrap a fresh superplane-demo instance and hand off a working CLI session.
#
# Runs inside the eval container against the freshly-booted superplane service.
# Three steps, all against the documented response shapes:
#   1. POST /api/v1/setup-owner       → { organization_id }, sets session cookie
#   2. POST /api/v1/service-accounts  → { serviceAccount: { id }, token }
#      with x-organization-id header (per web_src/src/lib/withOrganizationHeader.ts)
#   3. superplane connect             → persists ~/.superplane/config.yaml
#
# 409 from setup-owner is a real bug here (we run with tmpfs); we fail fast.
set -euo pipefail

: "${SUPERPLANE_URL:?SUPERPLANE_URL must be set (e.g. http://superplane:3000)}"

OWNER_EMAIL="${EVAL_OWNER_EMAIL:-eval@evals.local}"
OWNER_PASSWORD="${EVAL_OWNER_PASSWORD:-Password1}"
SA_NAME="${EVAL_SA_NAME:-skills-evals}"
COOKIE_JAR="$(mktemp -t sp-cookies.XXXXXX)"
trap 'rm -f "$COOKIE_JAR"' EXIT

log() { echo "[bootstrap] $*" >&2; }
fail() { log "FAIL: $*"; [ -n "${1:-}" ] && cat "$1" >&2 2>/dev/null || true; exit 1; }

# --- 1. wait for readiness --------------------------------------------------
log "waiting for $SUPERPLANE_URL ..."
for i in $(seq 1 120); do
  if curl -fsS --max-time 2 "$SUPERPLANE_URL/" >/dev/null 2>&1; then
    log "up after ${i}s"
    break
  fi
  [ "$i" = 120 ] && fail "$SUPERPLANE_URL did not become ready in 120s"
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

case "$setup_status" in
  200|201) ;;
  *) fail "setup-owner returned $setup_status"; cat /tmp/setup.json >&2 || true; exit 1 ;;
esac

ORG_ID=$(jq -r '.organization_id' /tmp/setup.json)
[ -n "$ORG_ID" ] && [ "$ORG_ID" != "null" ] || fail "no organization_id in setup response"
log "organization_id=$ORG_ID"

# --- 3. create service account ----------------------------------------------
# Scoped endpoints require x-organization-id (see web_src/src/lib/withOrganizationHeader.ts).
sa_payload=$(printf '{"name":"%s","description":"Used by skill evals","role":"org_admin"}' "$SA_NAME")
log "POST /api/v1/service-accounts (name=$SA_NAME)"
sa_status=$(curl -sS -o /tmp/sa.json -w "%{http_code}" \
  -b "$COOKIE_JAR" \
  -H "Content-Type: application/json" \
  -H "x-organization-id: $ORG_ID" \
  -X POST "$SUPERPLANE_URL/api/v1/service-accounts" \
  -d "$sa_payload")

case "$sa_status" in
  200|201) ;;
  *) fail "create service-account returned $sa_status"; cat /tmp/sa.json >&2 || true; exit 1 ;;
esac

# Response shape: { serviceAccount: { id, ... }, token: "..." }
SA_ID=$(jq -r '.serviceAccount.id' /tmp/sa.json)
SA_TOKEN=$(jq -r '.token' /tmp/sa.json)
[ -n "$SA_ID" ]    && [ "$SA_ID" != "null" ]    || fail "no serviceAccount.id in response"
[ -n "$SA_TOKEN" ] && [ "$SA_TOKEN" != "null" ] || fail "no token in response"
log "service_account_id=$SA_ID"
log "got API token (${#SA_TOKEN} chars)"

# --- 4. superplane connect ---------------------------------------------------
log "superplane connect $SUPERPLANE_URL"
superplane connect "$SUPERPLANE_URL" "$SA_TOKEN"
superplane whoami

export SUPERPLANE_URL
export SUPERPLANE_API_TOKEN="$SA_TOKEN"
export SUPERPLANE_ORGANIZATION_ID="$ORG_ID"

log "bootstrap complete"
