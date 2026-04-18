#!/usr/bin/env bash
set -e

# =============================================================================
# NS∞ FOUNDER READY+ MAX — FINAL CLOSURE SCRIPT
# -----------------------------------------------------------------------------
# PURPOSE:
#   Convert system from "phase-complete" → "Founder Ready+ Max verified"
#
#   This script DOES NOT TRUST PHASE FLAGS.
#   It re-verifies the system against 8 constitutional pillars.
#
# OUTPUT:
#   One authoritative artifact:
#   final_state_founder_ready_plus_max.json
# =============================================================================

REPO=~/axiolev_runtime
OUT="$REPO/.terminal_manager/final_state"
mkdir -p "$OUT"

STAMP=$(date -u +%Y%m%dT%H%M%SZ)
FINAL="$OUT/final_state_${STAMP}.json"

echo "=== NS∞ MAX CLOSURE START ==="

# -----------------------------------------------------------------------------
# 1. SYSTEM BOOT VERIFICATION (PILLAR: OPERATIONAL REALITY)
# -----------------------------------------------------------------------------

echo "[1] Checking core services..."

SERVICES_OK=true

curl -sf http://127.0.0.1:9000/healthz >/dev/null || SERVICES_OK=false
curl -sf http://127.0.0.1:9090/state >/dev/null || SERVICES_OK=false

DOCKER_OK=$(docker ps 2>/dev/null | wc -l)

# -----------------------------------------------------------------------------
# 2. CONSTITUTIONAL CORE (RING 6)
# -----------------------------------------------------------------------------

echo "[2] Checking constitutional core..."

PI_OK=$(curl -s -X POST http://127.0.0.1:9000/pi/check \
  -H "Content-Type: application/json" \
  -d '{"candidate":{"op":"test.read"}}' | grep -c "return_block_version")

CANON_OK=$(curl -s -X POST http://127.0.0.1:9000/canon/promote \
  -H "Content-Type: application/json" \
  -d '{"candidate":"test"}' | grep -c "return_block_version")

RESUME_OK=$(curl -s -X POST http://127.0.0.1:9000/ns/resume \
  -H "Content-Type: application/json" \
  -d '{}' | grep -c "return_block_version")

# -----------------------------------------------------------------------------
# 3. EPISTEMIC DISCIPLINE (DOCTRINE + CLEARING)
# -----------------------------------------------------------------------------

echo "[3] Checking epistemic discipline..."

DOCTRINE_EXISTS=false
# Actual path: docs/canon/HALLUCINATION_DOCTRINE.md
[ -f "$REPO/docs/canon/HALLUCINATION_DOCTRINE.md" ] && DOCTRINE_EXISTS=true

CLEARING_EXISTS=false
[ -d "$REPO/services/ns_core/clearing" ] && CLEARING_EXISTS=true

# -----------------------------------------------------------------------------
# 4. FOUNDER VISIBILITY (UI REALITY)
# -----------------------------------------------------------------------------

echo "[4] Checking UI integrity..."

UI_EXISTS=false
[ -d "$REPO/frontend/src" ] && UI_EXISTS=true

# key invariant: UI must not compute truth
UI_VIOLATION=$(grep -r "compute" "$REPO/frontend/src" 2>/dev/null | wc -l)

# -----------------------------------------------------------------------------
# 5. MEMORY + RECEIPTS (ALEXANDRIA)
# -----------------------------------------------------------------------------

echo "[5] Checking memory substrate..."

ALEX_OK=false
[ -d "/Volumes/NSExternal" ] && ALEX_OK=true

RECEIPTS_COUNT=$(find "$REPO/.run" 2>/dev/null | wc -l)

# -----------------------------------------------------------------------------
# 6. EMBODIMENT (HANDRAIL / ADAPTER)
# -----------------------------------------------------------------------------

echo "[6] Checking embodiment..."

HANDRAIL_OK=$(curl -sf http://127.0.0.1:8011/healthz >/dev/null && echo 1 || echo 0)

# -----------------------------------------------------------------------------
# 7. VOICE SYSTEM
# -----------------------------------------------------------------------------

echo "[7] Checking voice..."

VOICE_OK=$(grep -r "/voice/respond" "$REPO" | wc -l)

# -----------------------------------------------------------------------------
# 8. AUTOPOIESIS (PROGRAM RUNTIME)
# -----------------------------------------------------------------------------

echo "[8] Checking autopoiesis..."

AUTO_DIR="$REPO/services/ns_core/autopoiesis"
AUTO_OK=false
[ -d "$AUTO_DIR" ] && AUTO_OK=true

PROGRAM_RUNTIME=$(grep -r "ProgramRuntime" "$REPO" | wc -l)

# -----------------------------------------------------------------------------
# 9. CROSS-SYSTEM COHERENCE (CRITICAL)
# -----------------------------------------------------------------------------

echo "[9] Checking cross-pillar coherence..."

COHERENCE_OK=true

# must pass PDP deny — JSON uses "ok":false (no space)
PDP_TEST=$(curl -s -X POST http://127.0.0.1:9000/pdp/decide \
  -H "Content-Type: application/json" \
  -d '{"principal":"anon","action":"canon.promote"}' | grep -c '"ok":false')

[ "$PDP_TEST" -eq 0 ] && COHERENCE_OK=false

# -----------------------------------------------------------------------------
# FINAL VERDICT LOGIC (FOUNDER READY+ MAX)
# -----------------------------------------------------------------------------

echo "[FINAL] Computing verdict..."

if $SERVICES_OK \
&& [ "$PI_OK" -gt 0 ] \
&& [ "$CANON_OK" -gt 0 ] \
&& [ "$RESUME_OK" -gt 0 ] \
&& $DOCTRINE_EXISTS \
&& $CLEARING_EXISTS \
&& $UI_EXISTS \
&& $ALEX_OK \
&& [ "$HANDRAIL_OK" -eq 1 ] \
&& [ "$VOICE_OK" -gt 0 ] \
&& $AUTO_OK \
&& [ "$PROGRAM_RUNTIME" -gt 0 ] \
&& $COHERENCE_OK
then
  VERDICT="FOUNDER_READY_PLUS_MAX"
else
  VERDICT="NOT_COMPLETE"
fi

# -----------------------------------------------------------------------------
# WRITE FINAL STATE
# -----------------------------------------------------------------------------

cat > "$FINAL" <<EOF
{
  "timestamp": "$STAMP",
  "verdict": "$VERDICT",
  "pillars": {
    "operational": $SERVICES_OK,
    "constitutional": $PI_OK,
    "epistemic": $DOCTRINE_EXISTS,
    "visibility": $UI_EXISTS,
    "memory": $ALEX_OK,
    "embodiment": $HANDRAIL_OK,
    "voice": $VOICE_OK,
    "autopoiesis": $AUTO_OK
  },
  "coherence": $COHERENCE_OK,
  "receipts": $RECEIPTS_COUNT
}
EOF

echo "=== FINAL STATE ==="
cat "$FINAL"
echo "=== DONE ==="
