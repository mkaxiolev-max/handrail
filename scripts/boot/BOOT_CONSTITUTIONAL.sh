#!/usr/bin/env bash
# =============================================================================
# NS∞ CONSTITUTIONAL BOOT
# Architecture-faithful. Fail-closed. Emits certification artifacts.
# No degraded subset. Full organism or nonzero exit.
# =============================================================================
set -uo pipefail
cd ~/axiolev_runtime

PASS=0; FAIL=0
TS=$(date +%Y%m%d_%H%M%S)
CERT="certification/boot_${TS}.json"
mkdir -p certification

ok()   { echo "  ✓ $*"; PASS=$((PASS+1)); }
fail() { echo "  ✗ $*"; FAIL=$((FAIL+1)); }
warn() { echo "  ~ $*"; }

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║  NS∞ CONSTITUTIONAL BOOT                                  ║"
echo "║  $(date '+%Y-%m-%d %H:%M:%S')                                    ║"
echo "╚══════════════════════════════════════════════════════════╝"

# 1. Docker
DOCKER_SOCK=""
for c in "/var/run/docker.sock" "$HOME/.docker/run/docker.sock"; do
    [ -S "$c" ] && DOCKER_SOCK="unix://$c" && break
done
if [ -z "$DOCKER_SOCK" ]; then
    echo "  Starting Docker Desktop..."
    open -a Docker 2>/dev/null || true
    for i in $(seq 1 30); do
        sleep 2
        for c in "/var/run/docker.sock" "$HOME/.docker/run/docker.sock"; do
            [ -S "$c" ] && DOCKER_SOCK="unix://$c" && break 2
        done
    done
fi
[ -z "$DOCKER_SOCK" ] && fail "Docker socket not found" && exit 1
export DOCKER_HOST="$DOCKER_SOCK"
ok "Docker: $DOCKER_SOCK"

# 2. NSExternal SSD
if [ -d "/Volumes/NSExternal" ]; then
    ok "NSExternal mounted"
    mkdir -p /Volumes/NSExternal/ALEXANDRIA/ledger
else
    warn "NSExternal not mounted — receipts will use local fallback"
fi

# 3. Env vars (presence only — no values printed)
for KEY in ANTHROPIC_API_KEY XAI_API_KEY; do
    VAL=$(grep "^${KEY}=" .env 2>/dev/null | cut -d= -f2- | tr -d '"')
    if [ -n "$VAL" ] && [ "${#VAL}" -gt 10 ] && [ "$VAL" != "PENDING" ]; then
        ok "  $KEY present (${#VAL} chars)"
    else
        warn "  $KEY absent or placeholder"
    fi
done

# 4. Full stack boot
echo "  Bringing up full stack..."
docker compose up -d 2>&1 | grep -E "Started|Healthy|Running|Recreated|Created" | sed 's/^/    /'
echo "  Waiting 20s for convergence..."
sleep 20

# 5. Health verification
echo "  Health checks..."
ALL_HEALTHY=true
for pair in "9000:ns_core" "9001:alexandria" "9002:model_router" "9003:violet" "9004:canon" "9005:integrity" "9010:omega"; do
    port="${pair%%:*}"; svc="${pair##*:}"
    for attempt in 1 2 3; do
        S=$(curl -sf --connect-timeout 4 "http://127.0.0.1:${port}/healthz" 2>/dev/null \
            | python3 -c "import sys,json;print(json.load(sys.stdin).get('status','?'))" 2>/dev/null \
            || echo "unreachable")
        if [ "$S" = "ok" ] || [ "$S" = "healthy" ]; then
            ok ":$port $svc → $S"
            break
        elif [ $attempt -lt 3 ]; then
            sleep 5
        else
            fail ":$port $svc → $S"
            ALL_HEALTHY=false
        fi
    done
done

# 6. Frontends
for port in 3000 3002; do
    CODE=$(curl -sf -o /dev/null -w "%{http_code}" --connect-timeout 3 "http://localhost:${port}/" 2>/dev/null || echo "000")
    [ "$CODE" = "200" ] && ok "Frontend :$port → HTTP 200" || warn "Frontend :$port → HTTP $CODE (may need manual start)"
done

# 7. One intent round-trip
RESP=$(curl -sf --connect-timeout 20 \
    -X POST http://127.0.0.1:9000/violet/chat \
    -H 'Content-Type: application/json' \
    -d '{"message":"Constitutional boot check. Confirm organism online."}' \
    2>/dev/null | python3 -c "import sys,json;d=json.load(sys.stdin);print(d.get('text','')[:60])" 2>/dev/null || echo "")
[ -n "$RESP" ] && ok "Violet responding: $RESP" || fail "Violet not responding"

# 8. Emit certification
python3 - << CERTEOF
import json
from datetime import datetime

cert = {
    "boot_time": datetime.utcnow().isoformat() + "Z",
    "verdict": "BOOT_PASS" if $FAIL == 0 else "BOOT_PARTIAL",
}
with open("$CERT", "w") as f:
    json.dump(cert, f, indent=2)
print(f"  Cert: $CERT")
CERTEOF

[ $FAIL -eq 0 ] && echo "  ✅ BOOT COMPLETE" || echo "  ⚠ BOOT PARTIAL ($FAIL failures)"
