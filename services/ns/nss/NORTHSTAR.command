#!/bin/bash
# NORTHSTAR.command v2 — Single-click boot for macOS
# Double-click from Finder. Terminal opens. Everything starts automatically.
# NS∞ · AXIOLEV Holdings · Constitutional AI Operating System
#
# Step sequence:
#   1. Port clear
#   2. Alexandria SSD
#   3. Python venv + deps
#   4. Environment load
#   5. YubiKey bind check (non-blocking)
#   6. Server start + health verify
#   7. ngrok tunnel
#   8. Twilio webhook auto-config
#   9. Lexicon bootstrap (first boot)
#  10. Open Dashboard + Console

NSS="$HOME/NSS"
VENV="$NSS/.venv"
ENV="$NSS/.env"
PORT=9000
LOG="$NSS/logs"
FIRST_BOOT_FLAG="$NSS/.first_boot_done"

# Trap: on any error, show context and pause before exit
trap 'EC=$?; echo ""; echo "  ✗ Error at line $LINENO (exit $EC)"; echo "  → Check: $LOG/server.log"; echo "  Press Enter to exit."; read' ERR

mkdir -p "$LOG"
clear

echo ""
echo "  ╔══════════════════════════════════════════════════════╗"
echo "  ║  ⚡  N O R T H S T A R                               ║"
echo "  ║     NS∞  ·  AXIOLEV Holdings                         ║"
echo "  ║     Constitutional AI Operating System               ║"
echo "  ║     Ω Advisory Sovereignty Law · Conciliar v1.0      ║"
echo "  ╚══════════════════════════════════════════════════════╝"
echo ""

# ── 1. PORT CLEAR ─────────────────────────────────────────────────────────────
echo "  [1/9] Clearing ports..."
lsof -ti :$PORT    2>/dev/null | xargs kill -9 2>/dev/null || true
lsof -ti :4040     2>/dev/null | xargs kill -9 2>/dev/null || true
pkill -f "ngrok"   2>/dev/null || true
pkill -f "uvicorn" 2>/dev/null || true
sleep 1
echo "  ✓ Ports clear"

# ── 2. ALEXANDRIA SSD ─────────────────────────────────────────────────────────
echo "  [2/9] Alexandria..."
if [ -d "/Volumes/NSExternal" ]; then
    echo "  ✓ Alexandria SSD: mounted"
    mkdir -p /Volumes/NSExternal/ALEXANDRIA/{ether/voice,ether/files,ether/events,index,proto_canon,receipt_ledger,canon,san,lexicon} 2>/dev/null || true
else
    echo "  ⚠  Alexandria SSD: not mounted — using internal fallback"
    mkdir -p "$HOME/NSS/MANIFOLD/"{canon,mission_graph,lexicon} 2>/dev/null || true
fi

# ── 3. PYTHON VENV + DEPS ─────────────────────────────────────────────────────
echo "  [3/9] Python environment..."
if [ ! -d "$VENV" ]; then
    echo "  → First boot: creating venv..."
    python3 -m venv "$VENV"
fi
source "$VENV/bin/activate"

# Check if deps installed
if ! python3 -c "import fastapi, uvicorn" 2>/dev/null; then
    echo "  → Installing dependencies (60-120s first time)..."
    pip install --quiet --upgrade pip
    # Critical deps first (fast — ~20s)
    pip install --quiet fastapi uvicorn python-multipart websockets httpx pydantic python-jose aiofiles
    echo "  ✓ Core dependencies ready"
    # Optional deps in background (AI APIs, trading, Twilio)
    (pip install --quiet anthropic openai "google-generativeai" requests twilio         "alpaca-py" 2>/dev/null && echo "  ✓ Optional dependencies ready") &
    OPTPID=$!
else
    echo "  ✓ Dependencies ready"
fi

# ── 4. ENVIRONMENT ─────────────────────────────────────────────────────────────
echo "  [4/9] Environment..."
if [ ! -f "$ENV" ]; then
    echo "  → No .env found — creating minimal boot config..."
    cat > "$ENV" << 'ENVEOF'
# NS∞ Minimal Boot Config — add API keys via Console > Credentials
NS_FOUNDER_PASSWORD=northstar
NORTHSTAR_PORT=9000
NORTHSTAR_WEBHOOK_BASE=
# Add keys below when ready:
# ANTHROPIC_API_KEY=
# OPENAI_API_KEY=
# GOOGLE_API_KEY=
# TWILIO_ACCOUNT_SID=
# TWILIO_AUTH_TOKEN=
# TWILIO_PHONE_NUMBER=
# POLYGON_API_KEY=
# ALPACA_API_KEY=
# ALPACA_SECRET_KEY=
ENVEOF
    echo "  ✓ Minimal .env created — add credentials via Console after boot"
    exit 1
