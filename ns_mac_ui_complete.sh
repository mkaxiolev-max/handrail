#!/usr/bin/env bash
# =============================================================================
# NS∞ Founder Habitat — FULL UI SPEC COMPLETION runner
# =============================================================================
# Drives Claude Code in --print mode to:
#   1. build NSInfinityApp until green (up to NS_MAX_BUILD attempts)
#   2. launch the .app
#   3. audit the SwiftUI source against the canonical Living Architecture spec
#   4. patch gaps surgically (up to NS_MAX_UI iterations)
#   5. rebuild, relaunch, re-audit
#   6. stop when the spec is satisfied — or exit non-zero with open gap list
#
# Canonical rule: NEVER FAKE GREEN.
#   - Exit code reflects reality.
#   - Every attempt ledgered to .build/ui_runs/<ts>/.
#   - If budget runs out, exits non-zero with open gap diagnosis.
#
# Prereqs:
#   1. Xcode 26.4.1 installed, macOS 26 SDK present.
#   2. claude CLI installed and authenticated (curl -fsSL https://claude.ai/install.sh | bash; claude login).
#   3. Run from repo root: ~/axiolev_runtime.
#   4. Grant Screen Recording permission to Terminal on first run (for screencapture).
#
# Usage:
#   bash ~/axiolev_runtime/ns_mac_ui_complete.sh
#   NS_MAX_BUILD=4 NS_MAX_UI=4 bash ~/axiolev_runtime/ns_mac_ui_complete.sh
# =============================================================================

set -u  # fail on unset vars; we explicitly handle command failures below.

# ---------- config ----------
REPO="${HOME}/axiolev_runtime"
APP_DIR="${REPO}/apps/ns_mac/NSInfinityApp"
PROJ="${APP_DIR}/NSInfinityApp.xcodeproj"
SCHEME="NSInfinityApp"
CONFIG="Debug"
MAX_BUILD_ATTEMPTS="${NS_MAX_BUILD:-6}"
MAX_UI_ATTEMPTS="${NS_MAX_UI:-6}"
TS="$(date +%Y%m%d_%H%M%S)"
RUN_DIR="${REPO}/.build/ui_runs/${TS}"
DERIVED="${RUN_DIR}/derived"
SPEC_FILE="${RUN_DIR}/LIVING_ARCHITECTURE_SPEC.md"
AUDIT_JSON="${RUN_DIR}/ui_audit_current.json"
MASTER_LOG="${RUN_DIR}/run.log"

mkdir -p "$RUN_DIR" "$DERIVED"

# ---------- pretty printing ----------
BOLD=$'\033[1m'; DIM=$'\033[2m'; RESET=$'\033[0m'
PURPLE=$'\033[35m'; GREEN=$'\033[32m'; RED=$'\033[31m'; YELLOW=$'\033[33m'; CYAN=$'\033[36m'

banner() { printf '\n%s%s== %s ==%s\n' "$BOLD" "$PURPLE" "$*" "$RESET" | tee -a "$MASTER_LOG" >&2; }
step()   { printf '%s[%s]%s %s\n' "$CYAN" "$(date +%H:%M:%S)" "$RESET" "$*" | tee -a "$MASTER_LOG" >&2; }
ok()     { printf '%s[ok]%s %s\n' "$GREEN" "$RESET" "$*" | tee -a "$MASTER_LOG" >&2; }
warn()   { printf '%s[warn]%s %s\n' "$YELLOW" "$RESET" "$*" | tee -a "$MASTER_LOG" >&2; }
die()    { printf '%s[FAIL]%s %s\n' "$RED" "$RESET" "$*" | tee -a "$MASTER_LOG" >&2; exit 1; }

# ---------- preflight ----------
banner "Preflight"
cd "$REPO" 2>/dev/null || die "repo not found: $REPO"
[[ -d "$PROJ" ]] || die "xcodeproj missing: $PROJ"

command -v xcodebuild >/dev/null || die "xcodebuild not on PATH (run: sudo xcode-select -s /Applications/Xcode.app)"
command -v claude     >/dev/null || die "Claude CLI missing. Install: curl -fsSL https://claude.ai/install.sh | bash; claude login"
command -v python3    >/dev/null || die "python3 not found (install Xcode Command Line Tools)"

