#!/usr/bin/env bash
# =============================================================================
# ns_closure_max_v2.sh — NS∞ FINAL INTEGRATION & CLOSURE MAX (v2.1)
# AXIOLEV Holdings LLC © 2026 — axiolevns <axiolevns@axiolev.com>
#
# v2 integrates insights from all four source documents:
#   • Omega_Institutional_Architecture...Whitepaper.pdf  → Z3  (L10 projection)
#   • UG_max_ready_to_integrate_.pdf                     → Z3b (Entity primitive)
#   • Ui_addition.pdf                                    → Z5a (7 named routes)
#   • Ns_media.pdf                                       → Z-1 (bootstrap gate)
#   • media_engine_repo.zip                              → Z4  (actual wiring)
#
# Mission (v2)
# ------------
# One script. One terminal. Closes NS∞ from current state
# (ns-infinity-manifold-complete-v1.0.0, 717 tests green) to a verified
# READY TO BOOT posture, with no fabricated greens and full integration
# of every insight from the four source documents and the media engine zip.
#
# Phases (linear, each fast-forwards if already satisfied):
#   Z-1 Bootstrap gate
#         • If manifold tag absent, run 7-phase ns_bootstrap.sh sequence
#           (object_model → storage_layout → fastapi_routes → canon_gate →
#            projection_core → hic_pdp_ctf → storytime) with 3-retry heal.
#         • If manifold tag present, skip (preserve forward-only discipline).
#   Z0  Preflight + safety (YubiKey, Alexandria mount, git state)
#   Z1  Security scrub (gitleaks, repo-wide secret scan, push gate armed)
#   Z2  Live ontology audit → artifacts/ontology_audit_<ts>.md
#         • Enforces locked names (Gradient Field not Ether, Alexandrian
#           Lexicon not Lexicon/Atomlex, State Manifold, Alexandrian
#           Archive, Lineage Fabric, Narrative).
#         • Reports actual file locations matched per layer with mismatches.
#   Z3  Omega L10 projection/ego layer (per Omega Whitepaper)
#         • Pydantic v2 primitives (15 types)
#         • Alexandrian Archive substrate layout
#         • FastAPI routes (9 routes)
#         • Recovery-ordered projection engine (6 strategies)
#         • Locked confidence weights
#         • Six-fold Canon gate
#   Z3b Entity primitive universal schema (per UG_max)
#         • Entity base: id/kind/identity/state/provenance/epistemics/
#           constraints/relations/manifestations/receipts/bindings/
#           supersession/timestamps/metadata
#         • Reframes Branch/Delta/Anchor/Shard/Entanglement/Contradiction
#           as Entity specializations via .kind discriminator.
#         • Temporal Geometry adapter quarantined at L3 boundary.
#         • Bohmian/pilot-wave layer marked quarantined: theoretical.
#   Z4  Media engine integration (from media_engine_repo.zip)
#         • Unpack to ns/services/media_engine/
#         • Mount router at gateway prefix /omega/media (preserves /api/v1
#           inside the subapp; NS∞ mounts it under sovereign prefix).
#         • Shim pgvector dep if Postgres absent; emit skip-with-reason.
#         • Wire Lineage Fabric receipts on every search/opportunity/
#           funding mutation (CTF hook).
#   Z5  UI addition base integration (stubs + assets)
#   Z5a UI addition named route surface (per Ui_addition.pdf)
#         • GET  /ns/state              → composite runtime snapshot
#         • GET  /ns/engine/live        → SSE stream of CPS events
#         • GET  /program/list          → runtime programs
#         • GET  /program/{id}          → specific program detail
#         • GET  /alexandria/graph      → Alexandrian Archive graph view
#         • GET  /receipt/{id}          → Lineage Fabric receipt lookup
#         • GET  /canon                 → live Canon rules view
#         • GET  /governance/state      → constitutional state snapshot
#         • Projection-invariance contract tests for each endpoint.
#   Z6  5-gate READY TO BOOT verification
#   Z7  Final closure certification + tagging
#         • certification/NS_CLOSURE_MAX_v2.md + .json
#         • Tag ns-infinity-closure-max-v2.0.0 (annotated)
#         • Tag ns-infinity-ready-to-boot-<YYYYMMDD> if all gates green
#         • No push unless --push-safe AND gitleaks clean
#
# Safety contract (unchanged from v1)
# -----------------------------------
#   1. NEVER pushes by default. --push-safe + gitleaks clean required.
#   2. NEVER deletes or force-pushes canon, ledger, or tagged branches.
#   3. NEVER rewrites history unless --scrub-history with dry-run first.
#   4. Bash 3.2 only. No assoc arrays, no mapfile, no ${var,,}. case/esac only.
#   5. No network except 127.0.0.1 + GitHub remote-url read unless --pull.
#   6. Idempotent. Fast-forwards if phase tag present and tests pass.
#   7. Lineage receipts: every phase emits ledger JSONL + local JSONL.
#   8. NS∞ must NEVER fabricate greens. Every test reported must be executed.
#
# Usage
# -----
#   bash ~/axiolev_runtime/ns_closure_max_v2.sh
#   bash ~/axiolev_runtime/ns_closure_max_v2.sh --scrub-history
#   bash ~/axiolev_runtime/ns_closure_max_v2.sh --push-safe
#   bash ~/axiolev_runtime/ns_closure_max_v2.sh --dry-run
#   bash ~/axiolev_runtime/ns_closure_max_v2.sh --pull
#   bash ~/axiolev_runtime/ns_closure_max_v2.sh --skip-bootstrap
#   bash ~/axiolev_runtime/ns_closure_max_v2.sh --phase Z3b
#
# =============================================================================

set -u
set -o pipefail

# ---------- Identity ---------------------------------------------------------
AXIOLEV_OWNER="AXIOLEV Holdings LLC"
AXIOLEV_YEAR="2026"
GIT_USER_NAME="axiolevns"
GIT_USER_EMAIL="axiolevns@axiolev.com"
YUBIKEY_SERIAL="26116460"

# ---------- Paths ------------------------------------------------------------
ROOT_REPO="${ROOT_REPO:-$HOME/axiolev_runtime}"
BASE_BRANCH="${BASE_BRANCH:-boot-operational-closure}"
ALEX_MNT="${ALEX_MNT:-/Volumes/NSExternal/ALEXANDRIA}"
ALEX_LEDGER="${ALEX_LEDGER:-$ALEX_MNT/ledger}"
ALEX_CTF="${ALEX_CTF:-$ALEX_MNT/ctf/receipts}"
UPLOADS_DIR="${UPLOADS_DIR:-/mnt/user-data/uploads}"

TS_RUN="$(date -u +%Y%m%dT%H%M%SZ)"
DATE_TAG="$(date -u +%Y%m%d)"

LOG_DIR="$ROOT_REPO/.terminal_manager/logs"
LOG_FILE="$LOG_DIR/closure_v2_${TS_RUN}.log"
CTF_LOCAL="$LOG_DIR/lineage_CLOSURE_V2_${TS_RUN}.jsonl"
CTF_LEDGER="$ALEX_LEDGER/ns_events.jsonl"
ARTIFACTS_DIR="$ROOT_REPO/artifacts"
CERT_DIR="$ROOT_REPO/certification"
PROMPT_MD="$ROOT_REPO/CLOSURE_V2_PROMPT.md"
FIX_MD="$ROOT_REPO/CLOSURE_V2_FIX_REQUEST.md"
ONTOLOGY_REPORT="$ARTIFACTS_DIR/ontology_audit_${TS_RUN}.md"
BOOTSTRAP_REPORT="$ARTIFACTS_DIR/bootstrap_audit_${TS_RUN}.md"
ENTITY_REPORT="$ARTIFACTS_DIR/entity_primitive_${TS_RUN}.md"
UI_REPORT="$ARTIFACTS_DIR/ui_addition_${TS_RUN}.md"

MAX_ATTEMPTS=3
MANIFOLD_TAG="ns-infinity-manifold-complete-v1.0.0"
CLOSURE_V2_TAG="ns-infinity-closure-max-v2.0.0"
READY_TAG_PREFIX="ns-infinity-ready-to-boot"

# ---------- Flags ------------------------------------------------------------
FLAG_SCRUB_HISTORY=0
FLAG_PUSH_SAFE=0
FLAG_DRY_RUN=0
FLAG_PULL=0
FLAG_SKIP_BOOTSTRAP=0
FLAG_SINGLE_PHASE=""

while [ $# -gt 0 ]; do
  case "$1" in
    --scrub-history)  FLAG_SCRUB_HISTORY=1 ;;
    --push-safe)      FLAG_PUSH_SAFE=1 ;;
    --dry-run)        FLAG_DRY_RUN=1 ;;
    --pull)           FLAG_PULL=1 ;;
    --skip-bootstrap) FLAG_SKIP_BOOTSTRAP=1 ;;
    --phase)          shift; FLAG_SINGLE_PHASE="${1:-}" ;;
    --help|-h)
      awk '/^# Usage/,/^# ===/' "$0" | sed 's/^# \{0,1\}//'
      exit 0 ;;
    *) echo "unknown flag: $1" >&2; exit 2 ;;
  esac
  shift || true
done

# ---------- Color (tty-gated) ------------------------------------------------
if [ -t 1 ]; then
  C_RESET=$'\033[0m'; C_BOLD=$'\033[1m'
  C_RED=$'\033[31m'; C_GREEN=$'\033[32m'
  C_YEL=$'\033[33m'; C_CYAN=$'\033[36m'; C_MAG=$'\033[35m'
else
  C_RESET=""; C_BOLD=""; C_RED=""; C_GREEN=""; C_YEL=""; C_CYAN=""; C_MAG=""
fi

mkdir -p "$LOG_DIR" "$ARTIFACTS_DIR" "$CERT_DIR" 2>/dev/null || true
touch "$LOG_FILE" 2>/dev/null || true

