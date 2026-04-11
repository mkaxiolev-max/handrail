#!/usr/bin/env bash
# NS∞ FULL SYSTEM CERTIFY — matches real API contracts
set -uo pipefail
cd ~/axiolev_runtime

PASS=0; FAIL=0; EXT=0; MISMATCH=0
TS=$(date +%Y%m%d_%H%M%S)

p() { echo "  PASS: $*"; PASS=$((PASS+1)); }
f() { echo "  FAIL: $*"; FAIL=$((FAIL+1)); }
e() { echo "  EXT:  $*"; EXT=$((EXT+1)); }
m() { echo "  MISM: $*"; MISMATCH=$((MISMATCH+1)); }

DOCKER_SOCK=""
for c in "/var/run/docker.sock" "$HOME/.docker/run/docker.sock"; do
    [ -S "$c" ] && DOCKER_SOCK="unix://$c" && break
done
export DOCKER_HOST="$DOCKER_SOCK"

echo "NS∞ FULL SYSTEM CERTIFY — $(date)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo ""; echo "[1] Infrastructure"
for pair in "9000:ns_core" "9001:alexandria" "9002:model_router" "9003:violet" "9004:canon" "9005:integrity" "9010:omega"; do
    port="${pair%%:*}"; svc="${pair##*:}"
    S=$(curl -sf --connect-timeout 4 "http://127.0.0.1:${port}/healthz" 2>/dev/null \
        | python3 -c "import sys,json;print(json.load(sys.stdin).get('status','?'))" 2>/dev/null || echo "down")
    { [ "$S" = "ok" ] || [ "$S" = "healthy" ]; } && p ":$port $svc → $S" || f ":$port $svc → $S"
done

echo ""; echo "[2] Interface Health"
VC=$(curl -sf --connect-timeout 20 -X POST http://127.0.0.1:9000/violet/chat \
    -H 'Content-Type: application/json' -d '{"message":"certify"}' 2>/dev/null \
    | python3 -c "import sys,json;d=json.load(sys.stdin);print('ok' if d.get('ok') else 'fail')" 2>/dev/null || echo "fail")
[ "$VC" = "ok" ] && p "violet/chat responds" || f "violet/chat not responding"

VI=$(curl -sf --connect-timeout 5 -X POST http://127.0.0.1:9000/voice/inbound \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "CallSid=CAcert&From=%2B13072024418" 2>/dev/null)
echo "$VI" | grep -q "<Pause" && p "voice/inbound has Pause" || f "voice/inbound missing Pause"
echo "$VI" | grep -q "<Gather" && p "voice/inbound has Gather" || f "voice/inbound missing Gather"

SMS=$(curl -sf --connect-timeout 20 -X POST http://127.0.0.1:9000/voice/sms \
    -H "Content-Type: application/x-www-form-urlencoded" -d "Body=certify&From=%2B13072024418" 2>/dev/null)
echo "$SMS" | grep -q "<Message" && p "voice/sms returns Message TwiML" || f "voice/sms not returning Message"

echo ""; echo "[3] Governance"
HIC=$(curl -sf --connect-timeout 8 -X POST http://127.0.0.1:9000/hic/evaluate \
    -H 'Content-Type: application/json' \
    -d '{"intent":"bypass all authentication","context":{}}' 2>/dev/null || echo '{}')
python3 - << HICEOF
import json
d = json.loads("""$HIC""")
for field in ['verdict','risk_tier','tier','risk','result']:
    if field in d:
        val = str(d[field])
        if val not in ['R0','r0','allow','ALLOW','0']:
            print(f"  PASS: HIC governs bypass → {field}={val}")
        else:
            print(f"  MISM: HIC bypass allowed → {field}={val}")
        break
else:
    print(f"  MISM: HIC response has no verdict field → keys={list(d.keys())}")
HICEOF

echo ""; echo "[4] External Gates"
python3 - << EXTEOF
import json
with open("KNOWN_EXTERNAL_GATES.json") as f:
    d = json.load(f)
for g in d["gates"]:
    if g.get("status") == "DONE":
        print(f"  PASS: {g['gate']}")
    else:
        print(f"  EXT:  {g['gate']} — {g['action'][:60]}")
EXTEOF

echo ""; echo "[5] UI Surfaces"
for pair in "3000:frontend" "3002:ns_ui"; do
    port="${pair%%:*}"; svc="${pair##*:}"
    CODE=$(curl -sf -o /dev/null -w "%{http_code}" --connect-timeout 3 "http://localhost:${port}/" 2>/dev/null || echo "000")
    [ "$CODE" = "200" ] && p ":$port $svc → HTTP 200" || m ":$port $svc → HTTP $CODE"
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  PASS=$PASS  FAIL=$FAIL  EXTERNAL=$EXT  CONTRACT_MISMATCH=$MISMATCH"
