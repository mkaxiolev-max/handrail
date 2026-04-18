#!/usr/bin/env bash
# NS∞ Tauri boot helper — called by the native app at launch, non-interactive.
# Ensures Docker services + state_api are live. Logs to ~/Library/Logs/.
# Does NOT open browser tabs. Does NOT block the app window.
set -uo pipefail

export DOCKER_HOST="unix://$HOME/.docker/run/docker.sock"
REPO="$HOME/axiolev_runtime"
LOG="$HOME/Library/Logs/com.axiolev.ns-tauri-boot.log"
mkdir -p "$(dirname "$LOG")"

log() { echo "[$(date -u +%H:%M:%S)] $*" >> "$LOG"; }

log "=== ns_tauri_boot start ==="

# Alexandria must be present (Rust already checked, this is a belt-and-suspenders guard)
if [ ! -d "/Volumes/NSExternal" ]; then
    log "FATAL: /Volumes/NSExternal not mounted"
    exit 1
fi
log "Alexandria: mounted"

# Wait up to 90s for Docker
i=0
while ! docker info >/dev/null 2>&1; do
    i=$((i+1))
    if [ $i -ge 90 ]; then
        log "FATAL: Docker not reachable after 90s"
        exit 1
    fi
    sleep 1
done
log "Docker: reachable (waited ${i}s)"

# Compose up (idempotent)
cd "$REPO"
docker compose up -d >> "$LOG" 2>&1
log "docker compose up: done"

# Start state_api if not already live
if ! curl -sf http://127.0.0.1:9090/state >/dev/null 2>&1; then
    log "Starting state_api..."
    nohup /opt/homebrew/bin/python3 "$REPO/state_api.py" >> "$LOG" 2>&1 &
    disown
fi

# Wait for core services (up to 60s each)
_wait() {
    local url=$1 name=$2 n=0
    while ! curl -sf "$url" >/dev/null 2>&1; do
        n=$((n+1)); [ $n -ge 60 ] && log "WARN: $name not ready after 60s" && return 1
        sleep 1
    done
    log "$name: live (${n}s)"
}

_wait http://127.0.0.1:9000/healthz  "ns_core"
_wait http://127.0.0.1:9090/state    "state_api"
_wait http://127.0.0.1:8011/healthz  "handrail"
_wait http://127.0.0.1:8788/state    "continuum"

log "=== ns_tauri_boot complete ==="