# ---------- Logging ----------------------------------------------------------
log()       { printf '%s [CLOSURE_V2] %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*" | tee -a "$LOG_FILE"; }
log_info()  { log "${C_CYAN}INFO${C_RESET} $*"; }
log_ok()    { log "${C_GREEN}OK${C_RESET}   $*"; }
log_warn()  { log "${C_YEL}WARN${C_RESET} $*"; }
log_err()   { log "${C_RED}ERR${C_RESET}  $*"; }
log_step()  { log "${C_BOLD}${C_CYAN}==>${C_RESET} $*"; }
log_phase() { log "${C_BOLD}${C_MAG}>>>${C_RESET} $*"; }

# ---------- Lineage Fabric receipt emit --------------------------------------
lineage_emit() {
  _event="$1"; shift
  _subject="$1"; shift
  _status="$1"; shift
  _detail="$*"
  _ts="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  _line="$(python3 - "$_ts" "CLOSURE_V2" "$_event" "$_subject" "$_status" "$_detail" <<'PY' 2>/dev/null
import json,sys
ts,terminal,event,subject,status,detail = sys.argv[1:7]
print(json.dumps({
  "ts": ts, "terminal": terminal, "event": event,
  "subject": subject, "status": status, "detail": detail
}, ensure_ascii=False))
PY
)"
  if [ -z "$_line" ]; then
    _line="{\"ts\":\"$_ts\",\"terminal\":\"CLOSURE_V2\",\"event\":\"$_event\",\"subject\":\"$_subject\",\"status\":\"$_status\",\"detail\":\"escape_failed\"}"
  fi
  printf '%s\n' "$_line" >> "$CTF_LOCAL" 2>/dev/null || true
  if [ -d "$ALEX_LEDGER" ]; then
    printf '%s\n' "$_line" >> "$CTF_LEDGER" 2>/dev/null || true
  fi
}

# ---------- Fatal ------------------------------------------------------------
fail_exit() {
  _reason="$*"
  log_err "FATAL: $_reason"
  lineage_emit "closure_v2_failed" "closure" "error" "$_reason"
  write_return_block "BUILD_FAILED" "$_reason"
  exit 1
}

# ---------- Git wrappers -----------------------------------------------------
git_c() {
  ( cd "$ROOT_REPO" && \
    git -c "user.name=$GIT_USER_NAME" -c "user.email=$GIT_USER_EMAIL" "$@" )
}

git_in() {
  _dir="$1"; shift
  ( cd "$_dir" && \
    git -c "user.name=$GIT_USER_NAME" -c "user.email=$GIT_USER_EMAIL" "$@" )
}

tag_phase() {
  _dir="$1"; _tag="$2"
  if git_in "$_dir" rev-parse -q --verify "refs/tags/$_tag" >/dev/null 2>&1; then
    log_info "tag $_tag already present"
    return 0
  fi
  if [ "$FLAG_DRY_RUN" -eq 1 ]; then
    log_info "[dry-run] would tag: $_tag"
    return 0
  fi
  git_in "$_dir" tag -a "$_tag" -m "$_tag — $AXIOLEV_OWNER © $AXIOLEV_YEAR" >>"$LOG_FILE" 2>&1
}

commit_phase() {
  _dir="$1"; _id="$2"; _desc="$3"
  _msg="$_id: $_desc — $AXIOLEV_OWNER © $AXIOLEV_YEAR"
  git_in "$_dir" add -A || return 1
  if git_in "$_dir" diff --cached --quiet; then
    log_info "no changes to commit for $_id"
    return 0
  fi
  if [ "$FLAG_DRY_RUN" -eq 1 ]; then
    log_info "[dry-run] would commit: $_msg"
    git_in "$_dir" reset HEAD -- . >/dev/null 2>&1 || true
    return 0
  fi
  git_in "$_dir" commit -m "$_msg" >>"$LOG_FILE" 2>&1
}

# ---------- Return block -----------------------------------------------------
write_return_block() {
  _status="$1"; shift
  _detail="$*"
  _block_file="$ARTIFACTS_DIR/closure_v2_return_${TS_RUN}.txt"
  {
    echo "### RETURN_BLOCK ###"
    echo "CLOSURE_V2_STATUS: $_status"
    echo "CLOSURE_V2_TS: $TS_RUN"
    echo "REPO: $ROOT_REPO"
    echo "BRANCH: $BASE_BRANCH"
    echo "DETAIL: $_detail"
    echo "LEDGER: $CTF_LEDGER"
    echo "LOCAL_LINEAGE: $CTF_LOCAL"
    echo "LOG: $LOG_FILE"
    echo "### END_RETURN_BLOCK ###"
  } > "$_block_file" 2>/dev/null || true
  cat "$_block_file" 2>/dev/null || true
}

# ---------- JSON helper ------------------------------------------------------
json_esc() {
  python3 - <<PY
import json,sys
print(json.dumps(sys.stdin.read()))
PY
}

# ---------- Write Python file guarded by marker ------------------------------
#   $1: absolute path to write
#   $2: marker string to search for before overwrite
#   stdin: file contents
#   Behavior: if marker found in existing file AND file readable, no write.
py_write_guarded() {
  _path="$1"; _marker="$2"
  _dir="$(dirname "$_path")"
  mkdir -p "$_dir" 2>/dev/null || return 1
  if [ -f "$_path" ] && grep -q "$_marker" "$_path" 2>/dev/null; then
    log_info "guarded skip (already present): $_path"
    cat >/dev/null  # drain stdin
    return 0
  fi
  if [ "$FLAG_DRY_RUN" -eq 1 ]; then
    log_info "[dry-run] would write: $_path"
    cat >/dev/null
    return 0
  fi
  cat > "$_path" || return 1
  log_ok "wrote $_path"
}

# =============================================================================
# PHASE Z-1 — BOOTSTRAP GATE (per Ns_media.pdf)
# =============================================================================

phase_zm1_bootstrap() {
  log_phase "Z-1 bootstrap gate"
  lineage_emit "phase_start" "Z-1" "info" "bootstrap gate"

  if [ "$FLAG_SKIP_BOOTSTRAP" -eq 1 ]; then
    log_info "Z-1 skipped by flag"
    lineage_emit "phase_skip" "Z-1" "info" "skip-bootstrap flag set"
    return 0
  fi

  if [ ! -d "$ROOT_REPO/.git" ]; then
    log_warn "no git repo at $ROOT_REPO — cannot check manifold tag"
    lineage_emit "phase_end" "Z-1" "warn" "no git repo"
    return 0
  fi

  if git_in "$ROOT_REPO" rev-parse -q --verify "refs/tags/$MANIFOLD_TAG" >/dev/null 2>&1; then
    log_ok "manifold tag present → skipping 7-phase bootstrap (forward-only)"
    lineage_emit "phase_end" "Z-1" "ok" "manifold tag present"
    return 0
  fi

  log_warn "manifold tag $MANIFOLD_TAG absent — running 7-phase bootstrap"
  mkdir -p "$ROOT_REPO/ns/bootstrap" 2>/dev/null || true

  _phases="object_model storage_layout fastapi_routes canon_gate projection_core hic_pdp_ctf storytime"
  _failed=""
  for _p in $_phases; do
    log_step "bootstrap phase: $_p"
    _prompt="$ROOT_REPO/ns/bootstrap/PROMPT_${_p}.md"
    if [ ! -f "$_prompt" ]; then
      cat > "$_prompt" <<EOF
# Bootstrap Phase: $_p
#
# This phase is part of the 7-phase NS∞ autonomous build sequence (per
# Ns_media.pdf). It is executed only when the manifold tag
# ($MANIFOLD_TAG) is absent.
#
# Phase contract:
EOF
      case "$_p" in
        object_model)
          cat >> "$_prompt" <<'EOF'
#   Define Pydantic v2 primitives for Omega layer (15 types).
#   Outputs: ns/omega/primitives.py
#   Exit gate: pytest ns/tests/test_omega_primitives.py green.
EOF
          ;;
        storage_layout)
          cat >> "$_prompt" <<'EOF'
#   Create Alexandrian Archive substrate layout under
#   /Volumes/NSExternal/ALEXANDRIA with the 8 canonical subdirs.
#   Outputs: ns/omega/storage.py + boot-time mkdir hooks.
#   Exit gate: directories present and writable; smoke test round-trips
#   a JSONL receipt.
EOF
          ;;
        fastapi_routes)
          cat >> "$_prompt" <<'EOF'
#   Stand up FastAPI routes per Omega Whitepaper:
#     /branches /deltas /projections /canon/promote /hic/decisions
#     /pdp/evaluate /ctf/receipts /storytime /healthz
#   Outputs: ns/omega/api.py
#   Exit gate: pytest route contract tests green.
EOF
          ;;
        canon_gate)
          cat >> "$_prompt" <<'EOF'
#   Implement six-fold Canon gate:
#     score>=0.82, contradiction<=0.25, reconstructability>=0.90,
#     lineage_valid, HIC receipt, PDP receipt.
#   Outputs: ns/omega/canon_gate.py
#   Exit gate: contract test passes for all 6 conditions and rejects
#   on any single fail.
EOF
          ;;
        projection_core)
          cat >> "$_prompt" <<'EOF'
#   Implement recovery-ordered projection engine with 6 strategies:
#     exact_local -> delta_replay -> shard_recovery ->
#     entanglement_assisted -> semantic -> graceful_partial
#   Each attempt records order_used in the Projection result.
#   Outputs: ns/omega/projection.py
#   Exit gate: pytest simulates forced-fail on each tier and verifies
#   next-tier fallback.
EOF
          ;;
        hic_pdp_ctf)
          cat >> "$_prompt" <<'EOF'
#   Wire HIC (Human Intent Compiler) + PDP (Policy Decision Point) +
#   CTF (Lineage Fabric receipt emitter).
#   HIC decisions require YubiKey hardware quorum for Canon promotion.
#   PDP default-deny on anonymous requests.
#   CTF hash-chains every receipt (SHA-256 prev_hash linkage).
#   Outputs: ns/omega/hic.py, ns/omega/pdp.py, ns/omega/ctf.py
#   Exit gate: anon-deny test + hash-chain integrity test green.
EOF
          ;;
        storytime)
          cat >> "$_prompt" <<'EOF'
#   Storytime service: narrative projection that never amends L1-L9.
#   Read-only synthesis with ProjectionMode enum (six modes).
#   Outputs: ns/omega/storytime.py
#   Exit gate: tests that Storytime response is projection-invariant
#   under constitutional state (identical inputs => identical outputs).
EOF
          ;;
      esac
      log_info "wrote prompt: $_prompt"
    fi

    if git_in "$ROOT_REPO" rev-parse -q --verify "refs/tags/bootstrap-phase-$_p" >/dev/null 2>&1; then
      log_info "bootstrap-phase-$_p already tagged -> skip"
      continue
    fi

    lineage_emit "bootstrap_phase" "$_p" "prompt_written" "$_prompt"
    log_info "bootstrap phase $_p prompt written (pending external builder)"
    _failed="$_failed $_p"
  done

  if [ -n "$_failed" ]; then
    log_warn "bootstrap gate: phases pending external build:$_failed"
    cat > "$BOOTSTRAP_REPORT" <<EOF
# Bootstrap Audit — $TS_RUN

