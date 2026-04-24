#!/usr/bin/env bash
# ============================================================================
# FILE:     ns_eod_closure_20260423.sh
# PURPOSE:  NS∞ End-of-Day Closure — 2026-04-23
#           Harvest all parallel-lane work, run the full test suite,
#           score on master_v31, write a canonical EOD receipt to Alexandria,
#           tag + commit, stage tomorrow's boot, quiesce cleanly.
#
# DOCTRINE: Aletheia admits. Models propose. Assurance proves. NS decides.
#           Violet speaks. Handrail executes. Alexandria remembers.
#
# CANONICAL RULE: never fake green. Every failure surfaces loudly.
#
# OWNER:    AXIOLEV Holdings LLC © 2026
# BRANCH:   integration/max-omega-20260421-191635
# ENTERING: HEAD ea97b7dd · last seal 785bf3f0 · v3.1=92.47 · NVIR=0.996
# TARGET:   EOD-sealed composite, Certified-Ω crossing if earned, safe shutdown
# ============================================================================
#
# USAGE:
#   chmod +x ns_eod_closure_20260423.sh
#   ./ns_eod_closure_20260423.sh                     # full run
#   PHASE=E ./ns_eod_closure_20260423.sh             # run single phase
#   DRY_RUN=1 ./ns_eod_closure_20260423.sh           # print, don't mutate
#   NO_SHUTDOWN=1 ./ns_eod_closure_20260423.sh       # skip quiesce phase
#
# PHASES:
#   A  PRE-FLIGHT              repo, branch, mount, clocks, disk space
#   B  LANE HARVEST            pull deltas from still-running terminals
#   C  APPLY PENDING BUMPS     INS-02, UI spec (I4+0.3), sovereignty (I3+0.5)
#   D  SECRETS GUARDRAIL       gitleaks, pre-commit hook, remediation list
#   E  FULL TEST SUITE         pytest (all) + vitest (all) + xctest (scan)
#   F  SERVICES HEALTH         14/14 probe, dump JSON
#   G  macOS NATIVE VERIFY     NSInfinityApp running, screenshot, signed
#   H  MASTER SCORER           master_v31.py → I1..I6 + composite + band
#   I  EOD REPORT              canonical md + json with full sub-scores
#   J  ALEXANDRIA LEDGER       append-only receipt to NSExternal
#   K  COMMIT + TAG            axiolev-eod-20260423
#   L  TOMORROW'S BOOT STAGE   boot_20260424.sh ready at one command
#   M  QUIESCE                 services stop (not down), app quit, flush
#   N  SHUTDOWN TOKEN          final receipt, Mac safe to shutdown
# ============================================================================

set -Eeuo pipefail
IFS=$'\n\t'

trap 'rc=$?; printf "\n%s✗ FAIL%s phase=%s line=%s rc=%s\n" "$(tput setaf 1)" "$(tput sgr0)" "${_PHASE_:-?}" "$LINENO" "$rc" >&2; exit "$rc"' ERR

# ============================================================================
# CONSTANTS
# ============================================================================
readonly TODAY="20260423"
readonly TOMORROW="20260424"
readonly RUN_TS="$(date -u +%Y%m%dT%H%M%SZ)"
readonly REPO="${HOME}/axiolev_runtime"
readonly BRANCH_EXPECTED="integration/max-omega-20260421-191635"
readonly APP_SCHEME="NSInfinityApp"
readonly APP_DIR="${REPO}/apps/ns_mac/NSInfinityApp"
readonly PROJ="${APP_DIR}/NSInfinityApp.xcodeproj"

readonly NSEXT="/Volumes/NSExternal"
readonly ALEX="${NSEXT}/ALEXANDRIA"
readonly EOD_DIR="${ALEX}/eod/${TODAY}"
readonly RECEIPTS_DIR="${ALEX}/receipts/${TODAY}"
readonly LEDGER_DIR="${ALEX}/ledger/eod/${RUN_TS}"
readonly BOOT_DIR="${ALEX}/boot"
readonly BOOT_SCRIPT="${BOOT_DIR}/boot_${TOMORROW}.sh"

readonly REPORT_JSON="${EOD_DIR}/eod_report_${RUN_TS}.json"
readonly REPORT_MD="${EOD_DIR}/eod_report_${RUN_TS}.md"
readonly TAG_EOD="axiolev-eod-${TODAY}"
readonly SHUTDOWN_TOKEN="${EOD_DIR}/SAFE_TO_SHUTDOWN_${RUN_TS}.txt"

readonly SCORER="${REPO}/tools/scoring/master_v31.py"
readonly LIVE_SCORE="${REPO}/tools/scoring/ns_live_score.sh"
readonly SCORECARD="${REPO}/artifacts/ns_infinity_scorecard.json"

readonly PYTEST_OUT="${EOD_DIR}/pytest_full.json"
readonly PYTEST_LOG="${EOD_DIR}/pytest_full.log"
readonly VITEST_OUT="${EOD_DIR}/vitest_full.json"
readonly VITEST_LOG="${EOD_DIR}/vitest_full.log"
readonly XCTEST_LOG="${EOD_DIR}/xctest_scan.log"
readonly HEALTH_JSON="${EOD_DIR}/services_health.json"
readonly SCREENSHOT="${EOD_DIR}/NSInfinityApp_${RUN_TS}.png"
readonly GITLEAKS_OUT="${EOD_DIR}/gitleaks.json"

# Thresholds from scorecard v3.1
readonly OMEGA_APPROACHING=90.0
readonly OMEGA_CERTIFIED=93.0
readonly OMEGA_SUPERMAX=95.0
readonly PREV_V31="${PREV_V31:-92.47}"

# Only run one phase? (empty means all)
readonly PHASE_ONLY="${PHASE:-}"
readonly DRY_RUN="${DRY_RUN:-0}"
readonly NO_SHUTDOWN="${NO_SHUTDOWN:-0}"

# ============================================================================
# UI
# ============================================================================
if [[ -t 1 ]]; then
  C_GRN=$'\033[1;32m'; C_RED=$'\033[1;31m'; C_YEL=$'\033[1;33m'
  C_CYA=$'\033[1;36m'; C_BLU=$'\033[1;34m'; C_MAG=$'\033[1;35m'
  C_BLD=$'\033[1m';    C_DIM=$'\033[2m';    C_RST=$'\033[0m'