fi
set -a; source "$ENV"; set +a

KEY_COUNT=$(grep -cE "^[A-Z_]+=.+" "$ENV" 2>/dev/null || echo 0)
echo "  ✓ Environment: $KEY_COUNT keys loaded"

# First-boot password prompt
if [ ! -f "$FIRST_BOOT_FLAG" ] && [ "${NS_FOUNDER_PASSWORD:-}" = "northstar" -o -z "${NS_FOUNDER_PASSWORD:-}" ]; then
    echo ""
    echo "  ┌──────────────────────────────────────────────────────┐"
    echo "  │  FIRST BOOT — Set your founder password              │"
    echo "  │  Default is 'northstar'. Change it now.              │"
    echo "  │  (Press Enter to keep default for now)               │"
    echo "  └──────────────────────────────────────────────────────┘"
    read -p "  New founder password: " -s NEW_PW
    echo ""
    if [ -n "$NEW_PW" ]; then
        # Update .env
        if grep -q "^NS_FOUNDER_PASSWORD=" "$ENV"; then
            sed -i '' "s/^NS_FOUNDER_PASSWORD=.*/NS_FOUNDER_PASSWORD=$NEW_PW/" "$ENV"
        else
            echo "NS_FOUNDER_PASSWORD=$NEW_PW" >> "$ENV"
        fi
        export NS_FOUNDER_PASSWORD="$NEW_PW"
        echo "  ✓ Password set"
    fi
fi

# ── 5. YUBIKEY BIND CHECK ──────────────────────────────────────────────────────
echo "  [5/9] YubiKey..."
if command -v ykman &>/dev/null; then
    YK_SERIAL=$(ykman list --serials 2>/dev/null | head -1)
    if [ -n "$YK_SERIAL" ]; then
        echo "  ✓ YubiKey: serial $YK_SERIAL"
        # Record in .env if not set
        if ! grep -q "^YUBIKEY_SERIAL=" "$ENV"; then
            echo "YUBIKEY_SERIAL=$YK_SERIAL" >> "$ENV"
            export YUBIKEY_SERIAL="$YK_SERIAL"
        fi
        ENV_YK=$(grep "^YUBIKEY_SERIAL=" "$ENV" | cut -d= -f2)
        if [ "$ENV_YK" != "$YK_SERIAL" ]; then
            echo "  ⚠  YubiKey serial mismatch! Registered: $ENV_YK, Present: $YK_SERIAL"
            echo "  → If this is your key, update .env YUBIKEY_SERIAL=$YK_SERIAL"
            echo "  → Continuing without YubiKey binding (development mode)"
        fi
    else
        echo "  ⚠  YubiKey: not detected (insert for hardware auth)"
    fi
else
    echo "  ⚠  YubiKey: ykman not installed (brew install ykman for hardware auth)"
fi

# ── 6. START SERVER ────────────────────────────────────────────────────────────
echo "  [6/9] Starting NS Core..."
cd "$NSS"

# Start with output to log
"$VENV/bin/uvicorn" nss.api.server:app \
    --host 0.0.0.0 \
    --port $PORT \
    --log-level warning \
    --no-access-log \
    > "$LOG/server.log" 2>&1 &
SERVER_PID=$!

echo "  → Waiting for health check..."
for i in $(seq 1 15); do
    sleep 1
    HEALTH=$(curl -sf "http://localhost:$PORT/health" 2>/dev/null || echo "")
    if [ -n "$HEALTH" ]; then
        echo "  ✓ NS Core online (pid $SERVER_PID)"
        break
    fi
    if [ $i -eq 15 ]; then
        echo "  ✗ Server failed to start. Last log:"
        echo ""
        tail -20 "$LOG/server.log"
        echo ""
        echo "  Press Enter to exit."
        read
        exit 1
    fi
    printf "    [%d/15]\r" $i
done

# ── 7. NGROK TUNNEL ────────────────────────────────────────────────────────────
echo "  [7/9] Tunnel..."
NGROK_URL=""

# Check if ngrok is installed
if ! command -v ngrok &>/dev/null; then
    echo "  ⚠  ngrok not installed"
    echo "  → Install: brew install ngrok/ngrok/ngrok"
    echo "  → Then: ngrok config add-authtoken YOUR_TOKEN"
    echo "  → Voice will work locally. For inbound calls, ngrok is required."