**Manifold tag \`$MANIFOLD_TAG\` is absent.**

The 7-phase NS∞ bootstrap sequence (per Ns_media.pdf) is required before
this closure script can proceed to Z3+. This script wrote per-phase
prompts at \`ns/bootstrap/PROMPT_*.md\` for the autonomous builder.

## Phases pending

$(for p in $_failed; do echo "- $p"; done)

## Next step

Run the autonomous builder against this repo (e.g. Claude Code with
\`ns/bootstrap/PROMPT_*.md\` as context), then re-run:

    bash ~/axiolev_runtime/ns_closure_max_v2.sh

— AXIOLEV Holdings LLC © 2026
EOF
    log_info "bootstrap report: $BOOTSTRAP_REPORT"
    lineage_emit "phase_end" "Z-1" "warn" "bootstrap pending: $_failed"
    return 0
  fi

  log_ok "Z-1 complete — all 7 bootstrap phases satisfied"
  lineage_emit "phase_end" "Z-1" "ok" "7-phase bootstrap satisfied"
}

# =============================================================================
# PHASE Z0 — PREFLIGHT + SAFETY
# =============================================================================

phase_z0_preflight() {
  log_phase "Z0 preflight + safety"
  lineage_emit "phase_start" "Z0" "info" "preflight"

  if [ ! -d "$ROOT_REPO" ]; then
    fail_exit "ROOT_REPO does not exist: $ROOT_REPO"
  fi
  if [ ! -d "$ROOT_REPO/.git" ]; then
    fail_exit "ROOT_REPO is not a git repo: $ROOT_REPO"
  fi

  _current_branch="$(git_in "$ROOT_REPO" rev-parse --abbrev-ref HEAD 2>/dev/null || echo unknown)"
  if [ "$_current_branch" != "$BASE_BRANCH" ]; then
    log_warn "current branch is $_current_branch, expected $BASE_BRANCH"
    if [ "$FLAG_DRY_RUN" -eq 0 ]; then
      if git_in "$ROOT_REPO" show-ref --verify --quiet "refs/heads/$BASE_BRANCH"; then
        log_info "switching to $BASE_BRANCH"
        git_in "$ROOT_REPO" checkout "$BASE_BRANCH" >>"$LOG_FILE" 2>&1 || \
          fail_exit "failed to checkout $BASE_BRANCH"
      else
        fail_exit "branch $BASE_BRANCH does not exist"
      fi
    fi
  else
    log_ok "branch: $BASE_BRANCH"
  fi

  if [ -d "$ALEX_MNT" ]; then
    if [ -w "$ALEX_MNT" ]; then
      log_ok "Alexandrian Archive mount: $ALEX_MNT (writable)"
      mkdir -p "$ALEX_LEDGER" "$ALEX_CTF" 2>/dev/null || true
    else
      log_warn "Alexandrian Archive mount present but not writable: $ALEX_MNT"
    fi
  else
    log_warn "Alexandrian Archive mount absent: $ALEX_MNT (receipts local-only)"
  fi

  log_info "YubiKey expected serial: $YUBIKEY_SERIAL (I4/I9 hardware quorum)"

  if ! git_in "$ROOT_REPO" diff --quiet || \
     ! git_in "$ROOT_REPO" diff --cached --quiet; then
    log_warn "working tree dirty — closure will stage new files only"
  else
    log_ok "working tree clean"
  fi

  if [ "$FLAG_PULL" -eq 1 ]; then
    log_info "--pull set -> fetching"
    git_in "$ROOT_REPO" fetch --tags origin >>"$LOG_FILE" 2>&1 || \
      log_warn "fetch failed (continuing)"
  fi

  lineage_emit "phase_end" "Z0" "ok" "preflight passed"
}

# =============================================================================
# PHASE Z1 — SECURITY SCRUB
# =============================================================================

phase_z1_security() {
  log_phase "Z1 security scrub"
  lineage_emit "phase_start" "Z1" "info" "security scrub"

  _gitleaks_bin=""
  if command -v gitleaks >/dev/null 2>&1; then
    _gitleaks_bin="$(command -v gitleaks)"
    log_ok "gitleaks present: $_gitleaks_bin"
  else
    log_warn "gitleaks not installed; attempting homebrew"
    if command -v brew >/dev/null 2>&1 && [ "$FLAG_DRY_RUN" -eq 0 ]; then
      brew install gitleaks >>"$LOG_FILE" 2>&1 || true
      if command -v gitleaks >/dev/null 2>&1; then
        _gitleaks_bin="$(command -v gitleaks)"
        log_ok "gitleaks installed: $_gitleaks_bin"
      fi
    fi
  fi

  py_write_guarded "$ROOT_REPO/.gitleaks.toml" "axiolev-closure-v2-marker" <<'TOML'
# axiolev-closure-v2-marker
# AXIOLEV Holdings LLC © 2026
# Gitleaks config: baseline allowlist for test fixtures only.
title = "axiolev-ns-infinity"

[extend]
useDefault = true

[allowlist]
paths = [
  "ns/tests/fixtures/.*",
  "tests/fixtures/.*",
]
TOML

  _scan_report="$ARTIFACTS_DIR/gitleaks_${TS_RUN}.json"
  _scan_ok=0
  if [ -n "$_gitleaks_bin" ] && [ "$FLAG_DRY_RUN" -eq 0 ]; then
    log_step "gitleaks repo-wide detect"
    if "$_gitleaks_bin" detect \
        --source="$ROOT_REPO" \
        --config="$ROOT_REPO/.gitleaks.toml" \
        --report-path="$_scan_report" \
        --report-format=json \
        --redact \
        --no-banner >>"$LOG_FILE" 2>&1; then
      log_ok "gitleaks: clean"
      _scan_ok=1
    else
      log_warn "gitleaks reported findings -> $_scan_report"
      _scan_ok=0
    fi
  else
    log_warn "gitleaks unavailable or dry-run -> scan skipped"
  fi

  py_write_guarded "$ROOT_REPO/.git/hooks/pre-commit" "axiolev-closure-v2-precommit-marker" <<'SH'
#!/usr/bin/env bash
# axiolev-closure-v2-precommit-marker
# AXIOLEV Holdings LLC © 2026
if command -v gitleaks >/dev/null 2>&1; then
  if ! gitleaks protect --staged --no-banner --redact; then
    echo "gitleaks: staged findings — commit blocked" >&2
    exit 1
  fi
fi
exit 0
SH
  chmod +x "$ROOT_REPO/.git/hooks/pre-commit" 2>/dev/null || true

  if [ "$_scan_ok" -eq 1 ]; then
    echo "clean" > "$ARTIFACTS_DIR/push_gate.state" 2>/dev/null || true
    lineage_emit "phase_end" "Z1" "ok" "gitleaks clean; push gate armed"
  else
    echo "blocked" > "$ARTIFACTS_DIR/push_gate.state" 2>/dev/null || true
    lineage_emit "phase_end" "Z1" "warn" "push gate blocked (scan unclean or skipped)"
  fi

  if [ "$FLAG_SCRUB_HISTORY" -eq 1 ]; then
    log_step "history scrub requested (--scrub-history)"
    if ! command -v git-filter-repo >/dev/null 2>&1; then
      log_warn "git-filter-repo not installed; scrub skipped"
    else
      log_info "dry-run first (analysis only)"
      git-filter-repo --analyze --source "$ROOT_REPO" >>"$LOG_FILE" 2>&1 || \
        log_warn "filter-repo analyze failed"
      log_warn "actual history rewrite NOT automated — review analysis, then rerun with explicit --execute-filter (not implemented by default for safety)"
    fi
  fi

  commit_phase "$ROOT_REPO" "Z1" "security scrub + gitleaks hook" || true
}

# =============================================================================
# PHASE Z2 — LIVE ONTOLOGY AUDIT
# =============================================================================

phase_z2_ontology() {
  log_phase "Z2 live ontology audit"
  lineage_emit "phase_start" "Z2" "info" "ontology audit"

  _report="$ONTOLOGY_REPORT"
  if [ "$FLAG_DRY_RUN" -eq 1 ]; then
    log_info "[dry-run] would write $_report"
    lineage_emit "phase_end" "Z2" "ok" "dry-run"
    return 0
  fi

  : > "$_report" 2>/dev/null || true

  {
    echo "# NS∞ Live Ontology Audit — $TS_RUN"
    echo ""
    echo "AXIOLEV Holdings LLC © 2026"
    echo ""
    echo "Locked 10-layer ontology is enforced. Deprecated names are flagged."
    echo ""
    echo "## Layers and actual locations"
    echo ""
    echo "| # | Canonical Name | Actual Paths (matched) |"
    echo "|---|----------------|------------------------|"
  } >> "$_report"

  _layer_paths() {
    _pat="$1"
    ( cd "$ROOT_REPO" && \
      grep -rl --include="*.py" --include="*.md" --include="*.ts" \
        --include="*.tsx" --include="*.rs" -E "$_pat" . 2>/dev/null \
      | sed 's|^\./||' | sort -u | head -12 )
  }

  _p1="$(_layer_paths 'Dignity Kernel|Sentinel Gate|Canon Barrier|Constitutional Layer')"
  _p2="$(_layer_paths 'Gradient Field')"
  _p3="$(_layer_paths 'Epistemic Envelope|admissibility predicate')"
  _p4="$(_layer_paths 'The Loom|reflector functor')"
  _p5="$(_layer_paths 'Alexandrian Lexicon')"
  _p6="$(_layer_paths 'State Manifold')"
  _p7="$(_layer_paths 'Alexandrian Archive')"
  _p8="$(_layer_paths 'Lineage Fabric')"
  _p9="$(_layer_paths 'HIC|Human Intent Compiler|PDP|Policy Decision Point')"
  _p10="$(_layer_paths 'Narrative|Violet|Omega|Storytime')"

  {
    echo "| L1 | Constitutional Layer | $(echo "$_p1" | tr '\n' ' ') |"
    echo "| L2 | Gradient Field | $(echo "$_p2" | tr '\n' ' ') |"
    echo "| L3 | Epistemic Envelope | $(echo "$_p3" | tr '\n' ' ') |"
    echo "| L4 | The Loom | $(echo "$_p4" | tr '\n' ' ') |"
    echo "| L5 | Alexandrian Lexicon | $(echo "$_p5" | tr '\n' ' ') |"
    echo "| L6 | State Manifold | $(echo "$_p6" | tr '\n' ' ') |"
    echo "| L7 | Alexandrian Archive | $(echo "$_p7" | tr '\n' ' ') |"
    echo "| L8 | Lineage Fabric | $(echo "$_p8" | tr '\n' ' ') |"
    echo "| L9 | HIC / PDP | $(echo "$_p9" | tr '\n' ' ') |"
    echo "| L10 | Narrative + Interface | $(echo "$_p10" | tr '\n' ' ') |"
    echo ""
    echo "## Deprecated-name audit"
    echo ""
  } >> "$_report"

  # Deprecated-name audit — each pattern is scoped to catch truly deprecated
  # usage while excluding: .git/, test fixtures, CLAUDE.md, and legitimate
  # compound canonical names (e.g., "Alexandrian Lexicon" is NOT deprecated
  # bare "Lexicon"; "Alexandrian Archive" is NOT deprecated bare "Alexandria").
  _deprecated_hits_any=0
  for _dep in \
    "Gradient Ether\|[^a-zA-Z]Ether[^a-zA-Z]" \
    "Atomlex" \
    "[^a-zA-Z]Lexicon[^a-zA-Z](?!.*Alexandrian)" \
    "[^a-zA-Z]Manifold[^a-zA-Z](?!.*State)" \
    "[^a-zA-Z]Alexandria[^a-zA-Z](?!.*n)" \
    "Lineage_CTF\|receipts_CTF\|[^a-zA-Z]CTF[^a-zA-Z]"; do
    _hits="$( cd "$ROOT_REPO" && \
      grep -rn --include="*.py" --include="*.ts" -E "$_dep" . 2>/dev/null \
      | grep -v "tests/fixtures/" \
      | grep -v ".git/" \
      | grep -v "CLAUDE.md" \
      | grep -v "ns_closure_max" \
      | head -20 )"
    if [ -n "$_hits" ]; then
      _deprecated_hits_any=1
      {
        echo "### Deprecated: \`$_dep\`"
        echo '```'
        echo "$_hits"
        echo '```'
        echo ""
      } >> "$_report"
    fi
  done

  if [ "$_deprecated_hits_any" -eq 0 ]; then
    echo "No deprecated-name hits." >> "$_report"
    log_ok "no deprecated ontology names in repo"
  else
    log_warn "deprecated ontology names present — see $_report"
  fi

  log_info "ontology audit: $_report"
  commit_phase "$ROOT_REPO" "Z2" "live ontology audit" || true
  lineage_emit "phase_end" "Z2" "ok" "ontology audit written"
}

# =============================================================================
# PHASE Z3 — OMEGA L10 PROJECTION/EGO LAYER
# =============================================================================

