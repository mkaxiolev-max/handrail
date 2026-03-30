#!/usr/bin/env bash
set -euo pipefail
NGROK="${1:-}"
if [[ -z "$NGROK" ]]; then
  echo "usage: scripts/voice_smoke.sh https://xxxx.ngrok-free.dev"
  exit 1
fi
curl -s -X POST "$NGROK/voice/incoming" \
  -d "CallSid=CA_TEST" \
  -d "From=+15551234567" \
  -d "To=+15557654321" | sed -n '1,180p'
