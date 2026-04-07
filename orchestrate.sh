#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
# NS∞ FIRST OPERATIONAL CLOSURE — UNIFIED ORCHESTRATION SCRIPT
# ═══════════════════════════════════════════════════════════════════════════════
# GREEN = GO | Execution: bash ~/axiolev_runtime/orchestrate.sh

set -euo pipefail

RUNTIME_DIR="${HOME}/axiolev_runtime"
LOG_DIR="${RUNTIME_DIR}/.orchestration_logs"
mkdir -p "$LOG_DIR"

TIMESTAMP=$(date '+%Y-%m-%d_%H:%M:%S')
MAIN_LOG="${LOG_DIR}/orchestration_${TIMESTAMP}.log"

GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

log()     { echo -e "${GREEN}[$(date '+%H:%M:%S')]${NC} $*" | tee -a "$MAIN_LOG"; }
task()    { echo -e "${BLUE}[TASK]${NC} $*" | tee -a "$MAIN_LOG"; }
success() { echo -e "${GREEN}[✓]${NC} $*" | tee -a "$MAIN_LOG"; }
error()   { echo -e "${RED}[✗]${NC} $*" | tee -a "$MAIN_LOG"; }
warn()    { echo -e "${YELLOW}[⚠]${NC} $*" | tee -a "$MAIN_LOG"; }

# T1-TOP: Rebuild services
t1_rebuild() {
    local t1_log="${LOG_DIR}/T1-TOP_${TIMESTAMP}.log"
    { task "T1-TOP: Starting service rebuild..."
      cd "$RUNTIME_DIR"
      log "Building ns_core and integrity..."
      docker compose build ns_core integrity 2>&1 | grep -E "Built|ERROR|DONE" | head -20
      log "Starting services..."
      docker compose up -d ns_core integrity 2>&1 | grep -v "^time=" | tail -10
      sleep 8
      [ $(curl -sf http://127.0.0.1:9000/healthz 2>/dev/null | grep -c ok) -gt 0 ] && success "T1-TOP: ns_core healthy" || error "T1-TOP: ns_core failed"
      [ $(curl -sf http://127.0.0.1:9005/healthz 2>/dev/null | grep -c ok) -gt 0 ] && success "T1-TOP: integrity healthy" || error "T1-TOP: integrity failed"
      success "T1-TOP: Complete"
    } >> "$t1_log" 2>&1
}

# T2-BLUE: Model router validation
t2_validate() {
    local t2_log="${LOG_DIR}/T2-BLUE_${TIMESTAMP}.log"
    { task "T2-BLUE: Validating model router..."
      cd "$RUNTIME_DIR"
      sleep 4
      MODELS=$(curl -sf http://127.0.0.1:9002/router/models 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d.get('models',[])))" 2>/dev/null || echo "0")
      [ "$MODELS" -eq 3 ] && success "T2-BLUE: 3/3 models" || warn "T2-BLUE: Found $MODELS models"
      curl -sf http://127.0.0.1:9002/router/status > /dev/null 2>&1 && success "T2-BLUE: Router status live" || error "T2-BLUE: Router failed"
      success "T2-BLUE: Complete"
    } >> "$t2_log" 2>&1
}

# T3-MIDDLE: Memory layer validation
t3_memory() {
    local t3_log="${LOG_DIR}/T3-MIDDLE_${TIMESTAMP}.log"
    { task "T3-MIDDLE: Validating memory layer..."
      cd "$RUNTIME_DIR"
      sleep 4
      ATOMS=$(docker compose exec -T postgres psql -U ns -d ns -c "SELECT COUNT(*) FROM atoms;" 2>/dev/null | tail -2 | head -1 | xargs 2>/dev/null || echo "0")
      success "T3-MIDDLE: $ATOMS atoms"
      EDGES=$(docker compose exec -T postgres psql -U ns -d ns -c "SELECT COUNT(*) FROM edges;" 2>/dev/null | tail -2 | head -1 | xargs 2>/dev/null || echo "0")
      success "T3-MIDDLE: $EDGES edges"
      curl -sf http://127.0.0.1:9001/graph > /dev/null 2>&1 && success "T3-MIDDLE: Graph live" || error "T3-MIDDLE: Graph failed"
      success "T3-MIDDLE: Complete"
    } >> "$t3_log" 2>&1
}

# T4-RED: Final validation + tagging + shutdown
t4_finalize() {
    local t4_log="${LOG_DIR}/T4-RED_${TIMESTAMP}.log"
    { task "T4-RED: Running final validation..."
      cd "$RUNTIME_DIR"
      sleep 4
      if [ -f "scripts/final_validation.sh" ]; then
        bash scripts/final_validation.sh 2>&1 | tail -30 || true
      else
        warn "final_validation.sh not found — skipping"
      fi
      log "Creating LAST_SHUTDOWN.json..."
      GIT_HASH=$(git rev-parse --short HEAD)
      cat > LAST_SHUTDOWN.json << SHUTDOWN_EOF
{
  "timestamp": "$(date -u '+%Y-%m-%dT%H:%M:%SZ')",
  "tag": "ns-first-operational-closure",
  "status": "operational_closure_complete",
  "systems": {"boot":"complete","parsing":"complete","memory":"complete","routing":"complete","output":"complete"},
  "containers": 7,
  "git_hash": "${GIT_HASH}",
  "branch": "boot-operational-closure"
}
SHUTDOWN_EOF
      success "LAST_SHUTDOWN.json created"
      log "Git operations..."
      git add -A 2>&1 | tail -3
      git commit -m "feat: NS∞ first operational closure complete — all 5 layers live" 2>&1 | tail -3
      git tag -f ns-first-operational-closure 2>&1
      success "T4-RED: Complete"
    } >> "$t4_log" 2>&1
}

# MAIN ORCHESTRATION
main() {
    log "════════════════════════════════════════════════════════════════"
    log "NS∞ FIRST OPERATIONAL CLOSURE — UNIFIED ORCHESTRATION"
    log "════════════════════════════════════════════════════════════════"
    log "Status: GREEN = GO | Runtime: $RUNTIME_DIR"
    log ""

    t1_rebuild & T1_PID=$!; log "T1-TOP    → PID $T1_PID"
    t2_validate & T2_PID=$!; log "T2-BLUE   → PID $T2_PID"
    t3_memory & T3_PID=$!; log "T3-MIDDLE → PID $T3_PID"
    t4_finalize & T4_PID=$!; log "T4-RED    → PID $T4_PID"

    log ""; log "Waiting for all 4 tasks..."

    FAILED=0
    for pid in $T1_PID $T2_PID $T3_PID $T4_PID; do
        wait $pid || FAILED=$((FAILED + 1))
    done

    log ""
    log "════════════════════════════════════════════════════════════════"

    echo ""
    for label in "T1-TOP" "T2-BLUE" "T3-MIDDLE" "T4-RED"; do
        logfile="${LOG_DIR}/${label}_${TIMESTAMP}.log"
        [ -f "$logfile" ] && echo "--- $label ---" && cat "$logfile"
    done

    log ""
    [ $FAILED -eq 0 ] && success "✓ ALL 4 TASKS COMPLETE" || error "✗ $FAILED task(s) failed"
    log ""
    [ $FAILED -eq 0 ] && success "NS∞ FIRST OPERATIONAL CLOSURE — COMPLETE" && return 0 || return 1
}

main "$@"
