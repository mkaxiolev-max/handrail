#!/usr/bin/env bash
# ============================================================
# AXIOLEV NS∞ — Founder Cockpit MAX Acceptance Runner
# Runs swift test + scores cockpit dimensions live
# ============================================================
set -euo pipefail
IFS=$'\n\t'

CYAN='\033[0;36m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
RED='\033[0;31m'; BOLD='\033[1m'; NC='\033[0m'
log()  { echo -e "${CYAN}[ACCEPT]${NC} $*"; }
ok()   { echo -e "${GREEN}[OK]${NC}  $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
die()  { echo -e "${RED}[HALT]${NC} $*"; exit 1; }

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

log "=== ACCEPTANCE RUN ==="
log "Date: $(date -u +%FT%TZ)"

# ── Live endpoint pre-check ───────────────────────────────────
log "PRE-CHECK: Live endpoints"
SCORE=0; TOTAL=9; NOTES=()

check_ep() {
    local label="$1"; local url="$2"
    if curl -fsS --max-time 4 "$url" >/dev/null 2>&1; then
        ok "$label  →  UP"
        SCORE=$((SCORE + 1))
        return 0
    else
        warn "$label  →  DOWN"
        NOTES+=("$label unreachable")
        return 1
    fi
}

check_ep "Handrail :8011"    "http://127.0.0.1:8011/healthz"        || true
check_ep "NS Core :9000"     "http://127.0.0.1:9000/healthz"        || true
check_ep "Continuum :8788"   "http://127.0.0.1:8788/continuum/status" || true
check_ep "RIS :8014"         "http://127.0.0.1:8014/ris/sources"    || true
check_ep "NCOM :9020"        "http://127.0.0.1:9020/ncom/healthz"   || true
check_ep "Mac Adapter :8765" "http://127.0.0.1:8765/healthz"        || true

# ── IMO gate smoke test ───────────────────────────────────────
log "D2: IMO gate /query"
VERB=$(curl -s --max-time 8 -X POST http://127.0.0.1:9000/query \
    -H "Content-Type: application/json" \
    -d '{"prompt":"cockpit acceptance test"}' \
    | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('verb','FAIL'))" 2>/dev/null || echo "FAIL")
if [[ "$VERB" =~ ^(collapse_ready|hold_ncom|force_more_branches|abort)$ ]]; then
    ok "IMO gate verb: $VERB"
else
    warn "IMO gate returned unexpected: $VERB"
    NOTES+=("IMO gate verb unexpected: $VERB")
fi

# ── Ledger integrity ──────────────────────────────────────────
log "D9: Ledger integrity"
CHAINS=$(curl -s --max-time 5 "http://127.0.0.1:9020/ncom/panels/ledger_health" \
    | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('all_chains_valid','unknown'))" 2>/dev/null || echo "unknown")
if [ "$CHAINS" = "True" ] || [ "$CHAINS" = "true" ]; then
    ok "Ledger: all chains valid"
else
    warn "Ledger: chains_valid=$CHAINS"
    NOTES+=("ledger chain validity: $CHAINS")
fi

# ── Swift tests ───────────────────────────────────────────────
log "Running swift test..."
swift test 2>&1 | tee /tmp/founder_cockpit_tests.log
TEST_PASS=$(grep -E "passed" /tmp/founder_cockpit_tests.log | tail -1 | grep -oE "[0-9]+ passed" | head -1 || echo "? passed")
TEST_FAIL=$(grep -E "failed" /tmp/founder_cockpit_tests.log | tail -1 | grep -oE "[0-9]+ failed" | head -1 || echo "0 failed")

echo ""
echo -e "${BOLD}${GREEN}═══════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}${GREEN}  FOUNDER COCKPIT MAX — ACCEPTANCE RESULT              ${NC}"
echo -e "${BOLD}${GREEN}═══════════════════════════════════════════════════════${NC}"
echo    "  Services up   : $SCORE / 6"
echo    "  IMO gate verb : $VERB"
echo    "  Ledger chains : $CHAINS"
echo    "  Swift tests   : $TEST_PASS / $TEST_FAIL"
if [ ${#NOTES[@]} -gt 0 ]; then
    echo "  NOTES:"
    for n in "${NOTES[@]}"; do echo "    · $n"; done
fi
echo -e "${BOLD}${GREEN}═══════════════════════════════════════════════════════${NC}"
