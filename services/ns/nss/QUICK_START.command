#!/bin/bash
# NS∞ QUICK START — boots in < 2 min, no credentials required
# Full config: run NORTHSTAR.command after first boot
# ─────────────────────────────────────────────────────────────
clear
echo ""
echo "  ██████████████████████████████"
echo "  ██  NS∞  QUICK START         ██"
echo "  ██  Boot in < 2 min          ██"
echo "  ██████████████████████████████"
echo ""

NSS="$(cd "$(dirname "$0")" && pwd)"
VENV="$NSS/.venv"
LOG="$NSS/logs"
PORT=9000
ENV="$NSS/.env"

mkdir -p "$LOG"

# Trap for clean exit
cleanup() {
    [ -n "$SERVER_PID" ] && kill "$SERVER_PID" 2>/dev/null
    echo "  NS∞ stopped."
}
trap cleanup EXIT INT TERM

# ── 1. CLEAR PORT ──────────────────────────────────────────────────────────────
lsof -ti :$PORT 2>/dev/null | xargs kill -9 2>/dev/null || true
pkill -f "uvicorn nss" 2>/dev/null || true
sleep 0.5

# ── 2. MINIMAL ENV (if not present) ───────────────────────────────────────────
if [ ! -f "$ENV" ]; then
    cat > "$ENV" << 'ENVEOF'
NS_FOUNDER_PASSWORD=northstar
NORTHSTAR_PORT=9000
NORTHSTAR_WEBHOOK_BASE=
ENVEOF
    echo "  ✓ Minimal config created (password: northstar)"
fi
source "$ENV"

# ── 3. PYTHON VENV + CRITICAL DEPS ────────────────────────────────────────────
echo "  [1/3] Python environment..."
if [ ! -d "$VENV" ]; then
    echo "  → Creating venv (one-time, ~20s)..."
    python3 -m venv "$VENV"
fi
source "$VENV/bin/activate"

if ! python3 -c "import fastapi, uvicorn" 2>/dev/null; then
    echo "  → Installing core dependencies (~30s)..."
    pip install --quiet fastapi uvicorn python-multipart websockets \
        httpx pydantic "python-jose[cryptography]" aiofiles
    # Optional AI/trading deps in background
    (pip install --quiet anthropic openai "google-generativeai" \
        requests twilio 2>/dev/null) &
fi
echo "  ✓ Dependencies ready"

# ── 4. ALEXANDRIA STORAGE ─────────────────────────────────────────────────────
if [ -d "/Volumes/NSExternal" ]; then
    mkdir -p /Volumes/NSExternal/ALEXANDRIA/{ether/voice,index,receipt_ledger,canon_docs,pressure} 2>/dev/null || true
    echo "  ✓ Alexandria SSD"
else
    mkdir -p "$HOME/ALEXANDRIA"/{ether,index,receipt_ledger,canon_docs,pressure} 2>/dev/null || true
    echo "  ✓ Alexandria: local ($HOME/ALEXANDRIA)"
fi

# ── 5. LAUNCH SERVER ───────────────────────────────────────────────────────────
echo "  [2/3] Starting NS Core..."
cd "$NSS"
"$VENV/bin/uvicorn" nss.api.server:app \
    --host 0.0.0.0 \
    --port $PORT \
    --log-level warning \
    --no-access-log \
    > "$LOG/server.log" 2>&1 &
SERVER_PID=$!

# Health check (10s max)
echo "  → Health check..."
for i in $(seq 1 10); do
    sleep 1
    if curl -sf "http://localhost:$PORT/health" >/dev/null 2>&1; then
        echo "  ✓ NS∞ online"
        break
    fi
    if [ $i -eq 10 ]; then
        echo "  ✗ Server failed to start. Last 20 lines:"
        tail -20 "$LOG/server.log"
        read -p "Press Enter to exit"
        exit 1
    fi
done

# ── 6. OPEN + STREAM ───────────────────────────────────────────────────────────
echo "  [3/3] Opening Console..."
echo ""
echo "  ┌─────────────────────────────────────────┐"
echo "  │  Dashboard:  http://localhost:$PORT       │"
echo "  │  Console:    http://localhost:$PORT/console│"
echo "  │                                           │"
echo "  │  Login: founder / northstar               │"
echo "  │  (change password in Console > Settings)  │"
echo "  └─────────────────────────────────────────┘"
echo ""
echo "  Add API keys: Console > Credentials"
echo "  Full config:  run NORTHSTAR.command"
echo ""

open "http://localhost:$PORT/console" 2>/dev/null || true

# Stream log
echo "  ── Server Log (Ctrl+C to stop) ──────────────"
tail -f "$LOG/server.log"