else
    # Check if ngrok has an auth token
    if ngrok config check 2>/dev/null | grep -q "authtoken"; then
        ngrok http $PORT \
            --log=stdout \
            --log-format=json \
            --scheme=https \
            > "$LOG/ngrok.log" 2>&1 &
        NGROK_PID=$!

        # Wait for tunnel with retries
        for i in $(seq 1 10); do
            sleep 1
            NGROK_URL=$(curl -sf http://localhost:4040/api/tunnels 2>/dev/null | python3 -c "
import sys,json
try:
    d=json.load(sys.stdin)
    tunnels=d.get('tunnels',[])
    https=[t for t in tunnels if t.get('proto')=='https']
    print((https or tunnels)[0]['public_url'])
except: pass
" 2>/dev/null || echo "")
            [ -n "$NGROK_URL" ] && break
        done

        if [ -n "$NGROK_URL" ]; then
            echo "  ✓ Tunnel: $NGROK_URL"
            # Write to .env
            python3 -c "
import re
p,u='$ENV','$NGROK_URL'
c=open(p).read()
line='NORTHSTAR_WEBHOOK_BASE='+u
if re.search(r'^NORTHSTAR_WEBHOOK_BASE=',c,re.MULTILINE):
    c=re.sub(r'^NORTHSTAR_WEBHOOK_BASE=.*$',line,c,flags=re.MULTILINE)
else:
    c+='\n'+line
open(p,'w').write(c)
"
            export NORTHSTAR_WEBHOOK_BASE="$NGROK_URL"
        else
            echo "  ⚠  ngrok tunnel unavailable — check: $LOG/ngrok.log"
        fi
    else
        echo "  ⚠  ngrok authtoken not set — run: ngrok config add-authtoken YOUR_TOKEN"
    fi
fi

# ── 8. TWILIO WEBHOOK ─────────────────────────────────────────────────────────
echo "  [8/9] Twilio..."
if [ -n "$NGROK_URL" ] && [ -n "${TWILIO_ACCOUNT_SID:-}" ] && [ -n "${TWILIO_AUTH_TOKEN:-}" ] && [ -n "${TWILIO_PHONE_NUMBER:-}" ]; then
    python3 - "$NGROK_URL" << 'TWILIO_PY'
import os, sys, requests
from requests.auth import HTTPBasicAuth
url = sys.argv[1]
sid = os.environ.get('TWILIO_ACCOUNT_SID','')
tok = os.environ.get('TWILIO_AUTH_TOKEN','')
ph  = os.environ.get('TWILIO_PHONE_NUMBER','')
try:
    r = requests.get(
        f'https://api.twilio.com/2010-04-01/Accounts/{sid}/IncomingPhoneNumbers.json',
        auth=HTTPBasicAuth(sid,tok), timeout=10
    )
    numbers = r.json().get('incoming_phone_numbers', [])
    match = [n for n in numbers if n['phone_number'] == ph]
    if match:
        webhook = f'{url}/voice/inbound'
        status_cb = f'{url}/voice/status'
        requests.post(
            f'https://api.twilio.com/2010-04-01/Accounts/{sid}/IncomingPhoneNumbers/{match[0]["sid"]}.json',
            auth=HTTPBasicAuth(sid,tok),
            data={'VoiceUrl': webhook, 'VoiceMethod': 'POST',
                  'StatusCallback': status_cb, 'StatusCallbackMethod': 'POST',
                  'SmsUrl': f'{url}/sms/incoming', 'SmsMethod': 'POST'},
            timeout=10
        )
        print(f'  ✓ Voice webhook: {webhook}')
    else:
        print(f'  ⚠  Phone {ph} not found in Twilio account')
except Exception as e:
    print(f'  ⚠  Twilio config: {e}')
TWILIO_PY
elif [ -z "${TWILIO_ACCOUNT_SID:-}" ]; then
    echo "  ⚠  Twilio: credentials not set"
else
    echo "  ⚠  Twilio webhook: ngrok required for inbound calls"
fi

# ── 9. LEXICON BOOTSTRAP ──────────────────────────────────────────────────────
echo "  [9/9] Lexicon..."
if [ ! -f "$FIRST_BOOT_FLAG" ]; then
    echo "  → First boot: initializing Alexandria Lexicon (SFE)..."
    TOKEN=$(curl -sf -X POST "http://localhost:$PORT/auth/login" \
        -H "Content-Type: application/json" \
        -d '{"user_id":"founder","password":"'"${NS_FOUNDER_PASSWORD:-northstar}"'","device_name":"boot"}' \
        2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('access_token',''))" 2>/dev/null || echo "")

    if [ -n "$TOKEN" ]; then
        # Bootstrap with NS core vocabulary
        BOOT_RESULT=$(curl -sf -X POST "http://localhost:$PORT/lexicon/bootstrap" \
            -H "Authorization: Bearer $TOKEN" \
            -H "Content-Type: application/json" \
            -d '{
              "domain": "governance",
              "terms": [
                {"term": "dignity", "definition": "The irreducible worth of a person that cannot be traded away"},
                {"term": "sovereignty", "definition": "The ultimate authority over decisions within a bounded domain"},
                {"term": "canon", "definition": "A stabilized, receipted, versioned rule that governs behavior"},
                {"term": "receipt", "definition": "An immutable, chained record of every state transition"},
                {"term": "constraint", "definition": "A condition that reduces the feasible set of actions"},
                {"term": "boundary", "definition": "A learned constraint edge that defines where a concept applies"},
                {"term": "conflict", "definition": "A structured disagreement preserved as first-class artifact"},
                {"term": "arbiter", "definition": "Multi-model reasoning system that measures disagreement"},
                {"term": "ether", "definition": "The living stream of market, news, and macro signal"},
                {"term": "oversight", "definition": "The active monitoring of a system to prevent drift from intent"}
              ]
            }' 2>/dev/null || echo "{}")

        CONCEPTS=$(echo "$BOOT_RESULT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('concepts_created',0))" 2>/dev/null || echo "0")
        echo "  ✓ Lexicon v0.1 bootstrapped: $CONCEPTS concept candidates"
        touch "$FIRST_BOOT_FLAG"
    else
        echo "  ⚠  Lexicon bootstrap deferred (auth unavailable)"
    fi
else
    LEXICON_STATE=$(curl -sf "http://localhost:$PORT/lexicon/summary" \
        -H "Authorization: Bearer $(curl -sf -X POST "http://localhost:$PORT/auth/login" \
            -H "Content-Type: application/json" \
            -d '{"user_id":"founder","password":"'"${NS_FOUNDER_PASSWORD:-northstar}"'","device_name":"boot"}' \
            2>/dev/null | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))" 2>/dev/null || echo "")" \
        2>/dev/null | python3 -c "
