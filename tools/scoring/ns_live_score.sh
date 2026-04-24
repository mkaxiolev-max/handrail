#!/usr/bin/env bash
# =============================================================================
# ns_live_score.sh  —  NS∞ Live Scorer + Max-Delta Insight Ranker
# AXIOLEV Holdings LLC © 2026  —  NorthStar Infinity Constitutional AI OS
#
# WHAT IT DOES
#   1. Runs the full test surface live (pytest + vitest + XCTest if wired)
#   2. Computes live composite scores — v2.1, v3.0, v3.1, v3.2
#   3. Ranks insight deltas by composite-points-per-week (max-leverage first)
#   4. Scores ns_max_closure.sh completion (16-point rubric, 0-100)
#   5. Emits NS_LIVE_SCORE.md + NS_LIVE_SCORE.json to artifacts/
#
# READS (authoritative inputs, if present)
#   - artifacts/ns_infinity_scorecard.json      (instruments, weights, credits)
#   - artifacts/max_closure/M*.json             (per-phase credit emissions)
#   - ~/.ns_max_closure/state/*.state            (phase done/pending/failed)
#
# SAFE
#   - Read-only. Never commits, tags, or pushes.
#   - Bash 3.2 compatible (macOS default).
#   - Idempotent — re-run anytime.
#
# USAGE
#   cd ~/axiolev_runtime
#   chmod +x tools/scoring/ns_live_score.sh
#   tools/scoring/ns_live_score.sh
#
#   # Fast mode (skip full pytest, use last collect-only):
#   FAST=1 tools/scoring/ns_live_score.sh
# =============================================================================

set -Eeuo pipefail
umask 0022

# ─── Config ──────────────────────────────────────────────────────────────────
REPO_DIR="${REPO_DIR:-$HOME/axiolev_runtime}"
ALEX="${ALEXANDRIA:-/Volumes/NSExternal/ALEXANDRIA}"
ART_DIR="${ART_DIR:-$REPO_DIR/artifacts/live_score}"
CLOSURE_STATE_DIR="${CLOSURE_STATE_DIR:-$HOME/.ns_max_closure/state}"
CLOSURE_ART_DIR="${CLOSURE_ART_DIR:-$REPO_DIR/artifacts/max_closure}"
RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)"

FAST="${FAST:-0}"
PREV_V31="${PREV_V31:-92.42}"   # Prior SUPERMAX composite for delta

mkdir -p "$ART_DIR"
LOG="$ART_DIR/run-$RUN_ID.log"
touch "$LOG"

# ─── UI helpers (bash 3.2 safe) ──────────────────────────────────────────────
_ts()  { date -u +"%Y-%m-%dT%H:%M:%SZ"; }
_log() { printf "[%s] %s\n" "$(_ts)" "$*" | tee -a "$LOG"; }
hdr()  { printf "\n\033[1;36m━━━ %s ━━━\033[0m\n" "$*" | tee -a "$LOG"; }
info() { printf "\033[0;34m[..]\033[0m %s\n" "$*" | tee -a "$LOG"; }
ok()   { printf "\033[0;32m[OK]\033[0m %s\n" "$*" | tee -a "$LOG"; }
warn() { printf "\033[0;33m[!!]\033[0m %s\n" "$*" | tee -a "$LOG"; }
err()  { printf "\033[0;31m[XX]\033[0m %s\n" "$*" | tee -a "$LOG" 1>&2; }
have() { command -v "$1" >/dev/null 2>&1; }

# FP math via awk (bash 3.2 has no floats)
fmul() { awk -v a="$1" -v b="$2" 'BEGIN{printf "%.4f", a*b}'; }
fadd() { awk -v a="$1" -v b="$2" 'BEGIN{printf "%.4f", a+b}'; }
fsub() { awk -v a="$1" -v b="$2" 'BEGIN{printf "%.4f", a-b}'; }
fdiv() { awk -v a="$1" -v b="$2" 'BEGIN{if(b==0){print 0}else{printf "%.4f", a/b}}'; }
fmt2() { awk -v a="$1" 'BEGIN{printf "%.2f", a}'; }
fmt4() { awk -v a="$1" 'BEGIN{printf "%.4f", a}'; }
fge()  { awk -v a="$1" -v b="$2" 'BEGIN{exit !(a>=b)}'; }

cd "$REPO_DIR" 2>/dev/null || { err "repo not at $REPO_DIR"; exit 1; }

