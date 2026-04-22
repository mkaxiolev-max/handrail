#!/usr/bin/env bash
# NS∞ Verify + Save — run before shutdown
# Writes a timestamped JSON verdict to artifacts/.
# Idempotent. Safe to run repeatedly.
set -euo pipefail

REPO=~/axiolev_runtime
cd "$REPO"
mkdir -p "$REPO/artifacts"

STAMP=$(date -u +%Y%m%dT%H%M%SZ)
OUT="$REPO/artifacts/verify_${STAMP}.json"

BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
SHA=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")

# ── Checks ────────────────────────────────────────────────────────────────────
_check() {
    local url=$1
    curl -sf --max-time 5 "$url" >/dev/null 2>&1 && echo "ok" || echo "fail"
}

NS_CORE=$(_check http://127.0.0.1:9000/healthz)
NS_API=$(_check http://127.0.0.1:9011/health)
HANDRAIL=$(_check http://127.0.0.1:8011/healthz)
CONTINUUM=$(_check http://127.0.0.1:8788/state)
ALEX=$([ -d /Volumes/NSExternal ] && echo "ok" || echo "not-mounted")

STATE_BODY=$(curl -sf --max-time 5 http://127.0.0.1:8788/state 2>/dev/null || echo "{}")

# ── Live score snapshot (non-blocking, best-effort) ───────────────────────────
V31_SCORE=$(python3 tools/scoring/master_v31.py --no-tests 2>/dev/null \
    | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['canonical']['score'])" 2>/dev/null \
    || echo "null")
V31_MODE="no-tests"
NVIR_RATE=$(python3 -c "
from services.nvir.live_loop import load_live_credits
r,_ = load_live_credits(); print(r if r else 'null')
" 2>/dev/null || echo "null")
if [ "$NVIR_RATE" != "null" ]; then
  V31_SCORE=$(python3 tools/scoring/master_v31.py --no-tests 2>/dev/null \
      | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['canonical']['score'])" 2>/dev/null \
      || echo "null")
  V31_MODE="no-tests+nvir"
fi

# ── Verdict ───────────────────────────────────────────────────────────────────
VERDICT="READY_FOR_SHUTDOWN"
FAILURES=()
[ "$NS_CORE"   != "ok" ] && VERDICT="NOT_READY_FOR_SHUTDOWN" && FAILURES+=("ns_core:9000")
[ "$NS_API"    != "ok" ] && VERDICT="NOT_READY_FOR_SHUTDOWN" && FAILURES+=("ns_api:9011")
[ "$HANDRAIL"  != "ok" ] && VERDICT="NOT_READY_FOR_SHUTDOWN" && FAILURES+=("handrail:8011")
[ "$CONTINUUM" != "ok" ] && VERDICT="NOT_READY_FOR_SHUTDOWN" && FAILURES+=("continuum:8788")

# ── Write artifact ────────────────────────────────────────────────────────────
cat > "$OUT" <<EOF
{
  "timestamp": "$STAMP",
  "branch": "$BRANCH",
  "sha": "$SHA",
  "services": {
    "ns_core":   "$NS_CORE",
    "ns_api":    "$NS_API",
    "handrail":  "$HANDRAIL",
    "continuum": "$CONTINUUM"
  },
  "alexandria_mount": "$ALEX",
  "continuum_state": $STATE_BODY,
  "v31_score": $V31_SCORE,
  "v31_mode": "$V31_MODE",
  "nvir_rate": $NVIR_RATE,
  "verdict": "$VERDICT"
}
EOF

echo ""
echo "Verification report: $OUT"
echo ""

if [ "$VERDICT" = "READY_FOR_SHUTDOWN" ]; then
    echo "Safe to shut down Mac."
else
    echo "[NOT READY] Failing checks:"
    for f in "${FAILURES[@]}"; do echo "  - $f"; done
    exit 1
fi
