#!/usr/bin/env bash
# =============================================================================
# NS∞ — FULL COLD BOOT
# Single command. Full organism. Architecture-faithful.
# AXIOLEV Holdings LLC · Wyoming, USA
# =============================================================================
set -uo pipefail
cd ~/axiolev_runtime

PASS=0; FAIL=0
ok()   { echo "  ✓ $*"; PASS=$((PASS+1)); }
fail() { echo "  ✗ $*"; FAIL=$((FAIL+1)); }
warn() { echo "  ~ $*"; }

echo ""
echo "╔══════════════════════════════════════════════════════════════════════════╗"
echo "║   NS∞ — FULL BOOT                                                        ║"
echo "║   $(date '+%Y-%m-%d %H:%M:%S')  ·  AXIOLEV Holdings LLC                          ║"
echo "╚══════════════════════════════════════════════════════════════════════════╝"
echo ""

# =============================================================================
# 1. DOCKER
# =============================================================================
echo "1. Docker..."
DOCKER_SOCK=""
for c in "/var/run/docker.sock" "$HOME/.docker/run/docker.sock" "$HOME/.docker/desktop/docker.sock"; do
    [ -S "$c" ] && DOCKER_SOCK="unix://$c" && break
done
if [ -z "$DOCKER_SOCK" ]; then
    warn "Docker not running — launching Docker Desktop..."
    open -a Docker 2>/dev/null || true
    for i in $(seq 1 30); do
        sleep 2
        for c in "/var/run/docker.sock" "$HOME/.docker/run/docker.sock"; do
            [ -S "$c" ] && DOCKER_SOCK="unix://$c" && break 2
        done
        [ $((i % 5)) -eq 0 ] && echo "  waiting for Docker... (${i}s)"
    done
fi
[ -z "$DOCKER_SOCK" ] && fail "Docker socket not found" && exit 1
export DOCKER_HOST="$DOCKER_SOCK"
ok "Docker: $DOCKER_SOCK"

# =============================================================================
# 2. NSEXTERNAL SSD
# =============================================================================
echo ""
echo "2. NSExternal SSD..."
if [ -d "/Volumes/NSExternal" ]; then
    ok "NSExternal mounted"
    mkdir -p /Volumes/NSExternal/ALEXANDRIA/ledger
else
    warn "NSExternal not mounted — receipts will use local fallback"
fi

# =============================================================================
# 3. ENV KEYS (presence only — no values printed)
# =============================================================================
echo ""
echo "3. API keys..."
for KEY in ANTHROPIC_API_KEY XAI_API_KEY OPENAI_API_KEY GOOGLE_API_KEY GROQ_API_KEY; do
    VAL=$(grep "^${KEY}=" .env 2>/dev/null | cut -d= -f2- | tr -d '"' | tr -d "'")
    if [ -n "$VAL" ] && [ "${#VAL}" -gt 10 ] && \
       [ "$VAL" != "PENDING" ] && [ "$VAL" != "sk-pending" ] && \
       [ "$VAL" != "YOUR_KEY_HERE" ]; then
        ok "$KEY present (${#VAL} chars)"
    else
        warn "$KEY absent or placeholder"
    fi
done

# =============================================================================
# 4. FULL STACK BOOT
# =============================================================================
echo ""
echo "4. Bringing up full stack..."
docker compose up -d 2>&1 \
    | grep -E "Started|Healthy|Running|Recreated|Created|Warning" \
    | grep -v "version is obsolete" \
    | sed 's/^/  /'

echo ""
echo "  Waiting for services to converge (25s)..."
sleep 25

# =============================================================================
# 5. HEALTH CHECKS (with retry)
# =============================================================================
echo ""
echo "5. Health checks..."
ALL_HEALTHY=true
for pair in "9000:ns_core" "9001:alexandria" "9002:model_router" "9003:violet" "9004:canon" "9005:integrity" "9010:omega"; do
    port="${pair%%:*}"; svc="${pair##*:}"
    HEALTHY=false
    for attempt in 1 2 3; do
        S=$(curl -sf --connect-timeout 5 "http://127.0.0.1:${port}/healthz" 2>/dev/null \
            | python3 -c "import sys,json;print(json.load(sys.stdin).get('status','?'))" 2>/dev/null \
            || echo "unreachable")
        if [ "$S" = "ok" ] || [ "$S" = "healthy" ]; then
            ok ":$port $svc"
            HEALTHY=true
            break
        fi
        [ $attempt -lt 3 ] && sleep 5
    done
    $HEALTHY || { fail ":$port $svc — $(docker compose logs $svc --tail=3 2>/dev/null | tail -1)"; ALL_HEALTHY=false; }
done

# =============================================================================
# 6. LLM PROVIDER STATUS
# =============================================================================
echo ""
echo "6. LLM providers..."
curl -sf --connect-timeout 5 http://127.0.0.1:9002/providers 2>/dev/null \
    | python3 -c "
import sys, json
d = json.load(sys.stdin)
for name, p in d.get('providers', {}).items():
    live = p.get('live', False)
    key  = p.get('key_present', False)
    model = p.get('primary_model', '?')
    local = ' [LOCAL]' if p.get('local') else ''
    mark = '✓' if live else ('~' if key else '✗')
    status = 'LIVE' if live else ('KEY_NEEDS_BILLING' if key else 'NO_KEY')
    print(f'  {mark} {name:12s} | {status:18s} | {model}{local}')