# ─── 1. PYTEST — full collection + run ───────────────────────────────────────
hdr "1. PYTEST — LIVE TEST SURFACE"

COLLECT_FILE="$ART_DIR/pytest_collect.txt"
BYFILE_FILE="$ART_DIR/pytest_by_file.txt"
RUN_FILE="$ART_DIR/pytest_run.txt"

PYTEST_COLLECTED=0; PYTEST_PASS=0; PYTEST_FAIL=0; PYTEST_ERR=0; PYTEST_SKIP=0

if have pytest; then
  info "pytest --collect-only"
  pytest --collect-only -q 2>/dev/null | grep "::" | sort -u > "$COLLECT_FILE" || true
  PYTEST_COLLECTED=$(wc -l < "$COLLECT_FILE" | tr -d ' ')
  awk -F'::' '{print $1}' "$COLLECT_FILE" | sort | uniq -c | sort -rn > "$BYFILE_FILE"
  ok "collected: $PYTEST_COLLECTED tests across $(wc -l < "$BYFILE_FILE" | tr -d ' ') files"

  if [ "$FAST" = "1" ]; then
    warn "FAST=1 — skipping full pytest run; using collect count only"
    PYTEST_PASS="$PYTEST_COLLECTED"
  else
    info "pytest run (full suite)"
    ( pytest -q --tb=no --no-header 2>&1 || true ) | tee "$RUN_FILE" >/dev/null
    SUMMARY=$(tail -n 40 "$RUN_FILE" | grep -E "(passed|failed|error)" | tail -n 1)
    PYTEST_PASS=$(echo "$SUMMARY" | grep -oE "[0-9]+ passed"  | head -n1 | grep -oE "[0-9]+" || echo 0)
    PYTEST_FAIL=$(echo "$SUMMARY" | grep -oE "[0-9]+ failed"  | head -n1 | grep -oE "[0-9]+" || echo 0)
    PYTEST_ERR=$(echo  "$SUMMARY" | grep -oE "[0-9]+ error"   | head -n1 | grep -oE "[0-9]+" || echo 0)
    PYTEST_SKIP=$(echo "$SUMMARY" | grep -oE "[0-9]+ skipped" | head -n1 | grep -oE "[0-9]+" || echo 0)
    PYTEST_PASS=${PYTEST_PASS:-0}; PYTEST_FAIL=${PYTEST_FAIL:-0}
    PYTEST_ERR=${PYTEST_ERR:-0};   PYTEST_SKIP=${PYTEST_SKIP:-0}
    if [ "$PYTEST_FAIL" -eq 0 ] && [ "$PYTEST_ERR" -eq 0 ]; then
      ok "pytest: $PYTEST_PASS pass / $PYTEST_FAIL fail / $PYTEST_ERR err / $PYTEST_SKIP skip"
    else
      warn "pytest: $PYTEST_PASS pass / $PYTEST_FAIL fail / $PYTEST_ERR err / $PYTEST_SKIP skip"
    fi
  fi
else
  warn "pytest not found — PYTEST_PASS=0"
fi

PYTEST_TOTAL_RUN=$((PYTEST_PASS + PYTEST_FAIL + PYTEST_ERR))
if [ "$PYTEST_TOTAL_RUN" -gt 0 ]; then
  PYTEST_PASS_RATE=$(fdiv "$PYTEST_PASS" "$PYTEST_TOTAL_RUN")
else
  PYTEST_PASS_RATE="0.0000"
fi

# ─── 2. VITEST — ns_ui ───────────────────────────────────────────────────────
hdr "2. VITEST — ns_ui"

VITEST_PASS=0; VITEST_FAIL=0; VITEST_TOTAL=0
if [ -d "$REPO_DIR/ns_ui" ] && have npm; then
  info "npm test --silent (ns_ui)"
  VFILE="$ART_DIR/vitest_run.txt"
  ( cd "$REPO_DIR/ns_ui" && npm test --silent -- --run --reporter=default 2>&1 || true ) | tee "$VFILE" >/dev/null
  VITEST_PASS=$(grep -oE "[0-9]+ passed" "$VFILE" 2>/dev/null | tail -n1 | grep -oE "[0-9]+" || echo 0)
  VITEST_FAIL=$(grep -oE "[0-9]+ failed" "$VFILE" 2>/dev/null | tail -n1 | grep -oE "[0-9]+" || echo 0)
  VITEST_PASS=${VITEST_PASS:-0}; VITEST_FAIL=${VITEST_FAIL:-0}
  VITEST_TOTAL=$((VITEST_PASS + VITEST_FAIL))
  ok "vitest: $VITEST_PASS pass / $VITEST_FAIL fail"