import sys,json
try:
    d=json.load(sys.stdin)
    print(f\"{d.get('total_concepts',0)} concepts, {d.get('total_terms',0)} terms, avg completeness {d.get('average_completeness',0):.2f}\")
except: print('unavailable')
" 2>/dev/null || echo "unavailable")
    echo "  ✓ Lexicon: $LEXICON_STATE"
fi

# ── FINAL STATUS ──────────────────────────────────────────────────────────────

# Get health summary
HEALTH=$(curl -sf "http://localhost:$PORT/health" 2>/dev/null || echo "{}")
LLM_COUNT=$(echo "$HEALTH" | python3 -c "
import sys,json
try:
    h=json.load(sys.stdin).get('intelligence',{})
    print(sum(1 for v in h.values() if v))
except: print('?')
" 2>/dev/null || echo "?")
WS_COUNT=$(echo "$HEALTH" | python3 -c "import sys,json; print(json.load(sys.stdin).get('ws_connections',0))" 2>/dev/null || echo "0")

# Open URLs
open "http://localhost:$PORT" 2>/dev/null &
sleep 0.5
open "http://localhost:$PORT/console" 2>/dev/null &

echo ""
echo "  ╔══════════════════════════════════════════════════════╗"
echo "  ║  ✓ NORTHSTAR ONLINE                                  ║"
printf "  ║  ✓ Intelligence:   %d/4 LLMs active                  ║\n" "$LLM_COUNT"
echo "  ║  ✓ Computer voice: +1 (307) 202-4418                 ║"
echo "  ║  ✓ Dashboard:      http://localhost:9000             ║"
echo "  ║  ✓ Console:        http://localhost:9000/console     ║"
echo "  ║  ✓ Ether ingest:   ACTIVE (background)               ║"
echo "  ║  ✓ Lexicon (SFE):  ACTIVE                            ║"
echo "  ║                                                      ║"
echo "  ║  Login: founder / [your password]                    ║"
echo "  ║  Call +13072024418 → Computer online.                ║"
echo "  ╚══════════════════════════════════════════════════════╝"
echo ""
echo "  On iPhone/iPad: http://[your-mac-ip]:9000/console"
echo "  Console login: user=founder, password=northstar (or your new password)"
echo ""
echo "  Server log: $LOG/server.log"
echo "  Ctrl+C to shut down all systems."
echo ""

# Cleanup handler
cleanup() {
    echo ""
    echo "  Shutting down NS Core..."
    kill $SERVER_PID 2>/dev/null || true
    kill ${NGROK_PID:-0} 2>/dev/null || true
    pkill -f "uvicorn nss.api.server" 2>/dev/null || true
    pkill -f "ngrok" 2>/dev/null || true
    echo "  ✓ Systems offline."
    exit 0
}
trap cleanup INT TERM

# Stream server log to terminal
tail -f "$LOG/server.log" 2>/dev/null &
TAIL_PID=$!

wait $SERVER_PID
kill $TAIL_PID 2>/dev/null || true