" 2>/dev/null || warn "model_router /providers unreachable"

# =============================================================================
# 7. VIOLET CHAT VERIFY
# =============================================================================
echo ""
echo "7. Violet intelligence check..."
VIOLET_RESP=$(curl -sf --connect-timeout 30 \
    -X POST http://127.0.0.1:9000/violet/chat \
    -H 'Content-Type: application/json' \
    -d '{"message":"Boot check. Confirm online and name your active provider."}' \
    2>/dev/null \
    | python3 -c "import sys,json;d=json.load(sys.stdin);print(d.get('text','')[:80])" \
    2>/dev/null || echo "")
[ -n "$VIOLET_RESP" ] && ok "Violet: $VIOLET_RESP" || fail "Violet not responding"

# =============================================================================
# 8. VOICE ROUTE VERIFY
# =============================================================================
echo ""
echo "8. Voice route check..."
VOICE=$(curl -sf --connect-timeout 8 \
    -X POST http://127.0.0.1:9000/voice/inbound \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "CallSid=CAboot&From=%2B13072024418&CallStatus=ringing" 2>/dev/null)
echo "$VOICE" | grep -q "<Response" && ok "voice/inbound → TwiML" || fail "voice/inbound not returning TwiML"
echo "$VOICE" | grep -q "<Pause"   && ok "  <Pause> present (loop-fix confirmed)" || warn "  <Pause> not found"
echo "$VOICE" | grep -q "<Gather"  && ok "  <Gather> present" || fail "  <Gather> missing"

# =============================================================================
# 9. FRONTENDS
# =============================================================================
echo ""
echo "9. Frontends..."

# Vite/React :3000
if curl -sf --connect-timeout 3 http://localhost:3000 &>/dev/null; then
    ok "Frontend :3000 already running"
else
    echo "  Starting React frontend..."
    cd frontend
    [ -d node_modules ] || npm install --silent 2>&1 | tail -2 | sed 's/^/  /'
    npm run dev > /tmp/ns_frontend.log 2>&1 &
    cd ~/axiolev_runtime
    sleep 6
    curl -sf --connect-timeout 4 http://localhost:3000 &>/dev/null \
        && ok "Frontend :3000 started" \
        || warn "Frontend :3000 still starting (check /tmp/ns_frontend.log)"
fi

# Next.js ns_ui :3002
if curl -sf --connect-timeout 3 http://localhost:3002 &>/dev/null; then
    ok "ns_ui :3002 already running"
else
    echo "  Starting ns_ui..."
    cd ns_ui
    [ -d node_modules ] || npm install --silent 2>&1 | tail -2 | sed 's/^/  /'
    npm run dev -- -p 3002 > /tmp/ns_ui.log 2>&1 &
    cd ~/axiolev_runtime
    sleep 8
    curl -sf --connect-timeout 4 http://localhost:3002 &>/dev/null \
        && ok "ns_ui :3002 started" \
        || warn "ns_ui :3002 still starting (check /tmp/ns_ui.log)"
fi

# =============================================================================
# 10. OPEN BROWSER TABS
# =============================================================================
echo ""
echo "10. Opening founder surfaces..."
sleep 1
open "http://localhost:3000/violet"   2>/dev/null || true
sleep 0.5
open "http://localhost:3002"          2>/dev/null || true
sleep 0.5
open "http://localhost:3000/briefing" 2>/dev/null || true
ok "Opened: /violet · Living Architecture · /briefing"

# =============================================================================
# FINAL REPORT
# =============================================================================
echo ""
echo "╔══════════════════════════════════════════════════════════════════════════╗"
echo "║   NS∞ BOOT COMPLETE                                                      ║"
echo "╠══════════════════════════════════════════════════════════════════════════╣"
echo "║                                                                          ║"
echo "║  SERVICES     ns_core · alexandria · model_router · violet              ║"
echo "║               canon · integrity · omega · postgres · redis              ║"
echo "║                                                                          ║"
echo "║  INTERFACES   :3000/violet    — Violet text chat                        ║"
echo "║               :3000/briefing  — Founder briefing                        ║"
echo "║               :3000/omega     — Omega simulation                        ║"
echo "║               :3002           — Living Architecture                     ║"
echo "║                                                                          ║"
echo "║  VOICE        +1 (307) 202-4418                                         ║"
echo "║  SMS          +1 (307) 202-4418 (webhook: ngrok/voice/sms)              ║"
echo "║                                                                          ║"
echo "║  RING STATUS  Rings 1-4: COMPLETE · Ring 5: EXTERNAL GATES              ║"
echo "║                                                                          ║"
echo "║  NEXT BOOT    bash ~/axiolev_runtime/NS_BOOT.sh                         ║"
echo "║                                                                          ║"
printf "║  Result: PASS=%-4s FAIL=%-4s                                           ║\n" "$PASS" "$FAIL"
echo "╚══════════════════════════════════════════════════════════════════════════╝"
echo ""

[ $FAIL -gt 0 ] && echo "  ⚠ $FAIL failure(s) — check above for details" && exit 1
exit 0
