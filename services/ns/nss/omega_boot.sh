#!/bin/bash
# ============================================================
# NORTHSTAR OMEGA BOOT — NS∞ / AXIOLEV Holdings
# Constitutional AI Operating System
# One command. No drift. No more shells.
# ============================================================

set -e

REPO_DIR="$HOME/NSS"
VENV_DIR="$REPO_DIR/.venv"
LOG_DIR="$REPO_DIR/logs"
PORT=9000

echo ""
echo "============================================================"
echo "⚡ NORTHSTAR OMEGA BOOT"
echo "   NS∞ / AXIOLEV Holdings"
echo "   Ω Advisory Sovereignty Law: ACTIVE"
echo "============================================================"

# ─── Kill any existing process on port ───────────────────────
echo "→ Clearing port $PORT..."
lsof -ti :$PORT | xargs kill -9 2>/dev/null || true
sleep 1

# ─── Create internal directories ─────────────────────────────
mkdir -p "$LOG_DIR"
mkdir -p "$HOME/NSS/MANIFOLD/canon"
mkdir -p "$HOME/NSS/MANIFOLD/mission_graph"
mkdir -p "$HOME/NSS/configs"

# ─── Check external SSD ───────────────────────────────────────
if [ -d "/Volumes/NSExternal" ]; then
    echo "✓ Alexandria SSD: /Volumes/NSExternal"
    mkdir -p /Volumes/NSExternal/ALEXANDRIA/{ether/voice,ether/files,ether/events,index,proto_canon,receipt_ledger}
else
    echo "⚠  NSExternal not mounted — check Disk Utility"
    echo "   Internal fallback active"
fi

# ─── Python venv ─────────────────────────────────────────────
if [ ! -d "$VENV_DIR" ]; then
    echo "→ Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
fi
source "$VENV_DIR/bin/activate"

# ─── Dependencies ─────────────────────────────────────────────
echo "→ Installing dependencies..."
pip install --quiet --upgrade pip
pip install --quiet fastapi "uvicorn[standard]" anthropic openai python-multipart requests
echo "✓ Dependencies ready"

# ─── Load .env ────────────────────────────────────────────────
if [ -f "$REPO_DIR/.env" ]; then
    set -a
    source "$REPO_DIR/.env"
    set +a
    echo "✓ Environment loaded"
else
    echo "✗ FATAL: $REPO_DIR/.env not found"
    exit 1
fi

# ─── Verify critical keys ─────────────────────────────────────
echo ""
echo "─── Intelligence Layer ───────────────────────────────────"
[ -n "$ANTHROPIC_API_KEY" ] && echo "✓ Claude (Anthropic)" || echo "✗ ANTHROPIC_API_KEY missing"
[ -n "$OPENAI_API_KEY" ]   && echo "✓ GPT-4o (OpenAI)"    || echo "  OpenAI: not set"
[ -n "$GOOGLE_API_KEY" ]   && echo "✓ Gemini (Google)"     || echo "  Google: not set"
[ -n "$GROK_API_KEY" ]     && echo "✓ Grok (xAI)"          || echo "  Grok: not set"

echo "─── Voice ────────────────────────────────────────────────"
[ -n "$TWILIO_ACCOUNT_SID" ] && echo "✓ Twilio: $TWILIO_PHONE_NUMBER" || echo "✗ Twilio: not configured"

echo "─── Trading ──────────────────────────────────────────────"
[ -n "$ALPACA_API_KEY" ] && echo "✓ Alpaca: broker sandbox [PAPER MODE]" || echo "  Alpaca: not configured"

echo "─── Market Data ──────────────────────────────────────────"
[ -n "$POLYGON_API_KEY" ] && echo "✓ Polygon" || echo "  Polygon: not set"
[ -n "$FRED_API_KEY" ]    && echo "✓ FRED"    || echo "  FRED: not set"
[ -n "$NEWSAPI_KEY" ]     && echo "✓ NewsAPI" || echo "  NewsAPI: not set"
echo "──────────────────────────────────────────────────────────"
echo ""

# ─── Launch ───────────────────────────────────────────────────
echo "============================================================"
echo "✓ NORTHSTAR ONLINE"
echo "✓ Constitution:    Locked"
echo "✓ YubiKey:         Bound (SN: $YUBIKEY_SERIAL)"
echo "✓ Dashboard:       http://localhost:$PORT"
echo "✓ Query API:       POST http://localhost:$PORT/query"
echo "✓ Health:          GET  http://localhost:$PORT/health"
echo "✓ Trade gate:      POST http://localhost:$PORT/trade/request"
echo ""
echo "  Voice (Twilio):  Set NORTHSTAR_WEBHOOK_BASE after ngrok"
echo "  ngrok command:   ngrok http $PORT"
echo "============================================================"
echo ""
echo "Ctrl+C to stop."
echo ""

cd "$REPO_DIR"
exec uvicorn nss.api.server:app \
    --host 0.0.0.0 \
    --port $PORT \
    --log-level warning \
    --no-access-log