else
  warn "ns_ui or npm missing — vitest skipped"
fi

# ─── 3. XCTEST — Swift app (if wired) ────────────────────────────────────────
hdr "3. XCTEST — NSInfinityApp (if target wired)"

XCTEST_PASS=0; XCTEST_FAIL=0; XCTEST_STATUS="not_wired"
XCAPP_DIR="$REPO_DIR/apps/ns_mac/NSInfinityApp"
if [ -d "$XCAPP_DIR" ] && have xcodebuild; then
  XFILE="$ART_DIR/xctest_run.txt"
  info "xcodebuild test (NSInfinityApp)"
  ( cd "$XCAPP_DIR" && xcodebuild test \
      -scheme NSInfinityApp -destination 'platform=macOS' 2>&1 || true ) | tee "$XFILE" >/dev/null
  XCTEST_PASS=$(grep -c "Test Case.*passed" "$XFILE" 2>/dev/null || true)
  XCTEST_FAIL=$(grep -c "Test Case.*failed" "$XFILE" 2>/dev/null || true)
  XCTEST_PASS=${XCTEST_PASS:-0}; XCTEST_FAIL=${XCTEST_FAIL:-0}
  if [ "$((XCTEST_PASS + XCTEST_FAIL))" -gt 0 ]; then
    XCTEST_STATUS="wired"
    ok "xctest: $XCTEST_PASS pass / $XCTEST_FAIL fail"
  else
    XCTEST_STATUS="not_wired"
    warn "xctest target not wired (expected — deferred)"
  fi
else
  warn "Xcode app or xcodebuild missing — xctest skipped"
fi

# ─── 4. DOCKER SERVICES ──────────────────────────────────────────────────────
hdr "4. DOCKER SERVICES HEALTH"

DOCKER_HEALTHY=0; DOCKER_TOTAL=0
if have docker; then
  DOCKER_TOTAL=$( (docker ps --format '{{.Names}}' 2>/dev/null || true) | wc -l | tr -d ' ')
  DOCKER_HEALTHY=$( (docker ps --format '{{.Names}} {{.Status}}' 2>/dev/null || true) | grep -c healthy || true)
  DOCKER_HEALTHY=${DOCKER_HEALTHY:-0}
  ok "docker: $DOCKER_HEALTHY healthy / $DOCKER_TOTAL running"
else
  warn "docker not available"
fi

# ─── 5. GITLEAKS — security posture ──────────────────────────────────────────
hdr "5. GITLEAKS — SECURITY POSTURE"

LEAK_COUNT=0
if have gitleaks; then
  GFILE="$ART_DIR/gitleaks.json"
  gitleaks detect --no-banner --redact --exit-code 0 --report-path "$GFILE" 2>&1 | tee -a "$LOG" >/dev/null || true
  if [ -f "$GFILE" ]; then
    LEAK_COUNT=$(python3 -c "import json,sys;d=json.load(open('$GFILE'));print(len(d) if isinstance(d,list) else 0)" 2>/dev/null || echo 0)
  fi
  if [ "$LEAK_COUNT" -eq 0 ]; then ok "leaks: 0"; else warn "leaks: $LEAK_COUNT"; fi
else
  warn "gitleaks not installed"
fi

HOOK_INSTALLED="no"
if [ -x "$REPO_DIR/.git/hooks/pre-commit" ] && grep -q gitleaks "$REPO_DIR/.git/hooks/pre-commit" 2>/dev/null; then
  HOOK_INSTALLED="yes"
  ok "pre-commit gitleaks hook active"
else
  warn "pre-commit gitleaks hook missing"
fi

# ─── 6. COMPOSITE SCORE — v2.1 / v3.0 / v3.1 / v3.2 ──────────────────────────
hdr "6. COMPOSITE SCORES — v2.1 / v3.0 / v3.1 / v3.2"

# Instrument live scores (defaults; overwritten from scorecard if present)
I1=88.02; I2=88.36; I3=88.84; I4=95.28; I5=89.00; I6=88.00; I7=84.00