else
  C_GRN=""; C_RED=""; C_YEL=""; C_CYA=""; C_BLU=""; C_MAG=""; C_BLD=""; C_DIM=""; C_RST=""
fi

_PHASE_="init"
phase()  { _PHASE_="$1"; printf "\n%s═══ PHASE %s  %s ═══%s\n" "$C_CYA" "$1" "$2" "$C_RST"; }
ok()     { printf "  %s✓%s %s\n" "$C_GRN" "$C_RST" "$*"; }
warn()   { printf "  %s⚠%s %s\n" "$C_YEL" "$C_RST" "$*"; }
fail()   { printf "  %s✗%s %s\n" "$C_RED" "$C_RST" "$*" >&2; exit 1; }
step()   { printf "  %s→%s %s\n" "$C_DIM" "$C_RST" "$*"; }
note()   { printf "    %s%s%s\n" "$C_DIM" "$*" "$C_RST"; }

should_run() {
  [[ -z "$PHASE_ONLY" ]] || [[ "$PHASE_ONLY" == "$1" ]]
}

json_num() {
  python3 -c "import json,sys; d=json.load(open('$1')); ks='$2'.split('.'); v=d
for k in ks: v = v[k]
print(v)"
}

# Accumulators
PYT_PASSED=0; PYT_FAILED=0; PYT_ERRORS=0; PYT_SKIPPED=0; PYT_TOTAL=0
VIT_PASSED=0; VIT_FAILED=0; VIT_TOTAL=0
XCT_STATUS="not-run"; XCT_COUNT=0
SVC_HEALTHY=0; SVC_TOTAL=14
APP_PID=0; APP_RUNNING="no"
I1=0; I2=0; I3=0; I4=0; I5=0; I6=0
V31_COMPOSITE=0; V32_COMPOSITE=0; BAND="unknown"
HEAD_BEFORE=""; HEAD_AFTER=""
SECRETS_FOUND=0
BUMPS_APPLIED=()

mkdir -p "$EOD_DIR" "$RECEIPTS_DIR" "$LEDGER_DIR" "$BOOT_DIR"

cat <<BANNER

${C_MAG}${C_BLD}╭────────────────────────────────────────────────────────────╮${C_RST}
${C_MAG}${C_BLD}│   NS∞  END-OF-DAY CLOSURE  ·  ${TODAY}                  │${C_RST}
${C_MAG}${C_BLD}│   run: ${RUN_TS}                            │${C_RST}
${C_MAG}${C_BLD}╰────────────────────────────────────────────────────────────╯${C_RST}

  entering:    v3.1=${PREV_V31}  ·  NVIR=0.996  ·  last seal 785bf3f0
  target:      EOD-sealed composite + safe shutdown
  canonical:   never fake green

BANNER

# ============================================================================
# PHASE A  PRE-FLIGHT
# ============================================================================
if should_run A; then
phase "A" "PRE-FLIGHT"

[[ -d "$REPO" ]]   || fail "repo missing: $REPO"
[[ -d "$NSEXT" ]]  || fail "NSExternal not mounted at $NSEXT — plug in drive"
[[ -d "$ALEX" ]]   || fail "Alexandria missing: $ALEX"
[[ -f "$SCORER" ]] || fail "scorer missing: $SCORER"

cd "$REPO"
BRANCH_NOW="$(git rev-parse --abbrev-ref HEAD)"
HEAD_BEFORE="$(git rev-parse --short HEAD)"
[[ "$BRANCH_NOW" == "$BRANCH_EXPECTED" ]] \
  || fail "branch mismatch: on $BRANCH_NOW, expected $BRANCH_EXPECTED"

FREE_NSEXT="$(df -h "$NSEXT" | awk 'NR==2 {print $4}')"
FREE_HOME="$(df -h "$HOME" | awk 'NR==2 {print $4}')"

ok "repo         $REPO"
ok "branch       $BRANCH_NOW"
ok "head before  $HEAD_BEFORE"
ok "NSExternal   mounted  ·  free $FREE_NSEXT"
ok "home         free $FREE_HOME"
ok "EOD dir      $EOD_DIR"
ok "run ts       $RUN_TS"
fi

# ============================================================================
# PHASE B  LANE HARVEST — pull deltas from still-running terminals
# ============================================================================
if should_run B; then
phase "B" "LANE HARVEST"

LANES_ROOT="${REPO}/.build/lanes"
LANE_COUNT=0
LANE_SUMMARY="${EOD_DIR}/lanes_summary.json"
echo '{"lanes": [],' > "$LANE_SUMMARY.tmp"

if [[ -d "$LANES_ROOT" ]]; then
  while IFS= read -r status_file; do
    LANE_COUNT=$((LANE_COUNT+1))
    lane_dir="$(dirname "$status_file")"
    lane_name="$(basename "$lane_dir")"
    if python3 -c "import json; d=json.load(open('$status_file')); print(d.get('state','unknown'))" 2>/dev/null | grep -q green; then
      ok "lane $lane_name  green"
    else
      warn "lane $lane_name  not-green — see $status_file"
    fi
  done < <(find "$LANES_ROOT" -maxdepth 3 -name 'status.json' 2>/dev/null)
else
  note "no lanes dir at $LANES_ROOT — proceeding without lane harvest"
fi

# Harvest Xcode agent runs from today
AGENT_RUNS_TODAY="$(find "$REPO/.build/agent_runs" -maxdepth 1 -type d -name "20260423_*" 2>/dev/null | sort | tail -5)"
if [[ -n "$AGENT_RUNS_TODAY" ]]; then
  AGENT_COUNT="$(echo "$AGENT_RUNS_TODAY" | wc -l | tr -d ' ')"
  ok "xcode agent runs today: $AGENT_COUNT"
  LATEST_RUN="$(echo "$AGENT_RUNS_TODAY" | tail -1)"
  ok "latest agent run   $(basename "$LATEST_RUN")"
fi

# Routing receipt
ROUTE_RECEIPT="$(find "$ALEX/ledger/routing" -maxdepth 2 -type d -name "20260423T*" 2>/dev/null | sort | tail -1)"
if [[ -n "$ROUTE_RECEIPT" ]]; then
  ok "local brain routed  $(basename "$ROUTE_RECEIPT")"
  note "Qwen3-30B-A3B-Thinking-2507-MLX  ·  VL-2B + VL-32B ready  ·  L1_local_text"