XCODE_VER=$(xcodebuild -version 2>/dev/null | head -1 || echo "unknown")
ok "Xcode:   $XCODE_VER"
ok "Repo:    $REPO"
ok "Project: ${PROJ#${REPO}/}"
ok "Ledger:  $RUN_DIR"
ok "Budget:  build=$MAX_BUILD_ATTEMPTS, ui=$MAX_UI_ATTEMPTS"

# Rollback snapshot.
SNAPSHOT_TAG="ns-mac-ui-snapshot-${TS}"
if git rev-parse --git-dir >/dev/null 2>&1; then
  git tag -f "$SNAPSHOT_TAG" >/dev/null 2>&1 && ok "snapshot: $SNAPSHOT_TAG  (rollback: git reset --hard $SNAPSHOT_TAG)"
fi

# ---------- write canonical Living Architecture spec ----------
banner "Writing canonical Living Architecture spec"

cat > "$SPEC_FILE" <<'SPEC'
# NS∞ Living Architecture — Canonical UI Spec (ground truth)

The running NSInfinityApp must render every element below with exact design tokens.
Anything missing or drifting = GAP. No placeholder labels allowed.

## Design tokens (EXACT hex — no approximations)

| role      | hex      |
|-----------|----------|
| founder   | #FF6B00  |
| violet    | #00D4FF  |
| chambers  | #6B00FF  |
| adj       | #00FF88  |
| handrail  | #00FFFF  |
| alex      | #FFFF00  |
| kernel    | #FF3333  |
| build     | #4A6FA5  |
| bg        | #0A0E27  |

## Required scene: 3-pane + HUD + overlay + timeline

### 1. Top HUD (fixed strip, top)
- "NS∞" wordmark (left)
- "Docker 11/11" status pill
- "Invariants 8/10" pill
- "Ring 5 0/5" warn-state pill
- "YubiKey 26116460" label
- "Shalom ✓" green badge

### 2. Voice Overlay Pill (top-right, floats above every view)
- Text: "Violet · ready"
- Pulsing dot (voice-membrane animation)
- Color: violet token

### 3. Left Rail (fixed ≈ 200 pt)
- Six modes, in order, tappable, active highlighted:
    1. Living Architecture   (default active)
    2. Engine Room
    3. Programs Runtime
    4. Memory
    5. Governance
    6. Build Space
- Seven live-services status list (green dot when live)
- Founder identity card at bottom (founder token)

### 4. Center Canvas — Organism Map (fills center)
- Violet node at center, glowing (violet token, radial glow)
- Five chambers arrayed around Violet (chambers token):
    Forge, Institute, Board, Omega, Registry
- Adjudication node (adj token) between chambers and handrail
- Handrail band/ring (handrail token)
- Programs node + Alexandria node (alex token for Alexandria)
- Animated autopoietic flow lines between nodes
- Privacy membrane: translucent ring around Violet
- Constitutional boundary: dashed ellipse enclosing chambers + Adj + Handrail
- Dignity Kernel band (kernel token) INSIDE the boundary
- YubiKey band INSIDE the boundary
- Build Space label/area OUTSIDE the boundary (build token)
- Founder node (founder token) feeding into Violet

### 5. Right Panel (fixed ≈ 320 pt)
- Violet identity card (top)
- Live chamber scores:
    Institute 7.6
    Board 5.15
    Forge 4.9
- "10/10 proofs + Shalom" block
- Ring 5 gates: 5 rows, all red
- Alexandria counts block (edges, atoms, receipts)

### 6. Bottom Timeline (fixed ≈ 120 pt)
- Rolling receipts stream (right-to-left scroll)
- Rows color-coded by layer (token colors)
- Row types visible: receipt, adjudication, atom_write, invariant_check

