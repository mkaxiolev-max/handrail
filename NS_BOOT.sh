#!/usr/bin/env bash
# NS∞ ONE-CLICK FOUNDER BOOT
# Usage: ./NS_BOOT.sh
set -euo pipefail

BOLD='\033[1m'
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
RESET='\033[0m'

ok()   { echo -e "  ${GREEN}✓${RESET} $1"; }
fail() { echo -e "  ${RED}✗${RESET} $1"; }
info() { echo -e "  ${CYAN}→${RESET} $1"; }
warn() { echo -e "  ${YELLOW}!${RESET} $1"; }

echo ""
echo -e "${BOLD}╔══════════════════════════════════════╗${RESET}"
echo -e "${BOLD}║      NS∞ FOUNDER BOOT SEQUENCE       ║${RESET}"
echo -e "${BOLD}╚══════════════════════════════════════╝${RESET}"
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ── Step 1: Docker check ──────────────────────────────────────────────────────
echo -e "${BOLD}[1/6] Docker check${RESET}"
DOCKER_HOST="unix:///Users/${USER}/.docker/run/docker.sock"
export DOCKER_HOST

if docker info >/dev/null 2>&1; then
    ok "Docker daemon running"
else
    fail "Docker daemon not running — start Docker Desktop and retry"
    exit 1
fi

# ── Step 2: SSD mount check ───────────────────────────────────────────────────
echo -e "${BOLD}[2/6] SSD mount check${RESET}"
if [ -d "/Volumes/NSExternal/ALEXANDRIA" ]; then
    ok "NSExternal SSD mounted at /Volumes/NSExternal"
else
    warn "NSExternal not mounted — using ~/ALEXANDRIA fallback"
    mkdir -p ~/ALEXANDRIA
fi

# ── Step 3: Compose up ───────────────────────────────────────────────────────
echo -e "${BOLD}[3/6] Starting containers${RESET}"
info "Running docker compose up -d --build"
if docker compose up -d --build 2>&1 | tail -5; then
    ok "Compose up complete"
else
    fail "docker compose up failed — check logs"
    exit 1
fi

# ── Step 4: Health wait ───────────────────────────────────────────────────────
echo -e "${BOLD}[4/6] Waiting for services${RESET}"
SERVICES=(
    "ns_core:9000:/healthz"
    "alexandria:9001:/atoms/healthz"
    "handrail:8011:/healthz"
)

wait_healthy() {
    local name="$1" port="$2" path="$3"
    local tries=0 max=30
    while [ $tries -lt $max ]; do
        if curl -sf "http://127.0.0.1:${port}${path}" >/dev/null 2>&1; then
            ok "$name (port $port) healthy"
            return 0
        fi
        tries=$((tries + 1))
        sleep 2
    done
    fail "$name (port $port) not healthy after ${max} retries"
    return 1
}

ALL_HEALTHY=true
for svc in "${SERVICES[@]}"; do
    IFS=: read -r name port path <<< "$svc"
    wait_healthy "$name" "$port" "$path" || ALL_HEALTHY=false
done

if [ "$ALL_HEALTHY" = false ]; then
    fail "Some services not healthy — check: docker compose logs"
    exit 1
fi

# ── Step 5: Endpoint verify ───────────────────────────────────────────────────
echo -e "${BOLD}[5/6] Endpoint verification${RESET}"
check_endpoint() {
    local label="$1" url="$2"
    local result
    result=$(curl -sf "$url" 2>/dev/null) || { fail "$label — no response"; return; }
    local status
    status=$(echo "$result" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('status','?'))" 2>/dev/null || echo "?")
    if [ "$status" = "ok" ] || [ "$status" = "DEGRADED" ]; then
        ok "$label → status=$status"
    else
        warn "$label → status=$status"
    fi
}

check_endpoint "ns_core /healthz"      "http://127.0.0.1:9000/healthz"
check_endpoint "ns_core /system/now"   "http://127.0.0.1:9000/system/now"
check_endpoint "ns_core /violet/isr"   "http://127.0.0.1:9000/violet/isr"
check_endpoint "alexandria /atoms/healthz" "http://127.0.0.1:9001/atoms/healthz"

# ── Step 6: DB health ─────────────────────────────────────────────────────────
echo -e "${BOLD}[6/6] DB health${RESET}"
DB_COUNTS=$(curl -sf "http://127.0.0.1:9000/system/now" 2>/dev/null | \
    python3 -c "import sys,json; d=json.load(sys.stdin); m=d.get('memory',{}); print(f\"atoms={m.get('atoms',0)} edges={m.get('edges',0)} receipts={m.get('receipts',0)}\")" 2>/dev/null || echo "unavailable")
ok "DB counts: $DB_COUNTS"

GIT_BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
GIT_HASH=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
ok "Git: branch=$GIT_BRANCH hash=$GIT_HASH"

echo ""
echo -e "${BOLD}${GREEN}╔══════════════════════════════════════╗${RESET}"
echo -e "${BOLD}${GREEN}║       NS∞ BOOT COMPLETE              ║${RESET}"
echo -e "${BOLD}${GREEN}╚══════════════════════════════════════╝${RESET}"
echo ""
echo -e "  Violet:     ${CYAN}http://127.0.0.1:3000${RESET}"
echo -e "  NS Core:    ${CYAN}http://127.0.0.1:9000${RESET}"
echo -e "  Alexandria: ${CYAN}http://127.0.0.1:9001${RESET}"
echo -e "  Handrail:   ${CYAN}http://127.0.0.1:8011${RESET}"
echo ""