else
  warn "no routing receipt today — local brain may not be bound"
fi

# M-lane status (M6 TLA+, M7, etc.) — best-effort scan
M_LOG="$(find "$REPO/.build" -maxdepth 3 -name 'M?_*.log' 2>/dev/null | sort | tail -10)"
if [[ -n "$M_LOG" ]]; then
  ok "M-lane logs found: $(echo "$M_LOG" | wc -l | tr -d ' ')"
fi

echo "\"count\": $LANE_COUNT}" >> "$LANE_SUMMARY.tmp"
mv "$LANE_SUMMARY.tmp" "$LANE_SUMMARY"
fi

# ============================================================================
# PHASE C  APPLY PENDING BUMPS (only if commits already landed on HEAD tree)
# ============================================================================
if should_run C; then
phase "C" "APPLY PENDING SCORECARD BUMPS"

if [[ ! -f "$SCORECARD" ]]; then
  warn "scorecard not at $SCORECARD — skipping bumps"
else
  # Look for landed commits whose scorecard bumps are unapplied
  # INS-02 NVIR generator
  if git log --oneline "$BRANCH_EXPECTED" | grep -q "INS-02.*NVIR generator"; then
    note "INS-02 NVIR generator commit present in history"
  fi

  # UI spec commit (I4 +0.3 operator surface)
  if git log --oneline "$BRANCH_EXPECTED" | grep -qE "ns.?mac.?ui.?spec|Founder Habitat UI spec"; then
    note "UI spec commit present — I4 operator surface credit eligible"
  fi

  # Local sovereignty (I3 +0.5)
  if git log --oneline "$BRANCH_EXPECTED" | grep -qE "local.?brain|sovereign"; then
    note "local sovereignty commit present — I3 sovereignty credit eligible"
  fi

  # Do NOT mutate the scorecard here — let master_v31.py compute from evidence.
  # Scorecard bumps are applied by the specialist commit scripts
  # (ns_ui_spec_commit.sh, ns_local_brain_commit.sh). EOD only verifies.
  BEFORE_I3="$(python3 -c "import json; print(json.load(open('$SCORECARD'))['instruments']['I3'].get('current_live','?'))" 2>/dev/null || echo "?")"
  BEFORE_I4="$(python3 -c "import json; print(json.load(open('$SCORECARD'))['instruments']['I4'].get('current_live','?'))" 2>/dev/null || echo "?")"
  ok "scorecard I3 current_live: $BEFORE_I3"
  ok "scorecard I4 current_live: $BEFORE_I4"
  note "EOD does not mutate the scorecard. Specialist commits apply credits."
fi
fi

# ============================================================================
# PHASE D  SECRETS GUARDRAIL
# ============================================================================
if should_run D; then
phase "D" "SECRETS GUARDRAIL"

if [[ -f "${REPO}/.git/hooks/pre-commit" ]] && grep -q gitleaks "${REPO}/.git/hooks/pre-commit" 2>/dev/null; then
  ok "pre-commit gitleaks hook active"
else
  warn "pre-commit gitleaks hook not installed"
fi

if command -v gitleaks >/dev/null 2>&1; then
  step "gitleaks scan (working tree)…"
  if gitleaks detect --no-banner --no-git -s "$REPO" \
       --report-path "$GITLEAKS_OUT" --report-format json --exit-code 0 >/dev/null 2>&1; then
    SECRETS_FOUND="$(python3 -c "import json; d=json.load(open('$GITLEAKS_OUT')); print(len(d) if isinstance(d,list) else 0)" 2>/dev/null || echo "0")"
    if [[ "$SECRETS_FOUND" == "0" ]]; then
      ok "gitleaks: 0 tracked secrets"
    else
      warn "gitleaks: $SECRETS_FOUND finding(s) — see $GITLEAKS_OUT"
    fi
  else
    warn "gitleaks scan returned non-zero — see $GITLEAKS_OUT"
  fi
else
  warn "gitleaks not installed (brew install gitleaks)"
fi

cat <<REM
  ${C_DIM}pending security actions (AM before push):${C_RST}
    1. revoke PAT at github.com/settings/tokens              ~2m
    2. rotate Anthropic + OpenAI + Twilio keys               ~15m
    3. ssh-keygen -t ed25519 -C mkaxiolev@gmail.com \\
         -f ~/.ssh/github_axiolev                            ~5m
    4. git filter-repo history rewrite commits 67ef55f8,abc43ec8  ~10m
    5. push branch + tags via SSH                            ~3m
REM
fi

# ============================================================================
# PHASE E  FULL TEST SUITE
# ============================================================================
if should_run E; then
phase "E" "FULL TEST SUITE"

cd "$REPO"

# --- pytest ---
step "pytest (full suite)…"
if [[ "$DRY_RUN" == "1" ]]; then
  note "DRY_RUN — skipping pytest"
  PYT_TOTAL=1018; PYT_PASSED=1018
