#!/usr/bin/env bash
# NS∞ Founder Boot — double-click or run directly
# Idempotent. Safe to run repeatedly.
set -euo pipefail

export DOCKER_HOST="unix://$HOME/.docker/run/docker.sock"
REPO=~/axiolev_runtime
cd "$REPO"

# ── Docker check — wait up to 90s (needed when launched via launchd at login) ─
_wait_docker() {
    local i=0
    while ! docker info >/dev/null 2>&1; do
        i=$((i+1))
        if [ $i -ge 90 ]; then
            echo "[ERROR] Docker not reachable after 90s. Start Docker Desktop first."
            exit 1
        fi
        printf "\r  waiting for Docker (%d/90)..." "$i"
        sleep 1
    done
    [ $i -gt 0 ] && echo ""
}
_wait_docker

# ── Compose up ──────────────────────────────────────────────────────────────
echo "[BOOT] docker compose up -d..."
docker compose up -d

# ── state_api (host process) ─────────────────────────────────────────────────
if ! curl -sf http://127.0.0.1:9090/state >/dev/null 2>&1; then
    echo "[BOOT] Starting state_api on :9090..."
    nohup /opt/homebrew/bin/python3 "$REPO/state_api.py" \
        > /tmp/ns_state_api.log 2>&1 &
    disown
fi

# ── Wait helper ──────────────────────────────────────────────────────────────
_wait() {
    local url=$1 name=$2 retries=40
    for i in $(seq 1 $retries); do
        curl -sf "$url" >/dev/null 2>&1 && return 0
        printf "\r  waiting %s (%d/%d)..." "$name" "$i" "$retries"
        sleep 1
    done
    echo ""
    echo "[FAIL] $name did not respond at $url after ${retries}s"
    return 1
}

echo "[BOOT] Waiting for services..."
_wait http://127.0.0.1:9000/healthz    "ns_core"
_wait http://127.0.0.1:9090/state      "state_api"
_wait http://127.0.0.1:8011/healthz    "handrail"
_wait http://127.0.0.1:8788/state      "continuum"

# ── Summary ──────────────────────────────────────────────────────────────────
BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
SHA=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
STATE=$(curl -sf http://127.0.0.1:9090/state 2>/dev/null \
    | /opt/homebrew/bin/python3 -c \
        "import sys,json; d=json.load(sys.stdin); print(d.get('state','LIVE'))" \
    2>/dev/null || echo "LIVE")
ALEX=$([ -d /Volumes/NSExternal ] && echo "MOUNTED" || echo "not mounted")

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║        NS∞  FOUNDER READY+ MAX           ║"
echo "╠══════════════════════════════════════════╣"
printf "║  ns_core     %-28s║\n" "live :9000"
printf "║  state_api   %-28s║\n" "$STATE  :9090"
printf "║  handrail    %-28s║\n" "live :8011"
printf "║  continuum   %-28s║\n" "live :8788"
printf "║  alexandria  %-28s║\n" "$ALEX"
printf "║  branch      %-28s║\n" "$BRANCH"
printf "║  sha         %-28s║\n" "$SHA"
echo "╚══════════════════════════════════════════╝"

# ── Open UI in order ─────────────────────────────────────────────────────────
MAIN="http://127.0.0.1:3000"
ORGANISM="http://127.0.0.1:3000/organism"
OMEGA="http://127.0.0.1:3000/omega"

echo ""
echo "[UI] Opening main UI..."
open "$MAIN" 2>/dev/null || true
sleep 2

# Organism — only if frontend responds
if curl -sf --max-time 2 "$ORGANISM" >/dev/null 2>&1; then
    echo "[UI] Opening organism page..."
    open "$ORGANISM" 2>/dev/null || true
    sleep 1
fi

# Omega — only after main UI confirmed reachable
if curl -sf --max-time 3 "$MAIN" >/dev/null 2>&1; then
    echo "[UI] Opening omega page..."
    open "$OMEGA" 2>/dev/null || true
else
    echo "[UI] :3000 not reachable — omega tab skipped"
fi

echo ""
echo "NS∞ is live.  AXIOLEV HOLDINGS LLC — DIGNITY PRESERVED"