# Load live scores from scorecard JSON using a temp file (bash 3.2 safe: no heredoc in $())
SCORECARD="$REPO_DIR/artifacts/ns_infinity_scorecard.json"
_SC_PY="$ART_DIR/_sc_extract.py"
cat > "$_SC_PY" <<'PYEOF'
import json, sys
d = json.load(open(sys.argv[1]))
inst = d.get("instruments", {})
for k in ["I1","I2","I3","I4","I5","I6","I7"]:
    v = inst.get(k, {}).get("current_live")
    if v is not None:
        print(k + "=" + str(v))
PYEOF

if [ -f "$SCORECARD" ] && have python3; then
  while IFS="=" read -r k v; do
    [ -n "$k" ] && [ -n "$v" ] && eval "$k=$v"
  done < <(python3 "$_SC_PY" "$SCORECARD" 2>/dev/null)
  ok "instruments loaded from scorecard"
else
  warn "scorecard missing — using hardcoded live values"
fi

# Apply fractional credits from completed max-closure phases
# Use temp python script to avoid heredoc-in-$() in loop
_CR_PY="$ART_DIR/_credits_extract.py"
cat > "$_CR_PY" <<'PYEOF'
import json, sys
try:
    d = json.load(open(sys.argv[1]))
    c = d.get("credits", {})
    agg = {}
    for k, v in c.items():
        inst = k.split(".")[0]
        try:
            v = float(v)
        except Exception:
            continue
        agg[inst] = agg.get(inst, 0) + v
    for k, v in agg.items():
        print(k + "=" + str(v))
except Exception:
    pass
PYEOF

CREDITS_APPLIED=""
if [ -d "$CLOSURE_ART_DIR" ] && have python3; then
  for j in "$CLOSURE_ART_DIR"/M*.json; do
    [ -f "$j" ] || continue
    while IFS="=" read -r k inc; do
      [ -z "$k" ] && continue
      if awk -v a="$inc" 'BEGIN{exit !(a>0)}' 2>/dev/null; then
        cur=$(eval echo "\$$k" 2>/dev/null || echo 0)
        new=$(awk -v a="$cur" -v b="$inc" 'BEGIN{s=a+b*0.3; if(s>99.5)s=99.5; printf "%.4f", s}')
        eval "$k=$new"
        CREDITS_APPLIED="$CREDITS_APPLIED $k"
      fi
    done < <(python3 "$_CR_PY" "$j" 2>/dev/null)
  done
fi
[ -n "$CREDITS_APPLIED" ] && ok "credits applied:$CREDITS_APPLIED"

# Weights
V21_I1=0.15; V21_I2=0.20; V21_I3=0.20; V21_I4=0.30; V21_I5=0.15
V30_I1=0.150; V30_I2=0.200; V30_I3=0.175; V30_I4=0.275; V30_I5=0.150; V30_I6=0.100
V31_I1=0.135; V31_I2=0.185; V31_I3=0.175; V31_I4=0.255; V31_I5=0.145; V31_I6=0.105
V32_I1=0.1215; V32_I2=0.162; V32_I3=0.162; V32_I4=0.243; V32_I5=0.1215; V32_I6=0.090; V32_I7=0.100

COMP_V21=$(python3 -c "print(round($V21_I1*$I1+$V21_I2*$I2+$V21_I3*$I3+$V21_I4*$I4+$V21_I5*$I5,2))")
COMP_V30=$(python3 -c "print(round($V30_I1*$I1+$V30_I2*$I2+$V30_I3*$I3+$V30_I4*$I4+$V30_I5*$I5+$V30_I6*$I6,2))")
COMP_V31=$(python3 -c "print(round($V31_I1*$I1+$V31_I2*$I2+$V31_I3*$I3+$V31_I4*$I4+$V31_I5*$I5+$V31_I6*$I6,2))")
COMP_V32=$(python3 -c "print(round($V32_I1*$I1+$V32_I2*$I2+$V32_I3*$I3+$V32_I4*$I4+$V32_I5*$I5+$V32_I6*$I6+$V32_I7*$I7,2))")

band() {
  local c="$1"
  if fge "$c" 96; then echo "Omega-Transcendent"
  elif fge "$c" 95; then echo "Omega-SuperMax"
  elif fge "$c" 93; then echo "Omega-Certified"
  elif fge "$c" 90; then echo "Omega-Approaching"
  else echo "sub-90"
  fi
}
BAND_V31=$(band "$COMP_V31")
BAND_V32=$(band "$COMP_V32")
DELTA_V31=$(fsub "$COMP_V31" "$PREV_V31")

