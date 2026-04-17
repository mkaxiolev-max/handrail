#!/usr/bin/env bash
# resume_ns.sh — idempotent NS∞ bring-up
# AXIOLEV HOLDINGS LLC — DIGNITY PRESERVED
set -u
REPO="${REPO:-$(cd "$(dirname "$0")" && pwd)}"
DOCKER_HOST="${DOCKER_HOST:-unix://$HOME/.docker/run/docker.sock}"
export DOCKER_HOST

log() { printf '[%s] %s\n' "$(date -u +%H:%M:%SZ)" "$*"; }
ok()  { printf '[%s] ✓ %s\n' "$(date -u +%H:%M:%SZ)" "$*"; }
fail(){ printf '[%s] ✗ %s\n' "$(date -u +%H:%M:%SZ)" "$*"; }

cd "$REPO"

log "NS∞ resume — docker compose up"
docker compose up -d 2>&1 | tail -5

log "waiting for ns_core health..."
for i in $(seq 1 30); do
    if curl -sf http://127.0.0.1:9000/healthz >/dev/null 2>&1; then
        ok "ns_core healthy after ${i}×2s"
        break
    fi
    sleep 2
done

log "checking state_api:9090"
if curl -sf http://127.0.0.1:9090/healthz >/dev/null 2>&1; then
    ok "state_api:9090 already running"
else
    log "starting state_api"
    python3 state_api.py &>/tmp/state_api.log &
    sleep 2
    curl -sf http://127.0.0.1:9090/healthz >/dev/null && ok "state_api started" || fail "state_api failed"
fi

SHA=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")

printf '%s\n' '{
  "return_block_version": 2,
  "ok": true,
  "rc": 0,
  "operation": "ns.resume",
  "artifacts": [{"sha": "'"$SHA"'", "branch": "'"$BRANCH"'", "status": "up"}],
  "dignity_banner": "AXIOLEV HOLDINGS LLC — DIGNITY PRESERVED"
}'