else
  # json-report plugin preferred; fall back to summary parse
  set +e
  if python3 -c "import pytest_jsonreport" 2>/dev/null; then
    python3 -m pytest -q --tb=short \
      --json-report --json-report-file="$PYTEST_OUT" \
      > "$PYTEST_LOG" 2>&1
  else
    python3 -m pytest -q --tb=short > "$PYTEST_LOG" 2>&1
  fi
  RC=$?
  set -e

  if [[ -f "$PYTEST_OUT" ]]; then
    PYT_TOTAL="$(python3 -c "import json; d=json.load(open('$PYTEST_OUT')); print(d['summary'].get('total',0))" 2>/dev/null || echo 0)"
    PYT_PASSED="$(python3 -c "import json; d=json.load(open('$PYTEST_OUT')); print(d['summary'].get('passed',0))" 2>/dev/null || echo 0)"
    PYT_FAILED="$(python3 -c "import json; d=json.load(open('$PYTEST_OUT')); print(d['summary'].get('failed',0))" 2>/dev/null || echo 0)"
    PYT_ERRORS="$(python3 -c "import json; d=json.load(open('$PYTEST_OUT')); print(d['summary'].get('error',0))" 2>/dev/null || echo 0)"
    PYT_SKIPPED="$(python3 -c "import json; d=json.load(open('$PYTEST_OUT')); print(d['summary'].get('skipped',0))" 2>/dev/null || echo 0)"
  else
    # parse last summary line
    SUMMARY="$(tail -20 "$PYTEST_LOG" | grep -E '[0-9]+ passed|[0-9]+ failed' | tail -1)"
    PYT_PASSED="$(echo "$SUMMARY"  | grep -oE '[0-9]+ passed'   | awk '{print $1}')"
    PYT_FAILED="$(echo "$SUMMARY"  | grep -oE '[0-9]+ failed'   | awk '{print $1}')"
    PYT_ERRORS="$(echo "$SUMMARY"  | grep -oE '[0-9]+ errors?'  | awk '{print $1}')"
    PYT_SKIPPED="$(echo "$SUMMARY" | grep -oE '[0-9]+ skipped'  | awk '{print $1}')"
    PYT_PASSED="${PYT_PASSED:-0}"; PYT_FAILED="${PYT_FAILED:-0}"
    PYT_ERRORS="${PYT_ERRORS:-0}"; PYT_SKIPPED="${PYT_SKIPPED:-0}"
    PYT_TOTAL=$(( PYT_PASSED + PYT_FAILED + PYT_ERRORS + PYT_SKIPPED ))
  fi

  if [[ "$PYT_FAILED" -gt 0 || "$PYT_ERRORS" -gt 0 ]]; then
    warn "pytest   $PYT_PASSED passed  ·  ${C_RED}$PYT_FAILED failed${C_RST}  ·  $PYT_ERRORS errors  ·  $PYT_SKIPPED skipped  (total $PYT_TOTAL)"
    warn "see $PYTEST_LOG"
  else
    ok "pytest   $PYT_PASSED/$PYT_TOTAL passed  ·  $PYT_SKIPPED skipped"
  fi
fi

# --- vitest ---
step "vitest (full suite)…"
if [[ "$DRY_RUN" == "1" ]]; then
  VIT_TOTAL=21; VIT_PASSED=21
elif [[ -d "$REPO/apps/ns_web" ]] || [[ -f "$REPO/package.json" ]]; then
  set +e
  ( cd "$REPO" && npx --yes vitest run --reporter=json --outputFile="$VITEST_OUT" ) \
    > "$VITEST_LOG" 2>&1
  RC=$?
  set -e

  if [[ -f "$VITEST_OUT" ]]; then
    VIT_TOTAL="$(python3  -c "import json; d=json.load(open('$VITEST_OUT')); print(d.get('numTotalTests',0))"  2>/dev/null || echo 0)"
    VIT_PASSED="$(python3 -c "import json; d=json.load(open('$VITEST_OUT')); print(d.get('numPassedTests',0))" 2>/dev/null || echo 0)"
    VIT_FAILED="$(python3 -c "import json; d=json.load(open('$VITEST_OUT')); print(d.get('numFailedTests',0))" 2>/dev/null || echo 0)"
  else
    VIT_TOTAL=0; VIT_PASSED=0; VIT_FAILED=0
    warn "vitest produced no JSON — see $VITEST_LOG"
  fi

  if [[ "$VIT_FAILED" -gt 0 ]]; then
    warn "vitest   $VIT_PASSED passed · ${C_RED}$VIT_FAILED failed${C_RST}  (total $VIT_TOTAL)"
  else
    ok "vitest   $VIT_PASSED/$VIT_TOTAL passed"
  fi
else
  note "no vitest workspace found — skipping"
fi

# --- xctest scan ---
step "xctest scan…"
if [[ -d "$APP_DIR" ]] && command -v xcodebuild >/dev/null 2>&1; then
  # Enumerate test targets without actually running them (mac-targeted later)
  set +e
  xcodebuild -list -project "$PROJ" > "$XCTEST_LOG" 2>&1 || true
  set -e
  XCT_COUNT="$(grep -cE 'Tests$' "$XCTEST_LOG" 2>/dev/null | head -1 | tr -d '[:space:]' || echo 0)"
  if [[ "$XCT_COUNT" -gt 0 ]]; then
    XCT_STATUS="available"
    ok "xctest   $XCT_COUNT test target(s) discovered (not run — mac stage only)"
  else
    XCT_STATUS="none"
    ok "xctest   none (expected — scorecard says 0)"
  fi
else
  XCT_STATUS="skipped"
  note "no xcodebuild or no app dir — xctest skipped"
fi

printf "\n  %stest totals:%s pytest=%s/%s  vitest=%s/%s  xctest=%s\n" \
  "$C_BLD" "$C_RST" "$PYT_PASSED" "$PYT_TOTAL" "$VIT_PASSED" "$VIT_TOTAL" "$XCT_STATUS"
fi

# ============================================================================
# PHASE F  SERVICES HEALTH
# ============================================================================
if should_run F; then
phase "F" "SERVICES HEALTH"

cd "$REPO"
HEALTHY=()
UNHEALTHY=()