## Hard invariants (non-negotiable)
- Background = bg token (#0A0E27) across all views.
- All six left-rail modes must be reachable; tapping routes the center canvas.
- VoiceOverlayPill renders above every view.
- No "TODO", "Sample", "Lorem ipsum", "Placeholder" strings anywhere visible.
- Dignity Kernel visual INSIDE the constitutional boundary.
- Build Space visual OUTSIDE the boundary.
- Design tokens referenced by name, not hardcoded hex, wherever feasible.
SPEC
ok "spec: $SPEC_FILE"

# =============================================================================
# FUNCTIONS
# =============================================================================

build_once() {
  # $1 = label (e.g. "1", "ui_3")
  local n="$1"
  local log="${RUN_DIR}/build_${n}.log"
  local sum="${RUN_DIR}/build_${n}.summary.txt"

  step "xcodebuild (attempt ${n})"
  set +e
  xcodebuild \
    -project "$PROJ" \
    -scheme "$SCHEME" \
    -configuration "$CONFIG" \
    -destination 'platform=macOS' \
    -derivedDataPath "$DERIVED" \
    -skipMacroValidation \
    CODE_SIGN_IDENTITY="-" \
    CODE_SIGNING_REQUIRED=NO \
    CODE_SIGNING_ALLOWED=NO \
    ONLY_ACTIVE_ARCH=YES \
    build >"$log" 2>&1
  local rc=$?
  set -e

  {
    echo "## BUILD SUMMARY (attempt $n)"
    echo "exit_code: $rc"
    echo
    echo "### errors (first 30)"
    grep -E "error:" "$log" | head -30 || true
    echo
    echo "### warnings (first 20)"
    grep -E "warning:" "$log" | head -20 || true
  } > "$sum"

  return "$rc"
}

run_claude_build_repair() {
  local n="$1"
  local log="${RUN_DIR}/build_${n}.log"
  local sum="${RUN_DIR}/build_${n}.summary.txt"
  local prompt_file="${RUN_DIR}/prompt_build_${n}.txt"
  local claude_log="${RUN_DIR}/claude_build_${n}.log"

  step "Claude repairing build (attempt ${n})"

  cat > "$prompt_file" <<PROMPT
You are inside the NS∞ Founder Habitat repo at $REPO.
The Xcode build FAILED at attempt $n.

Full build log:   $log
Extracted summary: $sum

Task:
1. Read the summary first. Then targeted reads of source files named in errors.
2. Apply the SMALLEST fix that addresses the root cause.
3. Do NOT disable tests, silence warnings to pass, or weaken invariants.
4. Do NOT touch: Dignity Kernel code, YubiKey quorum logic, chamber separation,
   constitutional boundary rendering.
5. Common Xcode 26 failure modes:
   - objectVersion 56 → 77 auto-bump (leave as-is; Xcode owns the format).
   - Macro validation (already bypassed with -skipMacroValidation).
   - Deprecated SwiftUI / AppKit APIs (update to macOS 26 replacements).
   - Swift 6 strict concurrency (add @MainActor / Sendable as needed).
   - Missing imports.

Return ONE line at the end:
  FIX: <one-sentence root-cause fix summary>
  NEEDS_HUMAN: <question>    (if any decision can't be made safely)

Allowed tools: Read, Edit, Write, Grep, Glob. No Bash. No network.
PROMPT

  set +e
  claude --print --dangerously-skip-permissions \
    < "$prompt_file" > "$claude_log" 2>&1
  local rc=$?
  set -e

  echo "${DIM}--- Claude verdict (build) ---${RESET}"
  tail -5 "$claude_log"
  echo "${DIM}------------------------------${RESET}"

  grep -q "^NEEDS_HUMAN:" "$claude_log" && return 2
  return "$rc"
}

locate_and_launch() {
  step "Locating built .app"
  local app_path
  app_path=$(find "$DERIVED/Build/Products/$CONFIG" -maxdepth 2 -name "${SCHEME}.app" -type d 2>/dev/null | head -1)
  [[ -n "$app_path" ]] || { warn "built .app not found under $DERIVED"; return 1; }
  ok "app: $app_path"

  pkill -x "$SCHEME" 2>/dev/null || true
  sleep 0.5
  open -n "$app_path" || { warn "open failed"; return 1; }
  sleep 2

  local pid
  pid=$(pgrep -x "$SCHEME" | head -1)
  [[ -n "$pid" ]] || { warn "launched but no PID visible"; return 1; }
  ok "running pid=$pid"
  echo "$app_path" > "${RUN_DIR}/app_path.txt"
  echo "$pid"      > "${RUN_DIR}/app_pid.txt"
  return 0
}

capture_screenshot() {
  local tag="$1"
  local out="${RUN_DIR}/ui_${tag}.png"
  sleep 2  # let UI settle
  if screencapture -x -o "$out" 2>/dev/null; then
    ok "screenshot: $out"
  else
    warn "screencapture failed (grant Screen Recording to Terminal in System Settings)"
  fi
}

run_claude_ui_audit() {
  local n="$1"
  local prompt_file="${RUN_DIR}/prompt_audit_${n}.txt"
  local claude_log="${RUN_DIR}/claude_audit_${n}.log"

  step "Claude auditing UI source vs spec (iteration ${n})"

  # Wipe stale audit so we detect missing write.
  rm -f "$AUDIT_JSON"

  cat > "$prompt_file" <<PROMPT
You are inside $REPO. NSInfinityApp has built and is running.

Canonical UI spec (ground truth): $SPEC_FILE
Source tree to audit:             $APP_DIR/NSInfinityApp/

Task: audit every SwiftUI/AppKit view file against the spec. Identify
EVERY missing, wrong, or drifting element. Write a strict JSON report.

Steps:
1. Read the spec file completely.
2. Read every .swift file under $APP_DIR/NSInfinityApp/ (views, view models,
   design tokens, app entry points, scene roots). Use Grep/Glob to find them.
3. Map each spec requirement to existing Swift code. If not found or not
   conformant, record it as a gap.
4. Flag any hardcoded hex that should reference a named design token.

Write VALID JSON to this EXACT path:
  $AUDIT_JSON

Schema:
{
  "verdict": "MATCHES_SPEC" | "GAPS_EXIST",
  "on_spec_elements": ["..."],
  "gaps": [
    {
      "spec_element": "<exact name from spec>",
      "severity": "blocker" | "high" | "medium" | "low",
      "file_hint": "<existing file path to edit, or NEW:<path>>",
      "fix_plan": "<one-sentence smallest patch>"
    }
  ],
  "design_token_violations": [
    {"file": "<path>", "line_hint": "<grep pattern>", "issue": "hardcoded #XXXXXX should be <token>"}
  ],
  "needs_human": false,
  "notes": "<one paragraph>"
}

Do NOT edit source files in this pass. Audit only. Be strict.
If the app truly satisfies every element, verdict = MATCHES_SPEC and gaps = [].

Allowed tools: Read, Write, Grep, Glob. No Bash. No network.
PROMPT

  set +e
  claude --print \
    --allowedTools "Read,Write,Grep,Glob" \
    < "$prompt_file" > "$claude_log" 2>&1
  local rc=$?
  set -e

  if [[ ! -f "$AUDIT_JSON" ]]; then
    warn "audit JSON not written. Claude log:"
    tail -20 "$claude_log"
    return 1
  fi

  echo "${DIM}--- UI audit verdict ---${RESET}"
  python3 - "$AUDIT_JSON" <<'PY' 2>/dev/null || cat "$AUDIT_JSON"
import json, sys
d = json.load(open(sys.argv[1]))
print("verdict:", d.get("verdict"))
print("gaps:   ", len(d.get("gaps", [])))
for g in d.get("gaps", []):
    print("  -", g.get("severity"), "·", g.get("spec_element"), "→", g.get("fix_plan"))
tv = d.get("design_token_violations", [])
if tv:
    print("token violations:", len(tv))
    for v in tv[:10]:
        print("  -", v.get("file"), "·", v.get("issue"))
PY
  echo "${DIM}------------------------${RESET}"
  return 0
}

run_claude_ui_patch() {
  local n="$1"
  local prompt_file="${RUN_DIR}/prompt_patch_${n}.txt"
  local claude_log="${RUN_DIR}/claude_patch_${n}.log"

  step "Claude patching UI to close gaps (iteration ${n})"

  cat > "$prompt_file" <<PROMPT
You are inside $REPO. Previous audit wrote $AUDIT_JSON.

Task: read the audit JSON. For each item in "gaps" and each entry in
"design_token_violations", apply the smallest SwiftUI/AppKit edit that
closes it, following the canonical spec at $SPEC_FILE.

Rules:
- Edits must be minimal and surgical. One concern per edit.
- Respect design tokens EXACTLY (hex from spec). Reference named tokens where possible.
- Do NOT introduce placeholder text ("TODO", "Sample", "Lorem ipsum", "Placeholder").
- Do NOT disable existing functionality.
- Do NOT edit NSInfinityApp.xcodeproj/project.pbxproj (Xcode owns that).
- If a gap requires adding a NEW Swift file:
    - Create it under $APP_DIR/NSInfinityApp/<AppropriateSubdir>/
    - If the file must be added to the Xcode target to compile (most cases),
      emit NEEDS_HUMAN instead of editing project.pbxproj.
- If any gap requires judgement you can't make safely, emit NEEDS_HUMAN.
- Do NOT touch: Dignity Kernel logic, YubiKey quorum, chamber separation invariants.

Return ONE line at the end:
  FIX: <N files edited; M gaps closed>
  NEEDS_HUMAN: <which gap needs human judgement and why>

Allowed tools: Read, Edit, Write, Grep, Glob. No Bash. No network.
PROMPT

  set +e
  claude --print --dangerously-skip-permissions \
    < "$prompt_file" > "$claude_log" 2>&1
  local rc=$?
  set -e

  echo "${DIM}--- Claude verdict (patch) ---${RESET}"
  tail -5 "$claude_log"
  echo "${DIM}------------------------------${RESET}"

  grep -q "^NEEDS_HUMAN:" "$claude_log" && return 2
  return "$rc"
}

get_verdict() {
  python3 -c "import json; print(json.load(open('$AUDIT_JSON')).get('verdict',''))" 2>/dev/null || echo ""
}

get_gaps_count() {
  python3 -c "import json; print(len(json.load(open('$AUDIT_JSON')).get('gaps',[])))" 2>/dev/null || echo "0"
}

# =============================================================================
# PHASE 1 — BUILD TO GREEN
# =============================================================================
banner "Phase 1 — build to green"

attempt=1
last_rc=1
while (( attempt <= MAX_BUILD_ATTEMPTS )); do
  set +e; build_once "$attempt"; last_rc=$?; set -e

  if [[ "$last_rc" == "0" ]]; then
    ok "build green on attempt $attempt"
    break
  fi

  warn "build red on attempt $attempt (rc=$last_rc)"
  echo "${DIM}--- errors handed to Claude ---${RESET}"
  grep -E "error:" "${RUN_DIR}/build_${attempt}.log" | head -10 || true
  echo "${DIM}-------------------------------${RESET}"

  if (( attempt == MAX_BUILD_ATTEMPTS )); then break; fi

  set +e; run_claude_build_repair "$attempt"; c_rc=$?; set -e
  [[ $c_rc -eq 2 ]] && die "Claude flagged build decision needing human judgement. See ${RUN_DIR}/claude_build_${attempt}.log"
  [[ $c_rc -ne 0 ]] && die "Claude build repair crashed on attempt $attempt. Ledger: $RUN_DIR"

  attempt=$(( attempt + 1 ))
done

if [[ "$last_rc" != "0" ]]; then
  echo
  echo "${RED}${BOLD}BUILD DID NOT GREEN within $MAX_BUILD_ATTEMPTS attempts.${RESET}"
  echo "Last errors:"
  grep -E "error:" "${RUN_DIR}/build_${attempt}.log" | head -15 || true
  echo
  echo "Rollback: git reset --hard $SNAPSHOT_TAG"
  echo "Ledger:   $RUN_DIR"
  die "Canonical rule: never fake green."
fi

# =============================================================================
# PHASE 2 — LAUNCH
# =============================================================================
banner "Phase 2 — launch"
locate_and_launch || die "launch failed despite green build. See derived: $DERIVED"
capture_screenshot "baseline"

# =============================================================================
# PHASE 3 — UI SPEC COMPLETION LOOP
# =============================================================================
banner "Phase 3 — UI spec completion loop"

ui_attempt=1
spec_matches=0
while (( ui_attempt <= MAX_UI_ATTEMPTS )); do
  step "UI iteration $ui_attempt / $MAX_UI_ATTEMPTS"

  set +e; run_claude_ui_audit "$ui_attempt"; audit_rc=$?; set -e
  [[ $audit_rc -ne 0 ]] && die "UI audit crashed. See ${RUN_DIR}/claude_audit_${ui_attempt}.log"

  verdict=$(get_verdict)
  gaps_count=$(get_gaps_count)

  if [[ "$verdict" == "MATCHES_SPEC" ]]; then
    ok "UI matches spec on iteration $ui_attempt"
    spec_matches=1
    break
  fi

  warn "UI has $gaps_count gap(s). Patching."

  set +e; run_claude_ui_patch "$ui_attempt"; patch_rc=$?; set -e
  [[ $patch_rc -eq 2 ]] && die "Claude flagged UI decision needing human judgement. See ${RUN_DIR}/claude_patch_${ui_attempt}.log"
  [[ $patch_rc -ne 0 ]] && die "Claude UI patch crashed on iteration $ui_attempt. Rollback: git reset --hard $SNAPSHOT_TAG"

  step "Rebuilding after patch"
  set +e; build_once "ui_${ui_attempt}"; rc2=$?; set -e
  if [[ "$rc2" != "0" ]]; then
    warn "patch broke the build. Attempting repair."
    set +e; run_claude_build_repair "ui_${ui_attempt}_repair"; set -e
    set +e; build_once "ui_${ui_attempt}_retry"; rc3=$?; set -e
    [[ "$rc3" != "0" ]] && die "UI patch broke the build and repair failed. Rollback: git reset --hard $SNAPSHOT_TAG"
  fi

  locate_and_launch || die "relaunch failed after UI patch. Rollback: git reset --hard $SNAPSHOT_TAG"
  capture_screenshot "ui_${ui_attempt}"

  ui_attempt=$(( ui_attempt + 1 ))
done

# =============================================================================
# VERDICT
# =============================================================================
banner "Verdict"

if (( ! spec_matches )); then
  echo
  echo "${RED}${BOLD}UI SPEC NOT FULLY SATISFIED within $MAX_UI_ATTEMPTS iterations.${RESET}"
  echo "Last audit: $AUDIT_JSON"
  echo "Open gaps:"
  python3 - "$AUDIT_JSON" <<'PY' 2>/dev/null || cat "$AUDIT_JSON"
import json, sys
d = json.load(open(sys.argv[1]))
for g in d.get("gaps", []):
    print(f"  - [{g.get('severity')}] {g.get('spec_element')} → {g.get('fix_plan')} (file_hint: {g.get('file_hint')})")
PY
  echo
  echo "App is running but incomplete. PID: $(pgrep -x $SCHEME 2>/dev/null || echo unknown)"
  echo "Ledger:   $RUN_DIR"
  echo "Rollback: git reset --hard $SNAPSHOT_TAG"
  echo
  echo "This is not a failure of the agent. It is honest reporting."
  echo "Canonical rule: never fake green."
  exit 3
fi

# =============================================================================
# FULL GREEN
# =============================================================================
banner "NS∞ Founder Habitat — FULL UI SPEC COMPLETE"

capture_screenshot "final"

echo
echo "${GREEN}${BOLD}Living Architecture is rendering on screen.${RESET}"
echo "App PID:      $(pgrep -x $SCHEME 2>/dev/null || echo unknown)"
echo "Final shot:   $RUN_DIR/ui_final.png"
echo "Audit JSON:   $AUDIT_JSON"
echo "Stream logs:  log stream --predicate 'process == \"$SCHEME\"' --level info"
echo "Stop app:     pkill -x $SCHEME"
echo "Ledger:       $RUN_DIR"
echo "Snapshot:     $SNAPSHOT_TAG"
echo
echo "Commit groups to land (review with git diff first):"
echo "  1. chore(ns_mac): xcode 26 project format upgrade   (pbxproj only, if changed)"
echo "  2. ui(ns_mac): Living Architecture spec completion  ($(date -u +%Y%m%d))"
echo

exit 0