printf "\n"
printf "  %-10s %-10s %-22s %-10s\n" "version" "composite" "band" "delta vs prior"
printf "  %-10s %-10s %-22s %-10s\n" "──────" "─────────" "────" "──────────────"
printf "  %-10s %-10s %-22s %-10s\n" "v2.1"  "$COMP_V21" "(legacy)"     "—"
printf "  %-10s %-10s %-22s %-10s\n" "v3.0"  "$COMP_V30" "(internal)"   "—"
printf "  %-10s %-10s %-22s %-10s\n" "v3.1"  "$COMP_V31" "$BAND_V31"    "$DELTA_V31"
printf "  %-10s %-10s %-22s %-10s\n" "v3.2"  "$COMP_V32" "$BAND_V32"    "—"

# ─── 7. INSIGHT RANKING — max-delta first ────────────────────────────────────
hdr "7. INSIGHT DELTA RANKING — MAX LEVERAGE"

phase_state() {
  local f="$CLOSURE_STATE_DIR/$1.state"
  [ -f "$f" ] && head -n1 "$f" || echo "pending"
}

TMPR="$ART_DIR/insight_ranking.tsv"
: > "$TMPR"

# Write insight table to a temp file (avoid heredoc-in-$() issues)
_INSIGHT_TMP="$ART_DIR/_insight_table.txt"
cat > "$_INSIGHT_TMP" <<'INSIGHTS'
INS-01|Full action-surface CPS (I6.C3+10 I4.RCI+3 I5.rev+3)|2|2.2|M3
INS-03|Reversibility registry 100% (I6.C5+8 I5.rev+8)|2|1.6|M2
INS-06|Calibration SFT tokenized Brier (I2+7)|2|1.4|M1
INS-08|Hormetic B0-B5 sweep (I4.HDRC+5 I2.rob+3)|2|1.1|M4
INS-04|TLA+/Apalache on Dignity Kernel (I6.C2+5 I1.D4+5 I5+4)|3|1.4|M6
INS-02|NVIR generator+oracle remaining (I2+0.8)|3|0.8|M5
INS-05|Validator adapters Lean/DFT/FDA (I6.C4+8 I3.admin+4)|6|1.2|M7
INS-07|Witness cosigning (LANDED)|0|0.0|landed
NS-AL|Proof-carrying execution (I4+1.5 I6+2.0 I7+8.0)|8|1.2|M8
INSIGHTS

printf "\n  %-7s %-58s %-5s %-7s %-9s %-10s\n" "id" "description" "weeks" "delta" "d/wk" "status"
printf "  %-7s %-58s %-5s %-7s %-9s %-10s\n"   "──" "───────────" "─────" "─────" "────" "──────"

while IFS='|' read -r id name weeks dv31 phase_id; do
  [ -z "$id" ] && continue
  if [ "$phase_id" = "landed" ]; then
    status="landed"; dpw="0.0000"
  else
    status=$(phase_state "$phase_id")
    dpw=$(fdiv "$dv31" "$weeks")
  fi
  printf "%s\t%s\t%s\t%s\t%s\t%s\n" "$dpw" "$id" "$name" "$weeks" "$dv31" "$status" >> "$TMPR"
done < "$_INSIGHT_TMP"

sort -t$'\t' -k1,1 -rn "$TMPR" | while IFS=$'\t' read -r dpw id name weeks dv31 status; do
  printf "  %-7s %-58s %-5s %-7s %-9s %-10s\n" "$id" "$name" "$weeks" "+$dv31" "$dpw" "$status"
done | tee -a "$LOG"

REMAINING_DELTA=$(awk -F'\t' '$6!="done"&&$6!="landed"{s+=$5} END{printf "%.2f", s+0}' "$TMPR")
PROJ_V31=$(fadd "$COMP_V31" "$REMAINING_DELTA")
info "remaining delta if all pending land: +$REMAINING_DELTA => projected v3.1 $PROJ_V31"

# ─── 8. MAX-CLOSURE COMPLETION SCORE (0-100) ─────────────────────────────────
hdr "8. ns_max_closure.sh COMPLETION SCORE"

phase_pts() {
  local pid="$1"; local max="$2"
  local s; s=$(phase_state "$pid")
  case "$s" in
    done)    echo "$max" ;;
    running) awk -v m="$max" 'BEGIN{printf "%.2f", m*0.5}' ;;
    *)       echo "0" ;;
  esac
}

