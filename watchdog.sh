#!/usr/bin/env bash
# Copyright © 2026 Axiolev. All rights reserved.
# NS∞ Watchdog — service health monitor
# Checks handrail, ns, continuum every 60s. Auto-restarts unhealthy containers.
# Logs to /Volumes/NSExternal/ALEXANDRIA/ledger/watchdog.log

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Load env
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs 2>/dev/null) || true
fi

# Docker socket for macOS
if [ -S "/Users/${USER}/.docker/run/docker.sock" ]; then
  export DOCKER_HOST="unix:///Users/${USER}/.docker/run/docker.sock"
fi

LOG_DIR="/Volumes/NSExternal/ALEXANDRIA/ledger"
LOG_FILE="$LOG_DIR/watchdog.log"
INTERVAL=60

HANDRAIL_URL="http://localhost:8011/healthz"
NS_URL="http://localhost:9000/healthz"
CONTINUUM_URL="http://localhost:8788/state"

mkdir -p "$LOG_DIR"

log() {
  echo "[$(date -u '+%Y-%m-%dT%H:%M:%SZ')] $*" | tee -a "$LOG_FILE"
}

check_service() {
  local name="$1" url="$2" container="$3"
  local code
  code=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 3 --max-time 5 "$url" 2>/dev/null || echo "000")
  if [ "$code" = "200" ]; then
    return 0
  fi
  log "UNHEALTHY: $name ($url returned $code) — restarting $container"
  docker-compose restart "$container" >> "$LOG_FILE" 2>&1 && log "RESTARTED: $container" || log "RESTART FAILED: $container"
  return 1
}

log "Watchdog started (interval=${INTERVAL}s)"

while true; do
  check_service "handrail" "$HANDRAIL_URL" "handrail" || true
  check_service "ns"       "$NS_URL"       "ns"       || true
  check_service "continuum" "$CONTINUUM_URL" "continuum" || true
  sleep "$INTERVAL"
done