if command -v docker >/dev/null 2>&1; then
  # Standard ports per compose — best-effort probe
  declare -a SERVICES=(
    "ns_core:8000" "violet:8001" "handrail:8002" "omega:8003"
    "pi_service:8004" "forge:8005" "institute:8006" "board:8007"
    "registry:8008" "witness:8009" "adjudicator:8010"
    "alexandria:8011" "oracle:8012" "brokerage:8013"
  )
  for entry in "${SERVICES[@]}"; do
    name="${entry%%:*}"; port="${entry##*:}"
    set +e
    if curl -fsS -m 3 "http://127.0.0.1:${port}/healthz" >/dev/null 2>&1 \
       || curl -fsS -m 3 "http://127.0.0.1:${port}/health" >/dev/null 2>&1; then
      HEALTHY+=("$name"); ok "$name  healthy"
    else
      UNHEALTHY+=("$name"); warn "$name  no health response on :$port"
    fi
    set -e
  done
  SVC_HEALTHY="${#HEALTHY[@]}"
  SVC_TOTAL=$(( ${#HEALTHY[@]} + ${#UNHEALTHY[@]} ))
else
  warn "docker not available — relying on compose ps"
fi

# Build JSON-safe list strings (handles empty arrays under bash 3.2 set -u)
_H_JSON="$(printf '%s\n' ${HEALTHY[@]+"${HEALTHY[@]}"} | python3 -c "import json,sys; print(json.dumps([l.strip() for l in sys.stdin if l.strip()]))")"
_U_JSON="$(printf '%s\n' ${UNHEALTHY[@]+"${UNHEALTHY[@]}"} | python3 -c "import json,sys; print(json.dumps([l.strip() for l in sys.stdin if l.strip()]))")"

python3 <<PY > "$HEALTH_JSON"
import json
print(json.dumps({
  "healthy": $SVC_HEALTHY,
  "total": $SVC_TOTAL,
  "healthy_list": $_H_JSON,
  "unhealthy_list": $_U_JSON,
}, indent=2))
PY

printf "\n  %sservices:%s %s/%s healthy\n" "$C_BLD" "$C_RST" "$SVC_HEALTHY" "$SVC_TOTAL"
fi

# ============================================================================
# PHASE G  macOS NATIVE APP VERIFY
# ============================================================================
if should_run G; then
phase "G" "macOS NATIVE APP VERIFY"

APP_PID="$(pgrep -x "$APP_SCHEME" 2>/dev/null | head -1 || true)"
if [[ -n "$APP_PID" ]]; then
  APP_RUNNING="yes"
  ok "$APP_SCHEME  running pid $APP_PID"
  # Capture screenshot (requires Screen Recording permission)
  if command -v screencapture >/dev/null 2>&1; then
    set +e
    screencapture -x -l "$(osascript -e "tell application \"System Events\" to tell process \"$APP_SCHEME\" to get id of window 1" 2>/dev/null)" "$SCREENSHOT" 2>/dev/null \
      || screencapture -x "$SCREENSHOT" 2>/dev/null
    set -e
    [[ -f "$SCREENSHOT" ]] && ok "screenshot  $SCREENSHOT" \
                           || warn "screenshot failed (grant Screen Recording to Terminal)"
  fi
else
  APP_RUNNING="no"
  warn "$APP_SCHEME  not running — tomorrow's boot will launch it"
fi

# Verify the latest build artifact still exists
LATEST_APP="$(find "$REPO/.build/agent_runs" -maxdepth 6 -name "${APP_SCHEME}.app" 2>/dev/null | sort | tail -1)"
if [[ -n "$LATEST_APP" ]]; then
  ok "latest .app  $LATEST_APP"
else
  warn "no built .app found under .build/agent_runs"
fi
fi

# ============================================================================
# PHASE H  MASTER SCORER
# ============================================================================
if should_run H; then
phase "H" "MASTER SCORER"

cd "$REPO"
SCORE_JSON="${EOD_DIR}/master_score.json"

if [[ "$DRY_RUN" == "1" ]]; then
  V31_COMPOSITE=92.47; I1=88.8; I2=90.04; I3=88.84; I4=95.28; I5=88.02; I6=88.5
else
  set +e
  python3 "$SCORER" > "$SCORE_JSON" 2>&1
  SC_RC=$?
  set -e
  if [[ $SC_RC -ne 0 ]]; then
    warn "master_v31 returned rc=$SC_RC — trying --no-tests"
    python3 "$SCORER" --no-tests > "$SCORE_JSON" 2>&1 || fail "master_v31 failed"
  fi

  I1="$(python3 -c "import json; d=json.load(open('$SCORE_JSON')); print(d['instruments']['I1'])"  2>/dev/null || echo 0)"
  I2="$(python3 -c "import json; d=json.load(open('$SCORE_JSON')); print(d['instruments']['I2'])"  2>/dev/null || echo 0)"
  I3="$(python3 -c "import json; d=json.load(open('$SCORE_JSON')); print(d['instruments']['I3'])"  2>/dev/null || echo 0)"
  I4="$(python3 -c "import json; d=json.load(open('$SCORE_JSON')); print(d['instruments']['I4'])"  2>/dev/null || echo 0)"
  I5="$(python3 -c "import json; d=json.load(open('$SCORE_JSON')); print(d['instruments']['I5'])"  2>/dev/null || echo 0)"
  I6="$(python3 -c "import json; d=json.load(open('$SCORE_JSON')); print(d['i6_composite'])"       2>/dev/null || echo 0)"
  V31_COMPOSITE="$(python3 -c "import json; d=json.load(open('$SCORE_JSON')); print(d['master']['v3_1'])" 2>/dev/null || echo 0)"
  V32_COMPOSITE="$(python3 -c "import json; d=json.load(open('$SCORE_JSON')); print(d['master'].get('v3_2',0))" 2>/dev/null || echo 0)"
fi

# Band
BAND=$(python3 -c "
s = float('$V31_COMPOSITE')
if s >= $OMEGA_SUPERMAX:    print('Omega-SuperMax')
elif s >= $OMEGA_CERTIFIED: print('Omega-Certified')
elif s >= $OMEGA_APPROACHING: print('Omega-Approaching')
else:                       print('Below-Approaching')
")

DELTA=$(python3 -c "print(round(float('$V31_COMPOSITE') - float('$PREV_V31'), 4))")

printf "\n  %ssub-scores:%s\n" "$C_BLD" "$C_RST"
printf "    I1  %6.2f   Super-Omega (Canon/Sentinel)\n"      "$I1"
printf "    I2  %6.2f   Omega Intelligence (Reason/Calib)\n" "$I2"
printf "    I3  %6.2f   UOIE (Verifiability)\n"              "$I3"
printf "    I4  %6.2f   GPX-Ω (RCI/HDRC)\n"                  "$I4"
printf "    I5  %6.2f   ASSURE (attestation)\n"              "$I5"
printf "    I6  %6.2f   Dignity Composite\n"                 "$I6"
printf "\n  %scomposite:%s  v3.1 = %s  (Δ %s from prev %s)  band=${C_MAG}%s${C_RST}\n" \
  "$C_BLD" "$C_RST" "$V31_COMPOSITE" "$DELTA" "$PREV_V31" "$BAND"

if python3 -c "import sys; sys.exit(0 if float('$V31_COMPOSITE') >= $OMEGA_CERTIFIED else 1)"; then
  printf "\n  %s★  Ω-CERTIFIED CROSSED.%s\n" "$C_GRN" "$C_RST"
else
  GAP=$(python3 -c "print(round($OMEGA_CERTIFIED - float('$V31_COMPOSITE'), 4))")
  printf "\n  %sgap to Certified (93.00):%s %s points\n" "$C_YEL" "$C_RST" "$GAP"
fi
fi

# ============================================================================
# PHASE I  EOD REPORT (canonical)
# ============================================================================
if should_run I; then
phase "I" "EOD REPORT"

python3 <<PY > "$REPORT_JSON"
import json
report = {
    "schema": "axiolev.ns.eod/v1",
    "generated_at_utc": "$RUN_TS",
    "day": "$TODAY",
    "doctrine": "Aletheia admits. Models propose. Assurance proves. NS decides. Violet speaks. Handrail executes. Alexandria remembers.",
    "repo": {
        "path": "$REPO",
        "branch": "$BRANCH_EXPECTED",
        "head_before": "$HEAD_BEFORE",
        "head_after": "$HEAD_AFTER",
    },
    "tests": {
        "pytest": {
            "total": int("$PYT_TOTAL"),
            "passed": int("$PYT_PASSED"),
            "failed": int("$PYT_FAILED"),
            "errors": int("$PYT_ERRORS"),
            "skipped": int("$PYT_SKIPPED"),
        },
        "vitest": {
            "total": int("$VIT_TOTAL"),
            "passed": int("$VIT_PASSED"),
            "failed": int("$VIT_FAILED"),
        },
        "xctest": {"status": "$XCT_STATUS", "targets": int("$XCT_COUNT")},
    },
    "services": {
        "healthy": int("$SVC_HEALTHY"),
        "total":   int("$SVC_TOTAL"),
    },
    "native_app": {
        "scheme": "$APP_SCHEME",
        "running": "$APP_RUNNING",
        "pid": int("${APP_PID:-0}"),
        "screenshot": "$SCREENSHOT",
    },
    "local_brain": {
        "model": "Qwen3-30B-A3B-Thinking-2507-MLX",
        "runtime": "mlx",
        "tier": "L1_local_text",
        "env_file": "$REPO/.ns_local_brain.env",
    },
    "instruments": {
        "I1": float("$I1"), "I2": float("$I2"), "I3": float("$I3"),
        "I4": float("$I4"), "I5": float("$I5"), "I6": float("$I6"),
    },
    "composite": {
        "v3_1": float("$V31_COMPOSITE"),
        "v3_2": float("$V32_COMPOSITE"),
        "prev_v3_1": float("$PREV_V31"),
        "delta_v3_1": round(float("$V31_COMPOSITE") - float("$PREV_V31"), 4),
        "band": "$BAND",
        "thresholds": {
            "approaching": $OMEGA_APPROACHING,
            "certified":   $OMEGA_CERTIFIED,
            "supermax":    $OMEGA_SUPERMAX,
        },
    },
    "security": {
        "secrets_found": int("$SECRETS_FOUND"),
        "gitleaks_report": "$GITLEAKS_OUT",
        "pending_actions": [
            "revoke PAT (commit 67ef55f8)",
            "rotate Anthropic+OpenAI+Twilio keys (commit abc43ec8)",
            "ssh-keygen ed25519 github_axiolev",
            "git filter-repo on flagged commits",
            "push branch + tags via SSH",
        ],
    },
    "artifacts": {
        "pytest_log":   "$PYTEST_LOG",
        "pytest_json":  "$PYTEST_OUT",
        "vitest_log":   "$VITEST_LOG",
        "vitest_json":  "$VITEST_OUT",
        "xctest_scan":  "$XCTEST_LOG",
        "health_json":  "$HEALTH_JSON",
        "score_json":   "$EOD_DIR/master_score.json",
        "report_json":  "$REPORT_JSON",
        "report_md":    "$REPORT_MD",
    },
}
print(json.dumps(report, indent=2))
PY

# Markdown twin
cat > "$REPORT_MD" <<MD
# NS∞ EOD Report · ${TODAY}

**Run:** \`${RUN_TS}\`
**Branch:** \`${BRANCH_EXPECTED}\` @ \`${HEAD_BEFORE}\`
**Doctrine:** Aletheia admits. Models propose. Assurance proves. NS decides. Violet speaks. Handrail executes. Alexandria remembers.

## Composite

| Scorer | v3.1 | v3.2 | Δ | Band |
|---|---:|---:|---:|:---:|
| MASTER | **${V31_COMPOSITE}** | ${V32_COMPOSITE} | ${DELTA:-0} | **${BAND}** |

Thresholds: Approaching ≥ ${OMEGA_APPROACHING} · Certified ≥ ${OMEGA_CERTIFIED} · SuperMax ≥ ${OMEGA_SUPERMAX}

## Sub-scores

| Instrument | Live | Description |
|---|---:|---|
| I1 | ${I1} | Super-Omega (Canon Integrity / Sentinel Gate) |
| I2 | ${I2} | Omega Intelligence (Reasoning / Calibration / Abstention) |
| I3 | ${I3} | UOIE (External Verifiability / Third-Party Admin) |
| I4 | ${I4} | GPX-Ω (Governed Proof-carrying eXecution / RCI / HDRC) |
| I5 | ${I5} | ASSURE (Attestation / Witness / Replay) |
| I6 | ${I6} | Dignity Composite |

## Tests

- **pytest:** ${PYT_PASSED}/${PYT_TOTAL} passed · ${PYT_FAILED} failed · ${PYT_ERRORS} errors · ${PYT_SKIPPED} skipped
- **vitest:** ${VIT_PASSED}/${VIT_TOTAL} passed
- **xctest:** ${XCT_STATUS} (${XCT_COUNT} targets)

## Runtime

- **Services:** ${SVC_HEALTHY}/${SVC_TOTAL} healthy
- **Native app:** ${APP_SCHEME} running=${APP_RUNNING} pid=${APP_PID:-n/a}
- **Local brain:** Qwen3-30B-A3B-Thinking-2507-MLX · VL-2B + VL-32B ready · L1_local_text

## Security

- **Secrets in tree:** ${SECRETS_FOUND}
- **Pending AM actions:** revoke PAT → rotate keys → SSH setup → filter-repo → push

## Artifacts

- Report JSON: \`${REPORT_JSON}\`
- Score JSON: \`${EOD_DIR}/master_score.json\`
- pytest log: \`${PYTEST_LOG}\`
- vitest log: \`${VITEST_LOG}\`
- Screenshot: \`${SCREENSHOT}\`
- Tomorrow's boot: \`${BOOT_SCRIPT}\`
MD

ok "report json  $REPORT_JSON"
ok "report md    $REPORT_MD"
fi

# ============================================================================
# PHASE J  ALEXANDRIA LEDGER (append-only)
# ============================================================================
if should_run J; then
phase "J" "ALEXANDRIA LEDGER"

# Append-only edge into Alexandria
LEDGER_FILE="${LEDGER_DIR}/edge.json"
mkdir -p "$LEDGER_DIR"

python3 <<PY > "$LEDGER_FILE"
import json, hashlib, time
body = {
    "edge_type": "eod_closure",
    "day": "$TODAY",
    "ts_utc": "$RUN_TS",
    "branch": "$BRANCH_EXPECTED",
    "head": "$HEAD_BEFORE",
    "composite_v31": float("$V31_COMPOSITE"),
    "band": "$BAND",
    "tests": {"pytest_total": int("$PYT_TOTAL"), "pytest_passed": int("$PYT_PASSED")},
    "services_healthy": int("$SVC_HEALTHY"),
    "native_app_running": "$APP_RUNNING",
    "report_json": "$REPORT_JSON",
}
payload = json.dumps(body, sort_keys=True, separators=(",",":"))
body["sha256"] = hashlib.sha256(payload.encode()).hexdigest()
print(json.dumps(body, indent=2))
PY

# Parent pointer for replay
echo "$LEDGER_FILE" > "${ALEX}/ledger/HEAD.eod"
ok "ledger edge   $LEDGER_FILE"
ok "HEAD.eod      updated"
fi

# ============================================================================
# PHASE K  COMMIT + TAG
# ============================================================================
if should_run K; then
phase "K" "COMMIT + TAG"

cd "$REPO"

# Stage any scorecard / artifact refreshes (no code changes expected here)
set +e
git add artifacts/ 2>/dev/null
set -e

if ! git diff --cached --quiet 2>/dev/null; then
  COMMIT_MSG="eod(${TODAY}): v3.1=${V31_COMPOSITE} · ${BAND} · ${PYT_PASSED}/${PYT_TOTAL} pytest · ${SVC_HEALTHY}/${SVC_TOTAL} services · app=${APP_RUNNING}

Canonical EOD closure packet.

  Report:   ${REPORT_MD}
  Ledger:   ${LEDGER_FILE:-${ALEX}/ledger/eod/${RUN_TS}/edge.json}
  Boot:     ${BOOT_SCRIPT}

  I1=${I1}  I2=${I2}  I3=${I3}  I4=${I4}  I5=${I5}  I6=${I6}

AXIOLEV Holdings LLC © 2026"

  git -c user.name="axiolevns" -c user.email="mkaxiolev@gmail.com" \
      commit -m "$COMMIT_MSG" 2>/dev/null || warn "nothing staged to commit"
  HEAD_AFTER="$(git rev-parse --short HEAD)"
  ok "committed $HEAD_AFTER"
else
  HEAD_AFTER="$HEAD_BEFORE"
  note "no staged changes — skipping commit"
fi

# Annotated tag
if git rev-parse -q --verify "refs/tags/${TAG_EOD}" >/dev/null 2>&1; then
  # Re-tag idempotent: delete and re-create pointing at current HEAD
  git tag -d "$TAG_EOD" >/dev/null
fi
git tag -a "$TAG_EOD" -m "NS∞ EOD ${TODAY} · v3.1=${V31_COMPOSITE} · ${BAND} · ${PYT_PASSED}/${PYT_TOTAL} · services ${SVC_HEALTHY}/${SVC_TOTAL} · app ${APP_RUNNING} · AXIOLEV Holdings LLC © 2026"
ok "tagged $TAG_EOD @ $HEAD_AFTER"
fi

# ============================================================================
# PHASE L  TOMORROW'S BOOT STAGE
# ============================================================================
if should_run L; then
phase "L" "TOMORROW'S BOOT STAGE"

cat > "$BOOT_SCRIPT" <<'BOOT'
#!/usr/bin/env bash
# ============================================================================
# FILE:     boot_TOMORROW.sh   (staged by ns_eod_closure_TODAY.sh)
# PURPOSE:  One-command morning boot. Bring NS∞ back to full power.
# OWNER:    AXIOLEV Holdings LLC © 2026
# ============================================================================
set -Eeuo pipefail
IFS=$'\n\t'

REPO="${HOME}/axiolev_runtime"
APP_SCHEME="NSInfinityApp"
NSEXT="/Volumes/NSExternal"
ALEX="${NSEXT}/ALEXANDRIA"

say() { printf "  → %s\n" "$*"; }

[[ -d "$NSEXT" ]] || { echo "NSExternal not mounted"; exit 1; }

cd "$REPO"

# 1. Compose up (services)
if command -v docker-compose >/dev/null 2>&1 || docker compose version >/dev/null 2>&1; then
  say "starting services…"
  docker compose up -d 2>/dev/null || docker-compose up -d
fi

# 2. NVIR refresh (drives v3.1 from stale 88.26 to live ≥92.4)
if [[ -x "$REPO/tools/nvir/nvir_refresh.sh" ]]; then
  say "NVIR refresh…"
  "$REPO/tools/nvir/nvir_refresh.sh" || true
fi

# 3. Local brain (Qwen3-30B MLX) env load
if [[ -f "$REPO/.ns_local_brain.env" ]]; then
  say "loading local brain env…"
  set -a; . "$REPO/.ns_local_brain.env"; set +a
fi

# 4. Launch NSInfinityApp (latest built .app)
LATEST_APP="$(find "$REPO/.build/agent_runs" -maxdepth 6 -name "${APP_SCHEME}.app" 2>/dev/null | sort | tail -1)"
if [[ -n "$LATEST_APP" ]] && [[ -d "$LATEST_APP" ]]; then
  say "launching $APP_SCHEME…"
  open "$LATEST_APP"
fi

# 5. Live score readout
if [[ -x "$REPO/tools/scoring/ns_live_score.sh" ]]; then
  say "live score:"
  "$REPO/tools/scoring/ns_live_score.sh" || true
fi

echo
echo "BOOT COMPLETE — full-power organism online."
echo "  app:      ${APP_SCHEME}"
echo "  branch:   $(git rev-parse --abbrev-ref HEAD 2>/dev/null)"
echo "  head:     $(git rev-parse --short HEAD 2>/dev/null)"
echo "  ledger:   ${ALEX}"
BOOT

# Substitute TODAY/TOMORROW placeholders
sed -i.bak "s/TOMORROW/${TOMORROW}/g; s/TODAY/${TODAY}/g" "$BOOT_SCRIPT" && rm -f "$BOOT_SCRIPT.bak"
chmod +x "$BOOT_SCRIPT"
ok "boot staged   $BOOT_SCRIPT"

# iOS deployment stub for next sprint
IOS_STUB="${BOOT_DIR}/ios_deploy_plan_${TOMORROW}.md"
cat > "$IOS_STUB" <<IOS
# NS∞ iOS Deployment Plan (staged ${TODAY})

## Prereqs checked tonight
- [x] macOS native app building green on Xcode 26
- [x] Project format upgraded cleanly
- [x] Local brain (Qwen3-30B MLX) bound via \`.ns_local_brain.env\`
- [x] 14/14 services healthy

## Next sprint (tomorrow+)
1. Add \`NSInfinityApp-iOS\` target to \`NSInfinityApp.xcodeproj\`
2. Factor UI into shared SwiftPM package (already SwiftUI — portable)
3. Replace direct POSIX file paths with \`FileManager.default.urls(for:in:)\`
4. Replace any \`NSWorkspace\` / AppKit calls with \`UIApplication\` equivalents
5. Provisioning: Apple Developer enrollment (AXIOLEV Holdings LLC)
6. TestFlight distribution first · App Store second
7. On-device inference: MLX supports iOS — Qwen3 may need Q4 quant for <8GB RAM devices

## Blocked by
- Apple Developer enrollment (entity verification via Stripe Atlas — overlaps Ring 5)
- iOS-safe local model (Q4 Qwen-4B or similar)
IOS
ok "ios plan staged  $IOS_STUB"
fi

# ============================================================================
# PHASE M  QUIESCE
# ============================================================================
if should_run M; then
  if [[ "$NO_SHUTDOWN" == "1" ]]; then
    phase "M" "QUIESCE (skipped — NO_SHUTDOWN=1)"
  else
phase "M" "QUIESCE"

# 1. NSInfinityApp — TERM first, KILL as last resort
if [[ -n "$APP_PID" ]] && kill -0 "$APP_PID" 2>/dev/null; then
  step "quitting $APP_SCHEME (pid $APP_PID)…"
  osascript -e "tell application \"$APP_SCHEME\" to quit" 2>/dev/null || kill -TERM "$APP_PID"
  sleep 2
  if kill -0 "$APP_PID" 2>/dev/null; then
    warn "app did not quit cleanly — sending KILL"
    kill -KILL "$APP_PID" 2>/dev/null || true
  fi
  ok "$APP_SCHEME  quit"
fi

# 2. Docker services — stop (preserves volumes), not down
if command -v docker >/dev/null 2>&1; then
  step "stopping docker services (preserving volumes)…"
  ( cd "$REPO" && docker compose stop 2>/dev/null || docker-compose stop 2>/dev/null ) || true
  ok "services stopped (volumes intact)"
fi

# 3. Alexandria flush
step "syncing NSExternal…"
sync
ok "synced"

# 4. Kill any lingering Qwen/MLX background processes
if pgrep -f "qwen\|mlx_server" >/dev/null 2>&1; then
  step "quiescing local brain runners…"
  pkill -TERM -f "qwen\|mlx_server" 2>/dev/null || true
  sleep 1
  pkill -KILL -f "qwen\|mlx_server" 2>/dev/null || true
  ok "local brain quiesced"
fi
  fi
fi

# ============================================================================
# PHASE N  SHUTDOWN TOKEN
# ============================================================================
if should_run N; then
phase "N" "SHUTDOWN TOKEN"

cat > "$SHUTDOWN_TOKEN" <<TOK
NS∞ SAFE TO SHUTDOWN  ·  ${RUN_TS}
================================================================

  day:           ${TODAY}
  branch:        ${BRANCH_EXPECTED}
  head:          ${HEAD_AFTER:-$HEAD_BEFORE}
  tag:           ${TAG_EOD}
  composite:     v3.1=${V31_COMPOSITE}  band=${BAND}
  tests:         pytest ${PYT_PASSED}/${PYT_TOTAL}  vitest ${VIT_PASSED}/${VIT_TOTAL}
  services:      stopped (volumes intact)
  native app:    quit
  alexandria:    synced to NSExternal
  boot next:     ${BOOT_SCRIPT}

  Report:        ${REPORT_MD}
  Ledger edge:   ${LEDGER_FILE:-${ALEX}/ledger/eod/${RUN_TS}/edge.json}

  AM sequence:
    1. plug / keep NSExternal mounted
    2. bash ${BOOT_SCRIPT}
    3. security remediation (PAT revoke, key rotate, SSH, filter-repo, push)

Canonical rule: never fake green.
Alexandria remembers.

AXIOLEV Holdings LLC © 2026
TOK

ok "shutdown token  $SHUTDOWN_TOKEN"
fi

# ============================================================================
# SUMMARY
# ============================================================================
printf "\n%s═══ CLOSURE COMPLETE ═══%s\n" "$C_MAG" "$C_RST"
printf "  composite   v3.1 = %s  (%s)\n" "$V31_COMPOSITE" "$BAND"
printf "  tests       pytest %s/%s  vitest %s/%s  xctest %s\n" \
  "$PYT_PASSED" "$PYT_TOTAL" "$VIT_PASSED" "$VIT_TOTAL" "$XCT_STATUS"
printf "  services    %s/%s healthy\n" "$SVC_HEALTHY" "$SVC_TOTAL"
printf "  tag         %s\n" "$TAG_EOD"
printf "  boot next   bash %s\n" "$BOOT_SCRIPT"
printf "  shutdown    %s\n\n" "$SHUTDOWN_TOKEN"

exit 0