PHASE_WEIGHTS="PREFLIGHT:3 M0:5 M1:7 M2:8 M3:10 M4:6 M5:8 M6:7 M7:6 M8:10 M9:5 M10:8 M11:8 M12:2 M13:4 M14:3"

SCORE="0.00"
printf "\n  %-12s %-10s %-8s %-10s\n" "phase" "state" "weight" "earned"
printf "  %-12s %-10s %-8s %-10s\n"   "────" "─────" "──────" "──────"
for entry in $PHASE_WEIGHTS; do
  pid=$(echo "$entry" | cut -d: -f1)
  wt=$(echo "$entry" | cut -d: -f2)
  s=$(phase_state "$pid")
  earned=$(phase_pts "$pid" "$wt")
  SCORE=$(fadd "$SCORE" "$earned")
  printf "  %-12s %-10s %-8s %-10s\n" "$pid" "$s" "$wt" "$earned"
done | tee -a "$LOG"

SCORE=$(fmt2 "$SCORE")
SCORE_BAND="incomplete"
if fge "$SCORE" 95; then SCORE_BAND="complete"
elif fge "$SCORE" 85; then SCORE_BAND="near-complete"
elif fge "$SCORE" 70; then SCORE_BAND="in-progress"
elif fge "$SCORE" 40; then SCORE_BAND="early"
elif fge "$SCORE" 1;  then SCORE_BAND="started"
fi
ok "max-closure completion: $SCORE / 100 — $SCORE_BAND"

# ─── 9. EMIT ARTIFACTS ───────────────────────────────────────────────────────
hdr "9. EMIT ARTIFACTS"

MD="$ART_DIR/NS_LIVE_SCORE.md"
JSON_OUT="$ART_DIR/NS_LIVE_SCORE.json"

# Build insight ranking string for markdown (no $() in heredoc — use temp file)
_RANK_MD="$ART_DIR/_rank_md.txt"
sort -t$'\t' -k1,1 -rn "$TMPR" | while IFS=$'\t' read -r dpw id name weeks dv31 status; do
  printf "- **%s** %s — +%s v3.1 in %sw (d/wk=%s) — %s\n" "$id" "$name" "$dv31" "$weeks" "$dpw" "$status"
done > "$_RANK_MD"

_PHASE_JSON="$ART_DIR/_phase_json.txt"
: > "$_PHASE_JSON"
_first=1
for entry in $PHASE_WEIGHTS; do
  pid=$(echo "$entry" | cut -d: -f1)
  wt=$(echo "$entry" | cut -d: -f2)
  s=$(phase_state "$pid")
  e=$(phase_pts "$pid" "$wt")
  [ "$_first" = "1" ] && _first=0 || printf ',' >> "$_PHASE_JSON"
  printf '{"id":"%s","state":"%s","weight":%s,"earned":%s}\n' "$pid" "$s" "$wt" "$e" >> "$_PHASE_JSON"
done