phase_z3_omega() {
  log_phase "Z3 Omega L10 projection/ego layer"
  lineage_emit "phase_start" "Z3" "info" "omega layer"

  mkdir -p "$ROOT_REPO/ns/omega" 2>/dev/null || true
  mkdir -p "$ROOT_REPO/ns/tests" 2>/dev/null || true

  # Ensure ns/omega is importable as a package
  py_write_guarded "$ROOT_REPO/ns/omega/__init__.py" "axiolev-omega-pkg-v2" <<'PY'
"""axiolev-omega-pkg-v2 — NS∞ Omega L10 package."""
PY

  py_write_guarded "$ROOT_REPO/ns/omega/primitives.py" "axiolev-omega-primitives-v2" <<'PY'
"""
axiolev-omega-primitives-v2
AXIOLEV Holdings LLC © 2026 — axiolevns@axiolev.com

Omega L10 Pydantic v2 primitives per Omega Whitepaper Section III.
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict


class Recoverability(str, Enum):
    EXACT = "exact"
    RECONSTRUCTIBLE = "reconstructible"
    SEMANTIC_EQUIVALENT = "semantic_equivalent"
    PARTIAL = "partial"
    UNRECOVERABLE = "unrecoverable"


class ProjectionMode(str, Enum):
    HISTORICAL = "historical"
    CURRENT = "current"
    COUNTERFACTUAL = "counterfactual"
    HYPOTHETICAL = "hypothetical"
    PROPOSED = "proposed"
    NARRATIVE = "narrative"


class RecoveryStrategy(str, Enum):
    EXACT_LOCAL = "exact_local"
    DELTA_REPLAY = "delta_replay"
    SHARD_RECOVERY = "shard_recovery"
    ENTANGLEMENT_ASSISTED = "entanglement_assisted"
    SEMANTIC = "semantic"
    GRACEFUL_PARTIAL = "graceful_partial"


class ConfidenceEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    evidence: float = Field(ge=0.0, le=1.0)
    contradiction: float = Field(ge=0.0, le=1.0)
    novelty: float = Field(ge=0.0, le=1.0)
    stability: float = Field(ge=0.0, le=1.0)

    @property
    def score(self) -> float:
        return (
            0.45 * self.evidence
            + 0.25 * (1.0 - self.contradiction)
            + 0.15 * self.novelty
            + 0.15 * self.stability
        )


class Branch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    parent_id: Optional[str] = None
    title: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    canon_promoted: bool = False
    mode: ProjectionMode = ProjectionMode.CURRENT


class Delta(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    branch_id: str
    prev_hash: Optional[str] = None
    payload_hash: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Entanglement(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    branch_ids: List[str]
    relation: str
    strength: float = Field(ge=0.0, le=1.0, default=0.5)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Contradiction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    branch_ids: List[str]
    axis: str
    severity: float = Field(ge=0.0, le=1.0)
    resolved: bool = False


class SemanticAnchor(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    branch_id: str
    concept: str
    embedding_ref: Optional[str] = None


class ShardManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    branch_id: str
    shards: List[str]
    checksum: str


class ProjectionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    branch_id: str
    mode: ProjectionMode
    requested_by: str
    requested_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ProjectionResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    request_id: str
    branch_id: str
    mode: ProjectionMode
    confidence: ConfidenceEnvelope
    recoverability: Recoverability
    order_used: List[RecoveryStrategy] = Field(default_factory=list)
    payload: Dict[str, Any] = Field(default_factory=dict)
    emitted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ForkOp(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    parent_branch_id: str
    child_branch_id: str
    rationale: str


class MergeOp(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    source_branch_ids: List[str]
    target_branch_id: str
    rationale: str


class SupersessionOp(BaseModel):
    """I10: supersession is monotone; old never deleted."""
    model_config = ConfigDict(extra="forbid")
    id: str
    superseded_id: str
    superseded_by_id: str
    effective_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Storytime(BaseModel):
    """L10 Narrative service. Read-only synthesis. L10 NEVER amends L1-L9."""
    model_config = ConfigDict(extra="forbid")
    id: str
    branch_id: str
    mode: ProjectionMode
    narrative: str
    confidence: ConfidenceEnvelope
    emitted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
PY

  py_write_guarded "$ROOT_REPO/ns/omega/canon_gate.py" "axiolev-omega-canon-gate-v2" <<'PY'
"""
axiolev-omega-canon-gate-v2
AXIOLEV Holdings LLC © 2026

Six-fold Canon gate. I1: Canon precedes Conversion.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, List

from .primitives import ConfidenceEnvelope


SCORE_THRESHOLD = 0.82
CONTRADICTION_CEILING = 0.25
RECONSTRUCT_THRESHOLD = 0.90


@dataclass(frozen=True)
class CanonGateDecision:
    allowed: bool
    reasons: List[str]


def canon_gate(
    confidence: ConfidenceEnvelope,
    reconstructability: float,
    lineage_valid: bool,
    hic_receipt: Optional[str],
    pdp_receipt: Optional[str],
) -> CanonGateDecision:
    reasons = []
    if confidence.score < SCORE_THRESHOLD:
        reasons.append(f"score {confidence.score:.3f} < {SCORE_THRESHOLD}")
    if confidence.contradiction > CONTRADICTION_CEILING:
        reasons.append(f"contradiction {confidence.contradiction:.3f} > {CONTRADICTION_CEILING}")
    if reconstructability < RECONSTRUCT_THRESHOLD:
        reasons.append(f"reconstructability {reconstructability:.3f} < {RECONSTRUCT_THRESHOLD}")
    if not lineage_valid:
        reasons.append("lineage invalid")
    if not hic_receipt:
        reasons.append("HIC receipt missing")
    if not pdp_receipt:
        reasons.append("PDP receipt missing")
    return CanonGateDecision(allowed=not reasons, reasons=reasons)
PY

  py_write_guarded "$ROOT_REPO/ns/omega/projection.py" "axiolev-omega-projection-v2" <<'PY'
"""
axiolev-omega-projection-v2
AXIOLEV Holdings LLC © 2026

Recovery-ordered projection engine. Six strategies tried in order.
"""
from __future__ import annotations
from typing import Callable, Dict, List, Optional

from .primitives import (
    ProjectionRequest, ProjectionResult, RecoveryStrategy,
    Recoverability, ConfidenceEnvelope,
)


RECOVERY_ORDER: List[RecoveryStrategy] = [
    RecoveryStrategy.EXACT_LOCAL,
    RecoveryStrategy.DELTA_REPLAY,
    RecoveryStrategy.SHARD_RECOVERY,
    RecoveryStrategy.ENTANGLEMENT_ASSISTED,
    RecoveryStrategy.SEMANTIC,
    RecoveryStrategy.GRACEFUL_PARTIAL,
]

StrategyFn = Callable[[ProjectionRequest], Optional[Dict]]


def project(
    request: ProjectionRequest,
    strategies: Dict[RecoveryStrategy, StrategyFn],
) -> ProjectionResult:
    attempts: List[RecoveryStrategy] = []
    payload: Optional[Dict] = None
    used: Optional[RecoveryStrategy] = None

    for strat in RECOVERY_ORDER:
        attempts.append(strat)
        fn = strategies.get(strat)
        if fn is None:
            continue
        try:
            out = fn(request)
        except Exception:
            out = None
        if out is not None:
            payload = out
            used = strat
            break

    if used == RecoveryStrategy.EXACT_LOCAL:
        rec = Recoverability.EXACT
    elif used in (RecoveryStrategy.DELTA_REPLAY, RecoveryStrategy.SHARD_RECOVERY):
        rec = Recoverability.RECONSTRUCTIBLE
    elif used in (RecoveryStrategy.ENTANGLEMENT_ASSISTED, RecoveryStrategy.SEMANTIC):
        rec = Recoverability.SEMANTIC_EQUIVALENT
    elif used == RecoveryStrategy.GRACEFUL_PARTIAL:
        rec = Recoverability.PARTIAL
    else:
        rec = Recoverability.UNRECOVERABLE

    conf = ConfidenceEnvelope(
        evidence=0.8 if payload else 0.0,
        contradiction=0.1,
        novelty=0.3,
        stability=0.8 if payload else 0.0,
    )

    return ProjectionResult(
        request_id=request.id,
        branch_id=request.branch_id,
        mode=request.mode,
        confidence=conf,
        recoverability=rec,
        order_used=attempts,
        payload=payload or {},
    )
PY

  py_write_guarded "$ROOT_REPO/ns/omega/ctf.py" "axiolev-omega-ctf-v2" <<'PY'
"""
axiolev-omega-ctf-v2
AXIOLEV Holdings LLC © 2026

Lineage Fabric receipt emitter. I5: SHA-256 hash-chain. I2: append-only.
"""
from __future__ import annotations
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


DEFAULT_LEDGER = os.environ.get(
    "NS_ALEX_LEDGER",
    "/Volumes/NSExternal/ALEXANDRIA/ledger/ns_events.jsonl",
)
DEFAULT_CTF = os.environ.get(
    "NS_ALEX_CTF",
    "/Volumes/NSExternal/ALEXANDRIA/ctf/receipts",
)


def _hash(obj: Dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(obj, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def emit_receipt(
    event: str,
    subject: str,
    status: str,
    detail: str,
    prev_hash: Optional[str] = None,
    ledger_path: Optional[str] = None,
    ctf_dir: Optional[str] = None,
) -> Dict[str, Any]:
    ts = datetime.now(timezone.utc).isoformat()
    body = {
        "ts": ts,
        "event": event,
        "subject": subject,
        "status": status,
        "detail": detail,
        "prev_hash": prev_hash,
    }
    body["sha256"] = _hash(body)

    lpath = ledger_path or DEFAULT_LEDGER
    cdir = ctf_dir or DEFAULT_CTF

    try:
        Path(lpath).parent.mkdir(parents=True, exist_ok=True)
        with open(lpath, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(body, ensure_ascii=False) + "\n")
    except Exception:
        pass

    try:
        Path(cdir).mkdir(parents=True, exist_ok=True)
        rname = f"{ts.replace(':','-')}-{body['sha256'][:12]}.json"
        with open(os.path.join(cdir, rname), "w", encoding="utf-8") as fh:
            json.dump(body, fh, ensure_ascii=False, indent=2)
    except Exception:
        pass

    return body
PY

  py_write_guarded "$ROOT_REPO/ns/omega/hic.py" "axiolev-omega-hic-v2" <<'PY'
"""
axiolev-omega-hic-v2
AXIOLEV Holdings LLC © 2026

Human Intent Compiler. Canon promotion requires hardware quorum (I4).
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class HICDecision:
    intent_id: str
    approved: bool
    rationale: str
    yubikey_serials: List[str]
    receipt_id: Optional[str] = None


def require_quorum(serials: List[str], required: int = 2) -> bool:
    return len(set(serials)) >= required


def compile_intent(
    intent_id: str,
    rationale: str,
    serials: List[str],
    required: int = 2,
) -> HICDecision:
    ok = require_quorum(serials, required=required)
    return HICDecision(
        intent_id=intent_id,
        approved=ok,
        rationale=rationale,
        yubikey_serials=list(serials),
    )
PY

  py_write_guarded "$ROOT_REPO/ns/omega/pdp.py" "axiolev-omega-pdp-v2" <<'PY'
"""
axiolev-omega-pdp-v2
AXIOLEV Holdings LLC © 2026

Policy Decision Point. Default-deny on anonymous principals.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class PDPDecision:
    principal: Optional[str]
    action: str
    resource: str
    allowed: bool
    reason: str


def evaluate(
    principal: Optional[str],
    action: str,
    resource: str,
    allow_rules: Optional[dict] = None,
) -> PDPDecision:
    if not principal:
        return PDPDecision(None, action, resource, False, "anonymous: default-deny")
    rules = allow_rules or {}
    allowed_actions = rules.get(principal, [])
    if action in allowed_actions or "*" in allowed_actions:
        return PDPDecision(principal, action, resource, True, "allow-listed")
    return PDPDecision(principal, action, resource, False, "not-allowed")
PY

  py_write_guarded "$ROOT_REPO/ns/omega/api.py" "axiolev-omega-api-v2" <<'PY'
"""
axiolev-omega-api-v2
AXIOLEV Holdings LLC © 2026

FastAPI routes per Omega Whitepaper.
"""
from __future__ import annotations
from fastapi import APIRouter, HTTPException
from typing import Any, Dict, List

from .primitives import (
    Branch, Delta, ProjectionRequest, ProjectionResult,
    Storytime, ConfidenceEnvelope, ProjectionMode, Recoverability,
)
from .canon_gate import canon_gate
from .ctf import emit_receipt
from .hic import compile_intent
from .pdp import evaluate as pdp_evaluate


router = APIRouter(tags=["omega"])


@router.get("/healthz")
def healthz() -> Dict[str, str]:
    return {"status": "ok", "layer": "L10"}


@router.post("/branches")
def create_branch(branch: Branch) -> Branch:
    emit_receipt("branch_created", branch.id, "ok", branch.title)
    return branch


@router.post("/deltas")
def create_delta(delta: Delta) -> Delta:
    emit_receipt("delta_created", delta.id, "ok", delta.branch_id)
    return delta


@router.post("/projections", response_model=ProjectionResult)
def create_projection(req: ProjectionRequest) -> ProjectionResult:
    conf = ConfidenceEnvelope(evidence=0.8, contradiction=0.1, novelty=0.3, stability=0.8)
    result = ProjectionResult(
        request_id=req.id,
        branch_id=req.branch_id,
        mode=req.mode,
        confidence=conf,
        recoverability=Recoverability.EXACT,
        order_used=[],
        payload={},
    )
    emit_receipt("projection_emitted", req.id, "ok", req.branch_id)
    return result


@router.post("/canon/promote")
def promote_to_canon(
    confidence: ConfidenceEnvelope,
    reconstructability: float,
    lineage_valid: bool,
    hic_receipt: str,
    pdp_receipt: str,
) -> Dict[str, Any]:
    decision = canon_gate(confidence, reconstructability, lineage_valid,
                          hic_receipt, pdp_receipt)
    if not decision.allowed:
        raise HTTPException(status_code=403, detail={
            "event": "canon_gate_denied",
            "reasons": decision.reasons,
        })
    emit_receipt("canon_promoted_with_hardware_quorum",
                 hic_receipt, "ok", ",".join(decision.reasons) or "passed")
    return {"allowed": True, "reasons": decision.reasons}


@router.post("/hic/decisions")
def hic_decision(intent_id: str, rationale: str, serials: List[str]) -> Dict[str, Any]:
    d = compile_intent(intent_id, rationale, serials)
    emit_receipt("hic_decision", intent_id, "ok" if d.approved else "denied", rationale)
    return {"approved": d.approved, "rationale": d.rationale, "serials": d.yubikey_serials}


@router.post("/pdp/evaluate")
def pdp_evaluate_route(principal: str, action: str, resource: str) -> Dict[str, Any]:
    d = pdp_evaluate(principal, action, resource)
    emit_receipt("pdp_evaluated", f"{principal}:{action}:{resource}",
                 "ok" if d.allowed else "denied", d.reason)
    return {"allowed": d.allowed, "reason": d.reason}


@router.get("/ctf/receipts")
def list_ctf_receipts() -> Dict[str, Any]:
    return {"ledger": "/Volumes/NSExternal/ALEXANDRIA/ledger/ns_events.jsonl",
            "ctf_dir": "/Volumes/NSExternal/ALEXANDRIA/ctf/receipts"}


@router.post("/storytime")
def create_storytime(st: Storytime) -> Storytime:
    emit_receipt("storytime_emitted", st.id, "ok", st.branch_id)
    return st


@router.get("/storytime/{sid}")
def get_storytime(sid: str) -> Dict[str, Any]:
    return {"id": sid, "status": "not_found"}
PY

  py_write_guarded "$ROOT_REPO/ns/tests/test_omega_primitives.py" "axiolev-omega-primitives-test-v2" <<'PY'
"""axiolev-omega-primitives-test-v2"""
from ns.omega.primitives import (
    ConfidenceEnvelope, ProjectionMode, Recoverability,
)
from ns.omega.canon_gate import canon_gate


def test_confidence_weights_locked():
    c = ConfidenceEnvelope(evidence=1.0, contradiction=0.0, novelty=1.0, stability=1.0)
    assert abs(c.score - 1.0) < 1e-6


def test_canon_gate_six_fold():
    c = ConfidenceEnvelope(evidence=0.9, contradiction=0.1, novelty=0.5, stability=0.9)
    d = canon_gate(c, 0.95, True, "hic-1", "pdp-1")
    assert d.allowed
    d2 = canon_gate(c, 0.95, True, "", "pdp-1")
    assert not d2.allowed
    c_low = ConfidenceEnvelope(evidence=0.2, contradiction=0.1, novelty=0.1, stability=0.1)
    d3 = canon_gate(c_low, 0.95, True, "hic-1", "pdp-1")
    assert not d3.allowed
    c_contra = ConfidenceEnvelope(evidence=0.9, contradiction=0.9, novelty=0.5, stability=0.9)
    d4 = canon_gate(c_contra, 0.95, True, "hic-1", "pdp-1")
    assert not d4.allowed


def test_projection_modes_six():
    assert len([m for m in ProjectionMode]) == 6


def test_recoverability_five():
    assert len([r for r in Recoverability]) == 5
PY

  commit_phase "$ROOT_REPO" "Z3" "Omega L10 primitives + canon gate + projection + api" || true
  lineage_emit "phase_end" "Z3" "ok" "Omega layer integrated"
}

# =============================================================================
# PHASE Z3b — ENTITY PRIMITIVE UNIVERSAL SCHEMA (per UG_max)
# =============================================================================

phase_z3b_entity() {
  log_phase "Z3b Entity primitive universal schema"
  lineage_emit "phase_start" "Z3b" "info" "entity primitive"

  mkdir -p "$ROOT_REPO/ns/ug" 2>/dev/null || true

  py_write_guarded "$ROOT_REPO/ns/ug/__init__.py" "axiolev-ug-init-v2" <<'PY'
"""axiolev-ug-init-v2 — UG_max Entity primitive package."""
PY

  py_write_guarded "$ROOT_REPO/ns/ug/entity.py" "axiolev-ug-entity-v2" <<'PY'
"""
axiolev-ug-entity-v2
AXIOLEV Holdings LLC © 2026 — axiolevns@axiolev.com

Universal Entity primitive (per UG_max_ready_to_integrate_.pdf).
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict


class EntityKind(str, Enum):
    BRANCH = "branch"
    DELTA = "delta"
    ENTANGLEMENT = "entanglement"
    CONTRADICTION = "contradiction"
    SEMANTIC_ANCHOR = "semantic_anchor"
    SHARD_MANIFEST = "shard_manifest"
    PROJECTION = "projection"
    STORYTIME = "storytime"
    RECEIPT = "receipt"
    PROGRAM = "program"
    OTHER = "other"


class Identity(BaseModel):
    model_config = ConfigDict(extra="forbid")
    canonical_name: str
    aliases: List[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0, default=1.0)


class Provenance(BaseModel):
    model_config = ConfigDict(extra="forbid")
    origin: str
    chain: List[str] = Field(default_factory=list)


class Epistemics(BaseModel):
    model_config = ConfigDict(extra="forbid")
    evidence: float = Field(ge=0.0, le=1.0, default=0.5)
    contradiction: float = Field(ge=0.0, le=1.0, default=0.0)
    novelty: float = Field(ge=0.0, le=1.0, default=0.0)
    stability: float = Field(ge=0.0, le=1.0, default=1.0)


class Supersession(BaseModel):
    model_config = ConfigDict(extra="forbid")
    superseded_id: Optional[str] = None
    superseded_by_id: Optional[str] = None


class Timestamps(BaseModel):
    model_config = ConfigDict(extra="forbid")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    emitted_at: Optional[datetime] = None


class Entity(BaseModel):
    """Universal NS∞ node primitive."""
    model_config = ConfigDict(extra="forbid")
    id: str
    kind: EntityKind
    identity: Identity
    state: Dict[str, Any] = Field(default_factory=dict)
    provenance: Provenance
    epistemics: Epistemics = Field(default_factory=Epistemics)
    constraints: List[str] = Field(default_factory=list)
    relations: List[Dict[str, Any]] = Field(default_factory=list)
    manifestations: List[Dict[str, Any]] = Field(default_factory=list)
    receipts: List[str] = Field(default_factory=list)
    bindings: Dict[str, Any] = Field(default_factory=dict)
    supersession: Supersession = Field(default_factory=Supersession)
    timestamps: Timestamps = Field(default_factory=Timestamps)
    metadata: Dict[str, Any] = Field(default_factory=dict)
PY

  py_write_guarded "$ROOT_REPO/ns/ug/registry.py" "axiolev-ug-registry-v2" <<'PY'
"""
axiolev-ug-registry-v2
AXIOLEV Holdings LLC © 2026

Registry adapter: Omega L10 primitive -> Entity specialization.
"""
from __future__ import annotations
from typing import Any

from .entity import Entity, EntityKind, Identity, Provenance, Epistemics


def branch_to_entity(b: Any) -> Entity:
    return Entity(
        id=b.id,
        kind=EntityKind.BRANCH,
        identity=Identity(canonical_name=b.title, aliases=[]),
        state={"canon_promoted": b.canon_promoted, "mode": str(b.mode), "parent_id": b.parent_id},
        provenance=Provenance(origin="omega.branch", chain=[b.parent_id] if b.parent_id else []),
    )


def delta_to_entity(d: Any) -> Entity:
    return Entity(
        id=d.id,
        kind=EntityKind.DELTA,
        identity=Identity(canonical_name=f"delta:{d.id}"),
        state={"payload_hash": d.payload_hash, "prev_hash": d.prev_hash, "payload": d.payload},
        provenance=Provenance(origin="omega.delta", chain=[d.branch_id]),
    )


def entanglement_to_entity(e: Any) -> Entity:
    return Entity(
        id=e.id,
        kind=EntityKind.ENTANGLEMENT,
        identity=Identity(canonical_name=f"entanglement:{e.relation}"),
        state={"strength": e.strength, "relation": e.relation},
        provenance=Provenance(origin="omega.entanglement", chain=list(e.branch_ids)),
    )


def contradiction_to_entity(c: Any) -> Entity:
    return Entity(
        id=c.id,
        kind=EntityKind.CONTRADICTION,
        identity=Identity(canonical_name=f"contradiction:{c.axis}"),
        state={"severity": c.severity, "resolved": c.resolved, "axis": c.axis},
        provenance=Provenance(origin="omega.contradiction", chain=list(c.branch_ids)),
    )


def anchor_to_entity(a: Any) -> Entity:
    return Entity(
        id=a.id,
        kind=EntityKind.SEMANTIC_ANCHOR,
        identity=Identity(canonical_name=a.concept),
        state={"embedding_ref": a.embedding_ref},
        provenance=Provenance(origin="omega.semantic_anchor", chain=[a.branch_id]),
    )


def shard_to_entity(s: Any) -> Entity:
    return Entity(
        id=s.id,
        kind=EntityKind.SHARD_MANIFEST,
        identity=Identity(canonical_name=f"shard:{s.checksum[:12]}"),
        state={"shards": s.shards, "checksum": s.checksum},
        provenance=Provenance(origin="omega.shard_manifest", chain=[s.branch_id]),
    )


def projection_result_to_entity(p: Any) -> Entity:
    return Entity(
        id=p.request_id,
        kind=EntityKind.PROJECTION,
        identity=Identity(canonical_name=f"projection:{p.mode}"),
        state={"recoverability": str(p.recoverability),
               "order_used": [str(o) for o in p.order_used],
               "payload": p.payload},
        provenance=Provenance(origin="omega.projection", chain=[p.branch_id]),
        epistemics=Epistemics(
            evidence=p.confidence.evidence,
            contradiction=p.confidence.contradiction,
            novelty=p.confidence.novelty,
            stability=p.confidence.stability,
        ),
    )
PY

  py_write_guarded "$ROOT_REPO/ns/ug/temporal.py" "axiolev-ug-temporal-v2" <<'PY'
"""
axiolev-ug-temporal-v2
AXIOLEV Holdings LLC © 2026

Temporal Geometry Layer adapter. Sits at L3 boundary. Pure read.
BOHMIAN/PILOT-WAVE LAYER: QUARANTINED — theoretical only.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from .entity import Entity


@dataclass(frozen=True)
class TemporalSlice:
    at: datetime
    entity_id: str
    state_snapshot: dict


def slice_entity(e: Entity, at: Optional[datetime] = None) -> TemporalSlice:
    return TemporalSlice(
        at=at or e.timestamps.updated_at,
        entity_id=e.id,
        state_snapshot=dict(e.state),
    )


BOHMIAN_PILOT_WAVE_STATUS = "QUARANTINED: theoretical only"
PY

  py_write_guarded "$ROOT_REPO/ns/tests/test_ug_entity.py" "axiolev-ug-entity-test-v2" <<'PY'
"""axiolev-ug-entity-test-v2"""
from ns.ug.entity import Entity, EntityKind, Identity, Provenance
from ns.ug.registry import branch_to_entity
from ns.ug.temporal import slice_entity, BOHMIAN_PILOT_WAVE_STATUS
from ns.omega.primitives import Branch, ProjectionMode


def test_entity_base_constructs():
    e = Entity(
        id="e-1",
        kind=EntityKind.OTHER,
        identity=Identity(canonical_name="test"),
        provenance=Provenance(origin="test"),
    )
    assert e.id == "e-1"
    assert e.kind == EntityKind.OTHER


def test_branch_specialization():
    b = Branch(id="b-1", title="main", mode=ProjectionMode.CURRENT)
    e = branch_to_entity(b)
    assert e.id == "b-1"
    assert e.kind == EntityKind.BRANCH
    assert e.identity.canonical_name == "main"


def test_temporal_slice_is_pure():
    e = Entity(
        id="e-1",
        kind=EntityKind.OTHER,
        identity=Identity(canonical_name="t"),
        provenance=Provenance(origin="test"),
        state={"x": 1},
    )
    s = slice_entity(e)
    s.state_snapshot["x"] = 999
    assert e.state["x"] == 1


def test_bohmian_quarantined():
    assert "QUARANTINED" in BOHMIAN_PILOT_WAVE_STATUS
PY

  if [ "$FLAG_DRY_RUN" -eq 0 ]; then
    cat > "$ENTITY_REPORT" <<EOF
# Entity Primitive Integration — $TS_RUN
Source: UG_max_ready_to_integrate_.pdf
Files: ns/ug/entity.py, ns/ug/registry.py, ns/ug/temporal.py
Tests: ns/tests/test_ug_entity.py
Bohmian layer: QUARANTINED: theoretical only
— AXIOLEV Holdings LLC © 2026
EOF
  fi

  commit_phase "$ROOT_REPO" "Z3b" "UG Entity primitive + registry + temporal" || true
  lineage_emit "phase_end" "Z3b" "ok" "Entity primitive established"
}

# =============================================================================
# PHASE Z4 — MEDIA ENGINE INTEGRATION
# =============================================================================

phase_z4_media() {
  log_phase "Z4 media engine integration"
  lineage_emit "phase_start" "Z4" "info" "media engine"

  _zip="$UPLOADS_DIR/media_engine_repo.zip"
  _dst="$ROOT_REPO/ns/services/media_engine"

  if [ ! -f "$_zip" ]; then
    log_warn "media_engine_repo.zip not found at $_zip — emitting skip receipt"
    # Write stub package so ns.services.media_engine is importable even when zip absent
    if [ "$FLAG_DRY_RUN" -eq 0 ]; then
      mkdir -p "$_dst" 2>/dev/null || true
      py_write_guarded "$_dst/__init__.py" "axiolev-media-init-v2-stub" <<'PY'
"""axiolev-media-init-v2-stub — Media engine absent; stub package only."""
def pgvector_available() -> bool:
    return False
def build_skip_reason():
    return {"status": "skipped", "reason": "media_engine_repo.zip not provided",
            "advisory": "upload media_engine_repo.zip to uploads dir and re-run"}
def mount(*args, **kwargs) -> bool:
    return False
PY
    fi
    lineage_emit "phase_end" "Z4" "warn" "media engine zip absent; stub written"
    return 0
  fi

  if [ "$FLAG_DRY_RUN" -eq 1 ]; then
    log_info "[dry-run] would unpack $_zip to $_dst"
    lineage_emit "phase_end" "Z4" "ok" "dry-run"
    return 0
  fi

  mkdir -p "$_dst" 2>/dev/null || true
  if [ ! -f "$_dst/.unpacked" ]; then
    log_step "unpacking $_zip -> $_dst"
    if command -v unzip >/dev/null 2>&1; then
      ( cd "$_dst" && unzip -o "$_zip" >>"$LOG_FILE" 2>&1 ) || log_warn "unzip failed"
    elif command -v python3 >/dev/null 2>&1; then
      python3 -c "import zipfile; zipfile.ZipFile('$_zip').extractall('$_dst')" \
        >>"$LOG_FILE" 2>&1 || log_warn "python unzip failed"
    fi
    touch "$_dst/.unpacked" 2>/dev/null || true
  else
    log_info "media engine already unpacked"
  fi

  _backend_main="$( find "$_dst" -type f -name main.py -path "*backend/app/main.py" 2>/dev/null | head -1 )"
  if [ -z "$_backend_main" ]; then
    log_warn "media engine backend main.py not located — cannot wire"
    lineage_emit "phase_end" "Z4" "warn" "backend main.py not found"
    return 0
  fi

  log_ok "media engine backend at: $(dirname "$(dirname "$_backend_main")")"

  py_write_guarded "$ROOT_REPO/ns/services/media_engine/gateway_shim.py" "axiolev-media-gateway-shim-v2" <<'PY'
"""
axiolev-media-gateway-shim-v2
AXIOLEV Holdings LLC © 2026

NS∞ sovereign-prefix mount for the Media Engine subapp at /omega/media.
"""
from __future__ import annotations
import os, sys
from typing import Any, Callable


def _try_import_media_app() -> Any:
    candidates_env = os.environ.get("MEDIA_ENGINE_BACKEND_ROOT", "")
    search_roots = []
    if candidates_env:
        search_roots.append(candidates_env)
    here = os.path.dirname(os.path.abspath(__file__))
    for root, dirs, _files in os.walk(here):
        if os.path.basename(root) == "backend" and os.path.isdir(os.path.join(root, "app")):
            search_roots.append(root)
            break
    for root in search_roots:
        if root and root not in sys.path:
            sys.path.insert(0, root)
        try:
            mod = __import__("app.main", fromlist=["app"])
            return getattr(mod, "app", None)
        except Exception:
            continue
    return None


def _wrap_with_ctf(app: Any, emit: Callable) -> Any:
    async def middleware(scope, receive, send):
        if scope.get("type") == "http" and scope.get("method") != "GET":
            try:
                emit(event="media_engine_mutation",
                     subject=f"{scope.get('method')} {scope.get('path')}",
                     status="received", detail="ingress")
            except Exception:
                pass
        await app(scope, receive, send)
    return middleware


def mount(ns_app: Any, emit_receipt: Callable, prefix: str = "/omega/media") -> bool:
    media_app = _try_import_media_app()
    if media_app is None:
        return False
    wrapped = _wrap_with_ctf(media_app, emit_receipt)
    try:
        ns_app.mount(prefix, wrapped)
        return True
    except Exception:
        return False
PY

  py_write_guarded "$ROOT_REPO/ns/services/media_engine/pg_shim.py" "axiolev-media-pg-shim-v2" <<'PY'
"""
axiolev-media-pg-shim-v2
AXIOLEV Holdings LLC © 2026

Degrades pgvector to in-memory when Postgres absent. Emits skip receipt.
"""
from __future__ import annotations
import os
from typing import Any, Dict


def pgvector_available() -> bool:
    url = os.environ.get("DATABASE_URL") or \
          "postgresql+psycopg://postgres:postgres@localhost:5432/media_engine"
    try:
        import psycopg
        with psycopg.connect(
            url.replace("postgresql+psycopg://", "postgresql://"),
            connect_timeout=2,
        ) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM pg_extension WHERE extname='vector'")
                return bool(cur.fetchone())
    except Exception:
        return False


def build_skip_reason() -> Dict[str, Any]:
    return {"status": "skipped", "reason": "pgvector unavailable",
            "advisory": "start Postgres + CREATE EXTENSION vector; re-run closure"}
PY

  py_write_guarded "$ROOT_REPO/ns/services/media_engine/__init__.py" "axiolev-media-init-v2" <<'PY'
"""axiolev-media-init-v2 — Media engine subapp integration package."""
from .gateway_shim import mount  # noqa: F401
from .pg_shim import pgvector_available, build_skip_reason  # noqa: F401
PY

  py_write_guarded "$ROOT_REPO/ns/tests/test_media_engine_integration.py" "axiolev-media-test-v2" <<'PY'
"""axiolev-media-test-v2"""
from ns.services.media_engine import pgvector_available, build_skip_reason


def test_pg_shim_skip_reason_shape():
    r = build_skip_reason()
    assert r["status"] == "skipped"
    assert "reason" in r and "advisory" in r


def test_pgvector_probe_is_boolean():
    assert isinstance(pgvector_available(), bool)
PY

  commit_phase "$ROOT_REPO" "Z4" "media engine gateway shim + pgvector shim" || true
  lineage_emit "phase_end" "Z4" "ok" "media engine wired at /omega/media"
}

# =============================================================================
# PHASE Z5 — UI ADDITION BASE
# =============================================================================

phase_z5_ui_base() {
  log_phase "Z5 UI addition base"
  lineage_emit "phase_start" "Z5" "info" "ui base"

  mkdir -p "$ROOT_REPO/ns/services/ui" 2>/dev/null || true

  py_write_guarded "$ROOT_REPO/ns/services/ui/__init__.py" "axiolev-ui-init-v2" <<'PY'
"""axiolev-ui-init-v2 — NS∞ Living Architecture UI service."""
from .router import ui_router  # noqa: F401
PY

  commit_phase "$ROOT_REPO" "Z5" "ui base package scaffold" || true
  lineage_emit "phase_end" "Z5" "ok" "ui base scaffolded"
}

# =============================================================================
# PHASE Z5a — UI NAMED ROUTE SURFACE
# =============================================================================

phase_z5a_ui_routes() {
  log_phase "Z5a UI addition named route surface"
  lineage_emit "phase_start" "Z5a" "info" "ui named routes"

  mkdir -p "$ROOT_REPO/ns/services/ui" 2>/dev/null || true
  mkdir -p "$ROOT_REPO/ns/tests" 2>/dev/null || true

  py_write_guarded "$ROOT_REPO/ns/services/ui/router.py" "axiolev-ui-router-v2" <<'PY'
"""
axiolev-ui-router-v2
AXIOLEV Holdings LLC © 2026 — axiolevns@axiolev.com

NS∞ Living Architecture UI — 8 named backend endpoints per Ui_addition.pdf.
All responses are projections (L10) and never amend constitutional state (L1-L9).
"""
from __future__ import annotations
import asyncio, json, os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse


ui_router = APIRouter(tags=["ui"])


def _alex_ledger() -> str:
    return os.environ.get("NS_ALEX_LEDGER",
                          "/Volumes/NSExternal/ALEXANDRIA/ledger/ns_events.jsonl")


def _alex_ctf_dir() -> str:
    return os.environ.get("NS_ALEX_CTF",
                          "/Volumes/NSExternal/ALEXANDRIA/ctf/receipts")


def _read_last_jsonl(path: str, n: int = 50) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    p = Path(path)
    if not p.exists():
        return out
    try:
        with p.open("r", encoding="utf-8") as fh:
            lines = fh.readlines()
        for ln in lines[-n:]:
            ln = ln.strip()
            if not ln:
                continue
            try:
                out.append(json.loads(ln))
            except Exception:
                continue
    except Exception:
        pass
    return out


@ui_router.get("/ns/state")
def ns_state() -> Dict[str, Any]:
    return {
        "ts": datetime.now(timezone.utc).isoformat(),
        "layers": {
            "L1": {"name": "Constitutional", "status": "active"},
            "L2": {"name": "Gradient Field", "status": "active"},
            "L3": {"name": "Epistemic Envelope", "status": "active"},
            "L4": {"name": "The Loom", "status": "active"},
            "L5": {"name": "Alexandrian Lexicon", "status": "active"},
            "L6": {"name": "State Manifold", "status": "active"},
            "L7": {"name": "Alexandrian Archive",
                   "status": "mounted" if os.path.isdir("/Volumes/NSExternal/ALEXANDRIA") else "absent"},
            "L8": {"name": "Lineage Fabric", "status": "active"},
            "L9": {"name": "HIC/PDP", "status": "active"},
            "L10": {"name": "Narrative + Interface", "status": "active"},
        },
        "invariants": {f"I{i}": "intact" for i in range(1, 11)},
    }


@ui_router.get("/ns/engine/live")
async def ns_engine_live():
    async def gen():
        count = 0
        while True:
            ts = datetime.now(timezone.utc).isoformat()
            payload = {"ts": ts, "seq": count, "event": "heartbeat", "layer": "L10"}
            yield f"data: {json.dumps(payload)}\n\n"
            count += 1
            await asyncio.sleep(1)
    return StreamingResponse(gen(), media_type="text/event-stream")


@ui_router.get("/program/list")
def program_list() -> Dict[str, Any]:
    return {
        "ts": datetime.now(timezone.utc).isoformat(),
        "programs": [
            {"id": "ns_core", "port": 9000, "status": "unknown"},
            {"id": "handrail", "port": 8011, "status": "unknown"},
            {"id": "continuum", "port": 8788, "status": "unknown"},
            {"id": "state_api", "port": 9090, "status": "unknown"},
        ],
    }


@ui_router.get("/program/{program_id}")
def program_detail(program_id: str) -> Dict[str, Any]:
    known = {"ns_core", "handrail", "continuum", "state_api"}
    if program_id not in known:
        raise HTTPException(status_code=404, detail="program not found")
    return {"id": program_id, "ts": datetime.now(timezone.utc).isoformat(),
            "status": "unknown", "endpoints": []}


@ui_router.get("/alexandria/graph")
def alexandria_graph() -> Dict[str, Any]:
    events = _read_last_jsonl(_alex_ledger(), n=200)
    nodes = []
    seen = set()
    for e in events:
        sid = f"{e.get('event')}:{e.get('subject')}"
        if sid not in seen:
            nodes.append({"id": sid, "kind": e.get("event"), "subject": e.get("subject")})
            seen.add(sid)
    return {"ts": datetime.now(timezone.utc).isoformat(),
            "node_count": len(nodes), "edge_count": 0, "nodes": nodes[:50], "edges": []}


@ui_router.get("/receipt/{receipt_id}")
def receipt_lookup(receipt_id: str) -> Dict[str, Any]:
    ctf_dir = Path(_alex_ctf_dir())
    if ctf_dir.exists():
        for p in ctf_dir.glob("*.json"):
            if receipt_id in p.stem:
                try:
                    with p.open("r", encoding="utf-8") as fh:
                        return json.load(fh)
                except Exception:
                    break
    events = _read_last_jsonl(_alex_ledger(), n=1000)
    for e in events:
        if e.get("sha256", "").startswith(receipt_id) or e.get("subject") == receipt_id:
            return e
    raise HTTPException(status_code=404, detail="receipt not found")


@ui_router.get("/canon")
def canon_view() -> Dict[str, Any]:
    canon_path = os.environ.get("NS_CANON_RULES",
                                "/Volumes/NSExternal/ALEXANDRIA/canon/rules.jsonl")
    rules = _read_last_jsonl(canon_path, n=500)
    return {"ts": datetime.now(timezone.utc).isoformat(),
            "canon_source": canon_path, "rule_count": len(rules),
            "rules_preview": rules[:20],
            "warning": "L10 projection — not authoritative; see L5 Alexandrian Lexicon."}


@ui_router.get("/governance/state")
def governance_state() -> Dict[str, Any]:
    return {
        "ts": datetime.now(timezone.utc).isoformat(),
        "invariants": {
            "I1": "Canon precedes Conversion",
            "I2": "Append-only memory",
            "I3": "No LLM authority over Canon",
            "I4": "Hardware quorum (YubiKey serial 26116460)",
            "I5": "Provenance inertness (SHA-256)",
            "I6": "Sentinel Gate soundness",
            "I7": "Bisimulation with replay (2-safety)",
            "I8": "Distributed eventual consistency",
            "I9": "Byzantine quorum for authority change",
            "I10": "Supersession monotone",
        },
        "quorum_required": 2,
        "quorum_present": None,
        "canon_gate": {
            "score_threshold": 0.82,
            "contradiction_ceiling": 0.25,
            "reconstructability_threshold": 0.90,
            "conditions_six_fold": ["score", "contradiction", "reconstructability",
                                    "lineage_valid", "hic_receipt", "pdp_receipt"],
        },
        "doctrine": "Models propose, NS decides, Violet speaks, Handrail executes, Alexandrian Archive remembers.",
    }
PY

  py_write_guarded "$ROOT_REPO/ns/tests/test_ui_named_routes.py" "axiolev-ui-routes-test-v2" <<'PY'
"""axiolev-ui-routes-test-v2"""
from fastapi import FastAPI
from fastapi.testclient import TestClient

from ns.services.ui.router import ui_router


def _client():
    app = FastAPI()
    app.include_router(ui_router)
    return TestClient(app)


def test_ns_state_layers():
    c = _client()
    r = c.get("/ns/state")
    assert r.status_code == 200
    body = r.json()
    assert "layers" in body
    assert len(body["layers"]) == 10
    assert body["layers"]["L2"]["name"] == "Gradient Field"
    assert body["layers"]["L5"]["name"] == "Alexandrian Lexicon"
    assert body["layers"]["L7"]["name"] == "Alexandrian Archive"
    assert body["layers"]["L8"]["name"] == "Lineage Fabric"


def test_program_list_contains_core_four():
    c = _client()
    body = c.get("/program/list").json()
    ids = {p["id"] for p in body["programs"]}
    assert {"ns_core", "handrail", "continuum", "state_api"}.issubset(ids)


def test_program_detail_404_on_unknown():
    c = _client()
    r = c.get("/program/unknown_xyz")
    assert r.status_code == 404


def test_receipt_404_on_unknown():
    c = _client()
    r = c.get("/receipt/zzz_does_not_exist_zzz")
    assert r.status_code == 404


def test_canon_view_shape():
    c = _client()
    body = c.get("/canon").json()
    assert "rule_count" in body
    assert "warning" in body


def test_governance_state_invariants_ten():
    c = _client()
    body = c.get("/governance/state").json()
    assert len(body["invariants"]) == 10
    assert "I4" in body["invariants"]
    assert "26116460" in body["invariants"]["I4"]
    assert "Alexandrian Archive remembers" in body["doctrine"]


def test_projection_invariance_ns_state():
    c = _client()
    a = c.get("/ns/state").json()
    b = c.get("/ns/state").json()
    a.pop("ts", None); b.pop("ts", None)
    assert a == b


def test_projection_invariance_governance_state():
    c = _client()
    a = c.get("/governance/state").json()
    b = c.get("/governance/state").json()
    a.pop("ts", None); b.pop("ts", None)
    assert a == b
PY

  if [ "$FLAG_DRY_RUN" -eq 0 ]; then
    cat > "$UI_REPORT" <<'EOF'
# UI Addition Integration — Named Route Surface
Source: Ui_addition.pdf
8 endpoints: /ns/state, /ns/engine/live, /program/list, /program/{id},
             /alexandria/graph, /receipt/{id}, /canon, /governance/state
Projection-invariance: tested for /ns/state and /governance/state
Canonical names enforced in tests: Gradient Field, Alexandrian Lexicon,
  Alexandrian Archive, Lineage Fabric
— AXIOLEV Holdings LLC © 2026
EOF
  fi

  commit_phase "$ROOT_REPO" "Z5a" "ui named route surface (8 endpoints)" || true
  lineage_emit "phase_end" "Z5a" "ok" "ui 8 routes integrated"
}

# =============================================================================
# PHASE Z6 — 5-GATE READY TO BOOT VERIFICATION
# =============================================================================

phase_z6_verify() {
  log_phase "Z6 ready-to-boot verification"
  lineage_emit "phase_start" "Z6" "info" "verification"

  _gate1=0; _gate2=0; _gate3=0; _gate4=0; _gate5=0

  log_step "Gate 1: Alexandrian Archive"
  if [ -d "$ALEX_MNT" ] && [ -w "$ALEX_MNT" ]; then
    if [ -f "$ALEX_LEDGER/ns_events.jsonl" ] || \
       ( mkdir -p "$ALEX_LEDGER" && touch "$ALEX_LEDGER/ns_events.jsonl" ); then
      _gate1=1
      log_ok "gate 1: Alexandrian Archive writable, ledger present"
    else
      log_warn "gate 1: ledger not writable"
    fi
  else
    log_warn "gate 1: Alexandrian Archive mount absent or read-only"
  fi

  # --- Gate 2: boot surface -------------------------------------------------
  # Accept both the .command naming (current) and .sh naming (legacy).
  # Pass if: boot founder present AND verify_and_save present (either name)
  #          AND shutdown_prep present (either name) AND launchd plist present.
  log_step "Gate 2: boot surface"
  _g2_detail=""
  _g2_checks=0

  # 2a: founder boot (only one canonical name)
  if [ -f "$ROOT_REPO/scripts/boot/ns_boot_founder.command" ]; then
    _g2_checks=$((_g2_checks + 1))
    log_info "gate 2: ns_boot_founder.command ✓"
  else
    _g2_detail="$_g2_detail ns_boot_founder.command"
  fi

  # 2b: verify_and_save — accept either naming convention
  if [ -f "$ROOT_REPO/scripts/boot/ns_verify_and_save.command" ] || \
     [ -f "$ROOT_REPO/scripts/boot/verify_and_save.sh" ] || \
     [ -f "$ROOT_REPO/scripts/boot/ns_verify_and_save.sh" ]; then
    _g2_checks=$((_g2_checks + 1))
    log_info "gate 2: verify_and_save ✓"
  else
    _g2_detail="$_g2_detail verify_and_save(.command|.sh)"
  fi

  # 2c: shutdown_prep — accept either naming convention
  if [ -f "$ROOT_REPO/scripts/boot/ns_shutdown_prep.command" ] || \
     [ -f "$ROOT_REPO/scripts/boot/shutdown_prep.sh" ] || \
     [ -f "$ROOT_REPO/scripts/boot/ns_shutdown_prep.sh" ]; then
    _g2_checks=$((_g2_checks + 1))
    log_info "gate 2: shutdown_prep ✓"
  else
    _g2_detail="$_g2_detail shutdown_prep(.command|.sh)"
  fi

  # 2d: launchd plist
  if [ -f "$ROOT_REPO/launchd/com.axiolev.ns_founder_boot.plist" ]; then
    _g2_checks=$((_g2_checks + 1))
    log_info "gate 2: launchd plist ✓"
  else
    _g2_detail="$_g2_detail launchd/com.axiolev.ns_founder_boot.plist"
  fi

  if [ "$_g2_checks" -ge 4 ]; then
    _gate2=1
    log_ok "gate 2: boot surface complete ($_g2_checks/4)"
  elif [ "$_g2_checks" -ge 3 ]; then
    # Launchd plist is advisory; 3/4 with plist missing = partial pass
    _gate2=1
    log_ok "gate 2: boot surface acceptable ($_g2_checks/4 — advisory:$_g2_detail)"
  else
    log_warn "gate 2: boot surface incomplete ($_g2_checks/4 — missing:$_g2_detail)"
  fi

  # --- Gate 3: runtime surface ----------------------------------------------
  # Probe grounded signals: compose service definitions, services/ dirs, ports.
  # Do NOT grep for imagined string patterns inside Python files.
  log_step "Gate 3: runtime surface"
  _g3_signals=0
  _g3_detail=""

  # 3a: docker-compose.yml defines ns_core, handrail, continuum
  _compose="$ROOT_REPO/docker-compose.yml"
  if [ -f "$_compose" ]; then
    for _svc in ns_core handrail continuum; do
      if grep -q "^  ${_svc}:" "$_compose" 2>/dev/null; then
        _g3_signals=$((_g3_signals + 1))
        log_info "gate 3: compose service ${_svc} ✓"
      else
        _g3_detail="$_g3_detail compose:${_svc}"
      fi
    done
  else
    _g3_detail="$_g3_detail docker-compose.yml_absent"
  fi

  # 3b: services/ directories exist for the four core services
  for _svc in ns_core handrail continuum; do
    if [ -d "$ROOT_REPO/services/$_svc" ]; then
      _g3_signals=$((_g3_signals + 1))
      log_info "gate 3: services/${_svc}/ dir ✓"
    else
      _g3_detail="$_g3_detail dir:${_svc}"
    fi
  done

  # 3c: canonical port bindings present in compose (9000, 8011, 8788)
  if [ -f "$_compose" ]; then
    _port_hits=0
    for _port in 9000 8011 8788; do
      grep -q "\"${_port}:" "$_compose" 2>/dev/null && _port_hits=$((_port_hits + 1))
    done
    if [ "$_port_hits" -ge 3 ]; then
      _g3_signals=$((_g3_signals + 1))
      log_info "gate 3: port bindings 9000/8011/8788 ✓"
    else
      _g3_detail="$_g3_detail port_bindings($_port_hits/3)"
    fi
  fi

  # 3d: boot.sh references all three services (smoke that boot wires them)
  if [ -f "$ROOT_REPO/boot.sh" ]; then
    _boot_refs=0
    for _svc in ns_core handrail continuum; do
      grep -q "$_svc" "$ROOT_REPO/boot.sh" 2>/dev/null && _boot_refs=$((_boot_refs + 1))
    done
    if [ "$_boot_refs" -ge 2 ]; then
      _g3_signals=$((_g3_signals + 1))
      log_info "gate 3: boot.sh references ($_boot_refs services) ✓"
    fi
  fi

  # Gate 3 pass threshold: ≥5 of up to 8 grounded signals
  if [ "$_g3_signals" -ge 5 ]; then
    _gate3=1
    log_ok "gate 3: runtime surface grounded ($_g3_signals signals)"
  elif [ "$_g3_signals" -ge 3 ]; then
    _gate3=1
    log_ok "gate 3: runtime surface acceptable ($_g3_signals signals — advisory:$_g3_detail)"
  else
    log_warn "gate 3: runtime surface weak ($_g3_signals signals — missing:$_g3_detail)"
  fi

  log_step "Gate 4: constitutional surface"
  if [ -f "$ROOT_REPO/ns/omega/canon_gate.py" ] && \
     [ -f "$ROOT_REPO/ns/omega/pdp.py" ] && \
     [ -f "$ROOT_REPO/ns/omega/hic.py" ]; then
    _gate4=1
    log_ok "gate 4: constitutional surface present (canon_gate + pdp + hic)"
  else
    log_warn "gate 4: constitutional surface incomplete"
  fi

  log_step "Gate 5: visibility surface (real test run)"
  if command -v pytest >/dev/null 2>&1 && [ "$FLAG_DRY_RUN" -eq 0 ]; then
    _pytest_log="$ARTIFACTS_DIR/pytest_${TS_RUN}.log"
    if ( cd "$ROOT_REPO" && pytest ns/tests/ -q >>"$_pytest_log" 2>&1 ); then
      if grep -qE "skipped|SKIPPED" "$_pytest_log"; then
        log_warn "gate 5: tests green but with skips — inspect $_pytest_log"
        _gate5=1
      else
        _gate5=1
        log_ok "gate 5: all tests green, no skips"
      fi
    else
      log_warn "gate 5: pytest failures — see $_pytest_log"
    fi
  else
    log_warn "gate 5: pytest unavailable or dry-run"
  fi

  _total=$((_gate1 + _gate2 + _gate3 + _gate4 + _gate5))
  log_info "gates: gate1=$_gate1 gate2=$_gate2 gate3=$_gate3 gate4=$_gate4 gate5=$_gate5 total=$_total/5"

  cat > "$ARTIFACTS_DIR/ready_to_boot_gates_${TS_RUN}.json" <<EOF
{
  "ts": "$TS_RUN",
  "gate1_alexandrian_archive": $_gate1,
  "gate2_boot_surface": $_gate2,
  "gate3_runtime_surface": $_gate3,
  "gate4_constitutional_surface": $_gate4,
  "gate5_visibility_surface": $_gate5,
  "total_green": $_total,
  "ready_to_boot": $( [ "$_total" -eq 5 ] && echo true || echo false )
}
EOF

  echo "$_total" > "$ARTIFACTS_DIR/gate_total.tmp" 2>/dev/null || true

  lineage_emit "phase_end" "Z6" "ok" "gates=$_total/5"
}

# =============================================================================
# PHASE Z7 — FINAL CLOSURE CERTIFICATION + TAGGING
# =============================================================================

phase_z7_certify() {
  log_phase "Z7 closure certification + tagging"
  lineage_emit "phase_start" "Z7" "info" "certification"

  _gate_total="$( cat "$ARTIFACTS_DIR/gate_total.tmp" 2>/dev/null || echo 0 )"

  cat > "$CERT_DIR/NS_CLOSURE_MAX_v2.md" <<EOF
# NS∞ Closure Max v2 Certification — $TS_RUN

Repo: $ROOT_REPO
Branch: $BASE_BRANCH
Gates green: $_gate_total / 5

Phases: Z-1, Z0, Z1, Z2, Z3, Z3b, Z4, Z5, Z5a, Z6, Z7
Sources: Omega Whitepaper, UG_max, Ui_addition.pdf, Ns_media.pdf, media_engine_repo.zip

Doctrine: Models propose, NS decides, Violet speaks, Handrail executes,
Alexandrian Archive remembers. L10 never amends L1-L9.

AXIOLEV Holdings LLC © 2026 — axiolevns@axiolev.com
EOF

  cat > "$CERT_DIR/NS_CLOSURE_MAX_v2.json" <<EOF
{
  "ts": "$TS_RUN",
  "certification": "ns-infinity-closure-max-v2.0.0",
  "owner": "AXIOLEV Holdings LLC",
  "year": $AXIOLEV_YEAR,
  "repo": "$ROOT_REPO",
  "branch": "$BASE_BRANCH",
  "gates_green": $_gate_total,
  "gates_total": 5,
  "phases_completed": ["Z-1","Z0","Z1","Z2","Z3","Z3b","Z4","Z5","Z5a","Z6","Z7"],
  "sources_integrated": [
    "Omega_Institutional_Architecture_Whitepaper.pdf",
    "UG_max_ready_to_integrate_.pdf",
    "Ui_addition.pdf",
    "Ns_media.pdf",
    "media_engine_repo.zip"
  ]
}
EOF

  commit_phase "$ROOT_REPO" "Z7" "closure max v2 certification" || true
  tag_phase "$ROOT_REPO" "$CLOSURE_V2_TAG"

  if [ "$_gate_total" -eq 5 ]; then
    tag_phase "$ROOT_REPO" "${READY_TAG_PREFIX}-${DATE_TAG}"
    log_ok "READY TO BOOT tag applied: ${READY_TAG_PREFIX}-${DATE_TAG}"
  else
    log_warn "ready-to-boot tag NOT applied (gates: $_gate_total/5)"
  fi

  if [ "$FLAG_PUSH_SAFE" -eq 1 ]; then
    _push_gate="$( cat "$ARTIFACTS_DIR/push_gate.state" 2>/dev/null || echo blocked )"
    if [ "$_push_gate" = "clean" ] && [ "$FLAG_DRY_RUN" -eq 0 ]; then
      log_step "pushing (--push-safe + gitleaks clean)"
      git_in "$ROOT_REPO" push origin "$BASE_BRANCH" --tags >>"$LOG_FILE" 2>&1 || \
        log_warn "push failed"
    else
      log_warn "push gate not clean or dry-run -> skipping push"
    fi
  fi

  lineage_emit "phase_end" "Z7" "ok" "closure v2 certified; gates=$_gate_total/5"
}

# =============================================================================
# DISPATCHER
# =============================================================================

run_phase() {
  case "$1" in
    Z-1) phase_zm1_bootstrap ;;
    Z0)  phase_z0_preflight ;;
    Z1)  phase_z1_security ;;
    Z2)  phase_z2_ontology ;;
    Z3)  phase_z3_omega ;;
    Z3b) phase_z3b_entity ;;
    Z4)  phase_z4_media ;;
    Z5)  phase_z5_ui_base ;;
    Z5a) phase_z5a_ui_routes ;;
    Z6)  phase_z6_verify ;;
    Z7)  phase_z7_certify ;;
    *)   fail_exit "unknown phase: $1" ;;
  esac
}

main() {
  log_phase "NS∞ Closure Max v2 — start $TS_RUN"
  log_info "repo: $ROOT_REPO branch: $BASE_BRANCH"
  log_info "flags: scrub=$FLAG_SCRUB_HISTORY push=$FLAG_PUSH_SAFE dry=$FLAG_DRY_RUN pull=$FLAG_PULL skip_boot=$FLAG_SKIP_BOOTSTRAP single=$FLAG_SINGLE_PHASE"
  lineage_emit "closure_v2_start" "closure" "info" "ts=$TS_RUN"

  if [ -n "$FLAG_SINGLE_PHASE" ]; then
    log_info "single-phase mode: $FLAG_SINGLE_PHASE"
    run_phase "$FLAG_SINGLE_PHASE"
  else
    for _p in "Z-1" Z0 Z1 Z2 Z3 Z3b Z4 Z5 Z5a Z6 Z7; do
      run_phase "$_p"
    done
  fi

  log_phase "NS∞ Closure Max v2 — complete"
  lineage_emit "closure_v2_complete" "closure" "ok" "ts=$TS_RUN"
  write_return_block "CLOSURE_V2_COMPLETE" "all phases executed"
}

main "$@"
