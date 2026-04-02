#!/usr/bin/env bash
# Copyright © 2026 Axiolev. All rights reserved.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Load env
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

# Ensure Docker Desktop socket is used (macOS)
if [ -S "/Users/${USER}/.docker/run/docker.sock" ]; then
  export DOCKER_HOST="unix:///Users/${USER}/.docker/run/docker.sock"
fi

NS_URL="http://localhost:9000"
HANDRAIL_URL="http://localhost:8011"
CONTINUUM_URL="http://localhost:8788"

log() { echo "[$(date +%H:%M:%S)] $*"; }
fail() { echo "[FAIL] $*" >&2; exit 1; }

# ─── 1. Ensure Docker is running ────────────────────────────────────────────
log "Checking Docker daemon..."
if ! docker info >/dev/null 2>&1; then
  log "Starting Docker Desktop..."
  open -a Docker
  for i in $(seq 1 30); do
    sleep 2
    docker info >/dev/null 2>&1 && break
    [ "$i" -eq 30 ] && fail "Docker did not start after 60s"
  done
  log "Docker started"
else
  log "Docker already running"
fi

# ─── 2. docker-compose up --build -d ────────────────────────────────────────
log "Building and starting NS∞ stack..."
docker-compose up --build -d

# ─── 3. Wait for all 3 health checks ────────────────────────────────────────
wait_healthy() {
  local name="$1" url="$2" max=60
  log "Waiting for $name at $url ..."
  for i in $(seq 1 $max); do
    code=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null || echo "000")
    [ "$code" = "200" ] && { log "$name healthy"; return 0; }
    sleep 2
  done
  fail "$name did not become healthy after ${max}×2s"
}

wait_healthy "handrail" "$HANDRAIL_URL/healthz"
wait_healthy "ns"       "$NS_URL/healthz"
wait_healthy "continuum" "$CONTINUUM_URL/state"

# ─── 4. Start ngrok on port 9000 (if not already running) ───────────────────
log "Checking ngrok..."
NGROK_URL=""
if curl -s http://localhost:4040/api/tunnels >/dev/null 2>&1; then
  NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | python3 -c \
    "import sys,json; t=json.load(sys.stdin).get('tunnels',[]); print(t[0]['public_url'] if t else '')" 2>/dev/null)
  log "ngrok already running: $NGROK_URL"
else
  log "Starting ngrok on port 9000..."
  nohup ngrok http 9000 >/tmp/ngrok.log 2>&1 &
  sleep 3
  NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | python3 -c \
    "import sys,json; t=json.load(sys.stdin).get('tunnels',[]); print(t[0]['public_url'] if t else '')" 2>/dev/null)
  log "ngrok started: $NGROK_URL"
fi

# ─── 5. Update Twilio webhook ────────────────────────────────────────────────
if [ -n "$NGROK_URL" ] && [ -n "${TWILIO_ACCOUNT_SID:-}" ] && [ -n "${TWILIO_AUTH_TOKEN:-}" ] && [ -n "${TWILIO_PHONE_NUMBER:-}" ]; then
  log "Updating Twilio webhook to $NGROK_URL/voice/inbound ..."
  PHONE_SID=$(curl -s -u "$TWILIO_ACCOUNT_SID:$TWILIO_AUTH_TOKEN" \
    "https://api.twilio.com/2010-04-01/Accounts/$TWILIO_ACCOUNT_SID/IncomingPhoneNumbers.json" | \
    python3 -c "import sys,json; nums=json.load(sys.stdin).get('incoming_phone_numbers',[]); \
    match=[n['sid'] for n in nums if n.get('phone_number')=='${TWILIO_PHONE_NUMBER}']; \
    print(match[0] if match else '')" 2>/dev/null)
  if [ -n "$PHONE_SID" ]; then
    curl -s -X POST -u "$TWILIO_ACCOUNT_SID:$TWILIO_AUTH_TOKEN" \
      "https://api.twilio.com/2010-04-01/Accounts/$TWILIO_ACCOUNT_SID/IncomingPhoneNumbers/$PHONE_SID.json" \
      --data-urlencode "VoiceUrl=$NGROK_URL/voice/inbound" >/dev/null
    log "Twilio webhook updated: $NGROK_URL/voice/inbound"
  else
    log "Could not find phone SID for ${TWILIO_PHONE_NUMBER}, skipping Twilio update"
  fi
else
  log "Skipping Twilio webhook update (missing ngrok URL or Twilio credentials)"
fi

# ─── BOOT COMPLETE ───────────────────────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║           NS∞ BOOT COMPLETE                      ║"
echo "╠══════════════════════════════════════════════════╣"
echo "║  handrail:   $HANDRAIL_URL"
echo "║  ns:         $NS_URL"
echo "║  continuum:  $CONTINUUM_URL"
echo "║  ngrok:      ${NGROK_URL:-not started}"
echo "║  webhook:    ${NGROK_URL:-?}/voice/inbound"
echo "╚══════════════════════════════════════════════════╝"