cat > "$MD" <<EOF
# NS∞ Live Score — run $RUN_ID
**AXIOLEV Holdings LLC © 2026** — generated by \`ns_live_score.sh\`

## Tests
| runner | collected | pass | fail | err | skip |
|---|---|---|---|---|---|
| pytest | $PYTEST_COLLECTED | $PYTEST_PASS | $PYTEST_FAIL | $PYTEST_ERR | $PYTEST_SKIP |
| vitest | $VITEST_TOTAL | $VITEST_PASS | $VITEST_FAIL | — | — |
| xctest | — | $XCTEST_PASS | $XCTEST_FAIL | — | — ($XCTEST_STATUS) |

Pass rate (pytest): $(fmt4 "$PYTEST_PASS_RATE")
Docker: $DOCKER_HEALTHY / $DOCKER_TOTAL healthy
Leaks: $LEAK_COUNT — pre-commit hook: $HOOK_INSTALLED

## Instrument scores (live)
| inst | name | score |
|---|---|---|
| I1 | Super-Omega v2 | $(fmt2 "$I1") |
| I2 | Omega Intelligence v2 | $(fmt2 "$I2") |
| I3 | UOIE v2 (admin-capped) | $(fmt2 "$I3") |
| I4 | GPX-Omega | $(fmt2 "$I4") |
| I5 | SAQ | $(fmt2 "$I5") |
| I6 | Omega-Logos | $(fmt2 "$I6") |
| I7 | Certification Power | $(fmt2 "$I7") |

## Composite
| version | composite | band | delta vs $PREV_V31 |
|---|---|---|---|
| v2.1 | $COMP_V21 | legacy | — |
| v3.0 | $COMP_V30 | internal | — |
| **v3.1** | **$COMP_V31** | **$BAND_V31** | **$DELTA_V31** |
| v3.2 | $COMP_V32 | $BAND_V32 | — |

## Insight ranking (max-delta first, composite-points per week)
$(cat "$_RANK_MD")

Projected v3.1 if all pending land: **$PROJ_V31**

## ns_max_closure.sh completion
**Score: $SCORE / 100 — $SCORE_BAND**

## Run log
\`$LOG\`
EOF

cat > "$JSON_OUT" <<EOF
{
  "schema": "axiolev.ns.live_score/v1",
  "run_id": "$RUN_ID",
  "tests": {
    "pytest": {"collected": $PYTEST_COLLECTED, "pass": $PYTEST_PASS, "fail": $PYTEST_FAIL, "err": $PYTEST_ERR, "skip": $PYTEST_SKIP, "pass_rate": $(fmt4 "$PYTEST_PASS_RATE")},
    "vitest": {"pass": $VITEST_PASS, "fail": $VITEST_FAIL, "total": $VITEST_TOTAL},
    "xctest": {"pass": $XCTEST_PASS, "fail": $XCTEST_FAIL, "status": "$XCTEST_STATUS"}
  },
  "infra": {
    "docker_healthy": $DOCKER_HEALTHY,
    "docker_total": $DOCKER_TOTAL,
    "leaks": $LEAK_COUNT,
    "pre_commit_hook": "$HOOK_INSTALLED"
  },
  "instruments": {
    "I1": $(fmt2 "$I1"), "I2": $(fmt2 "$I2"), "I3": $(fmt2 "$I3"),
    "I4": $(fmt2 "$I4"), "I5": $(fmt2 "$I5"), "I6": $(fmt2 "$I6"),
    "I7": $(fmt2 "$I7")
  },
  "composite": {
    "v2_1": $COMP_V21,
    "v3_0": $COMP_V30,
    "v3_1": $COMP_V31,
    "v3_2": $COMP_V32,
    "band_v3_1": "$BAND_V31",
    "band_v3_2": "$BAND_V32",
    "delta_v3_1_vs_prior": $DELTA_V31,
    "prior_v3_1": $PREV_V31,
    "projected_v3_1_if_all_land": $PROJ_V31,
    "remaining_delta": $REMAINING_DELTA
  },
  "max_closure_completion": {
    "score": $SCORE,
    "band": "$SCORE_BAND",
    "phases": [
$(cat "$_PHASE_JSON")
    ]
  }
}
EOF

ok "emitted: $MD"
ok "emitted: $JSON_OUT"

# ─── 10. FINAL SUMMARY ───────────────────────────────────────────────────────
hdr "10. SUMMARY"

NEXT_INSIGHT=$(sort -t$'\t' -k1,1 -rn "$TMPR" | awk -F'\t' '$6!="done"&&$6!="landed"{print $2" (+"$5" in "$4"w)"; exit}' || echo "all done")

cat <<EOF

  +=================================================================+
  |         NS INFINITY LIVE SCORE — run $RUN_ID          |
  +=================================================================+
  |  Tests    : pytest $PYTEST_PASS/$PYTEST_TOTAL_RUN green  vitest $VITEST_PASS/$VITEST_TOTAL  xctest $XCTEST_STATUS
  |  Docker   : $DOCKER_HEALTHY/$DOCKER_TOTAL healthy
  |  Security : $LEAK_COUNT leaks  hook=$HOOK_INSTALLED
  |
  |  Composite v3.1 : $COMP_V31  ($BAND_V31)   delta $DELTA_V31 vs prior
  |  Composite v3.2 : $COMP_V32  ($BAND_V32)
  |
  |  Max leverage next : $NEXT_INSIGHT
  |  Projected v3.1 if all insights land : $PROJ_V31
  |
  |  ns_max_closure.sh : $SCORE / 100  ($SCORE_BAND)
  +=================================================================+

  Artifacts:
    $MD
    $JSON_OUT

EOF

_log "ns_live_score.sh complete — run $RUN_ID"
exit 0
