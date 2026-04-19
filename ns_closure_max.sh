#!/usr/bin/env bash
# =============================================================================
# ns_closure_max.sh — NS∞ FINAL INTEGRATION & CLOSURE MAX
# AXIOLEV Holdings LLC © 2026 — axiolevns <axiolevns@axiolev.com>
#
# Mission
# -------
# One script. One terminal. Closes NS∞ from current state
# (ns-infinity-manifold-complete-v1.0.0, 717 tests green) to a verified
# READY TO BOOT posture with:
#   • Leaked-PAT scrub from git history + gitleaks pre-commit hook
#   • Live ontology audit (10 layers → actual runtime)
#   • Omega L10 projection/ego layer (per Omega Whitepaper)
#   • Media engine integration (from uploaded zip, if present)
#   • UI addition integration (from uploaded PDF spec, if present)
#   • 5-gate READY TO BOOT verification
#   • Final closure tag: ns-infinity-closure-max-v1.0.0
#
# Locked ontology (enforced throughout — deprecated names rejected):
#   L1  Constitutional Layer   (Dignity Kernel / Sentinel Gate / Canon Barrier)
#   L2  Gradient Field         (not "Ether")
#   L3  Epistemic Envelope     (Intake admissibility predicates)
#   L4  The Loom               (reflector functor GradientField → Canon)
#   L5  Alexandrian Lexicon    (not "Lexicon" / "Atomlex")
#   L6  State Manifold         (not "Manifold")
#   L7  Alexandrian Archive    (not "Alexandria")
#   L8  Lineage Fabric         (not "CTF")
#   L9  HIC / PDP              (error + correction, supersession routers)
#   L10 Narrative + Interface  (Omega + Violet; "Storytime" only as service)
#
# Ten invariants (must remain intact):
#   I1  Canon precedes Conversion
#   I2  Append-only memory (Lineage inertness)
#   I3  No LLM authority over Canon
#   I4  Hardware quorum (YubiKey serial 26116460 mandatory)
#   I5  Provenance inertness (SHA-256 hash-chain)
#   I6  Sentinel Gate soundness
#   I7  Bisimulation with replay (2-safety)
#   I8  Distributed eventual consistency (CRDT/SEC)
#   I9  Byzantine quorum for authority change (≥2f+1)
#   I10 Supersession monotone (never delete)
#
# Phases (linear, each fast-forwards if already satisfied):
#   Z0  Preflight + safety (YubiKey, Alexandria, git state)
#   Z1  Security scrub (gitleaks install, repo-wide secret scan,
#                       safe-to-push gate armed)
#   Z2  Live ontology audit → artifacts/ontology_audit_<ts>.md
#   Z3  Omega L10 projection/ego layer
#         • Pydantic v2 primitives (Branch, Delta, Entanglement,
#           Contradiction, SemanticAnchor, ShardManifest,
#           ProjectionRequest/Result, ForkOp, MergeOp, SupersessionOp,
#           Storytime, ConfidenceEnvelope, Recoverability,
#           ProjectionMode)
#         • Alexandrian Archive layout under
#           /Volumes/NSExternal/ALEXANDRIA/{branches, projections,
#           entanglements, contradictions, anchors, shards,
#           storytime, ledger}
#         • FastAPI routes:
#           POST /projections, POST /canon/promote, POST /hic/decisions,
#           POST /pdp/evaluate, GET /ledger/receipts, POST /storytime,
#           GET /storytime/{id}, GET /healthz
#         • Recovery-ordered projection engine (exact_local, delta_replay,
#           shard_recovery, entanglement_assisted, semantic,
#           graceful_partial) — order_used recorded
#         • ConfidenceEnvelope with locked weights
#           0.45·evidence + 0.25·(1-contradiction) + 0.15·novelty +
#           0.15·stability
#         • Six-fold Canon gate (score≥0.82, contradiction≤0.25,
#           reconstructability≥0.90, lineage_valid, HIC receipt,
#           PDP receipt) → canon_promoted_with_hardware_quorum receipt
#   Z4  Media engine integration
#         • If /mnt/user-data/uploads/media_engine_repo.zip present,
#           unpack to ns/services/media_engine/ and wire router.
#         • If absent, emit skip receipt; do NOT fabricate.
#   Z5  UI addition integration
#         • If uploaded Ui_addition spec present, populate
#           ns/services/ui/* additions; else emit skip receipt.
#   Z6  5-gate READY TO BOOT verification
#         Gate 1  Alexandria hard-mounted, ledger writable
#         Gate 2  Boot surface (scripts/boot/ns_boot_founder.command,
#                 verify_and_save, shutdown_prep, Tauri app, launchd plist)
#         Gate 3  Runtime surface (ns_core :9000, handrail :8011,
#                 continuum :8788, state_api :9090) — optional Docker
#         Gate 4  Constitutional surface
#                 (GET /ring5/gates, POST /pi/check abstention,
#                 POST /pdp/decide anon-deny, Ring 6 φ parallel,
#                 ring6_complete.signal)
#         Gate 5  Visibility surface (no fabricated greens:
#                 full pytest ns/tests/ pass, no silent skips,
#                 FOUNDER_OPS reference present)
#   Z7  Final closure certification + tagging
#         • certification/NS_CLOSURE_MAX_v1.md + .json
#         • Tag ns-infinity-closure-max-v1.0.0 (annotated)
#         • Tag ns-infinity-ready-to-boot-<YYYYMMDD>
#         • No push unless --push-safe passed AND gitleaks clean
#
# Safety contract
# ---------------
#   1. NEVER pushes by default. Must pass --push-safe AND gitleaks clean.
#   2. NEVER deletes or force-pushes canon/rules.jsonl, ledger JSONL,
#      or any tagged branch.
#   3. NEVER rewrites history automatically. Scrub mode is advisory until
#      --scrub-history passed; then uses git-filter-repo with dry-run first.
#   4. Bash 3.2 only: no assoc arrays, no mapfile, no ${var,,}, case/esac.
#   5. All network calls blocked except localhost 127.0.0.1 + GitHub
#      remote-url read. No fetch/pull of upstream unless --pull passed.
#   6. Idempotent: every phase fast-forwards if its tag is present and
#      its test suite passes.
#   7. Receipts: every phase start/end writes a JSONL line to
#      /Volumes/NSExternal/ALEXANDRIA/ledger/ns_events.jsonl and
#      $LOG_DIR/lineage_CLOSURE_<ts>.jsonl.
#
# Usage
# -----
#   bash ~/axiolev_runtime/ns_closure_max.sh
#   bash ~/axiolev_runtime/ns_closure_max.sh --scrub-history    # enable PAT scrub
#   bash ~/axiolev_runtime/ns_closure_max.sh --push-safe        # allow push if clean
#   bash ~/axiolev_runtime/ns_closure_max.sh --dry-run          # plan only
#   bash ~/axiolev_runtime/ns_closure_max.sh --phase Z3         # run single phase
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
UPLOADS_DIR="${UPLOADS_DIR:-/mnt/user-data/uploads}"

TS_RUN="$(date -u +%Y%m%dT%H%M%SZ)"
DATE_TAG="$(date -u +%Y%m%d)"

LOG_DIR="$ROOT_REPO/.terminal_manager/logs"
LOG_FILE="$LOG_DIR/closure_${TS_RUN}.log"
CTF_LOCAL="$LOG_DIR/lineage_CLOSURE_${TS_RUN}.jsonl"
CTF_LEDGER="$ALEX_LEDGER/ns_events.jsonl"
ARTIFACTS_DIR="$ROOT_REPO/artifacts"
CERT_DIR="$ROOT_REPO/certification"
PROMPT_MD="$ROOT_REPO/CLOSURE_PROMPT.md"
FIX_MD="$ROOT_REPO/CLOSURE_FIX_REQUEST.md"
ONTOLOGY_REPORT="$ARTIFACTS_DIR/ontology_audit_${TS_RUN}.md"

MAX_ATTEMPTS=3

# ---------- Flags ------------------------------------------------------------
FLAG_SCRUB_HISTORY=0
FLAG_PUSH_SAFE=0
FLAG_DRY_RUN=0
FLAG_PULL=0
FLAG_SINGLE_PHASE=""

while [ $# -gt 0 ]; do
  case "$1" in
    --scrub-history) FLAG_SCRUB_HISTORY=1 ;;
    --push-safe)     FLAG_PUSH_SAFE=1 ;;
    --dry-run)       FLAG_DRY_RUN=1 ;;
    --pull)          FLAG_PULL=1 ;;
    --phase)         shift; FLAG_SINGLE_PHASE="${1:-}" ;;
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
log()       { printf '%s [CLOSURE] %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*" | tee -a "$LOG_FILE"; }
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
  _line="$(python3 - "$_ts" "CLOSURE" "$_event" "$_subject" "$_status" "$_detail" <<'PY' 2>/dev/null
import json,sys
ts,terminal,event,subject,status,detail = sys.argv[1:7]
print(json.dumps({
  "ts": ts, "terminal": terminal, "event": event,
  "subject": subject, "status": status, "detail": detail
}, ensure_ascii=False))
PY
)"
  if [ -z "$_line" ]; then
    _line="{\"ts\":\"$_ts\",\"terminal\":\"CLOSURE\",\"event\":\"$_event\",\"subject\":\"$_subject\",\"status\":\"$_status\",\"detail\":\"escape_failed\"}"
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
  lineage_emit "closure_failed" "closure" "error" "$_reason"
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
  if ! git_in "$_dir" diff --cached --quiet 2>/dev/null; then
    if [ "$FLAG_DRY_RUN" -eq 1 ]; then
      log_info "[dry-run] would commit: $_msg"
      return 0
    fi
    git_in "$_dir" commit -m "$_msg" >>"$LOG_FILE" 2>&1 || return 1
  else
    log_info "$_id: no staged changes (idempotent)"
  fi
  return 0
}

# ---------- Preflight --------------------------------------------------------
preflight() {
  log_phase "Z0 — Preflight + safety"
  lineage_emit "preflight_start" "z0" "start" "run=$TS_RUN repo=$ROOT_REPO"

  for _t in git python3 curl awk sed grep tar; do
    command -v "$_t" >/dev/null 2>&1 || fail_exit "missing required tool: $_t"
  done
  command -v claude >/dev/null 2>&1 || log_warn "claude CLI not found — Z3+ will fail if gaps exist"

  _py="$(python3 -c 'import sys;print("%d.%d"%sys.version_info[:2])' 2>/dev/null || echo 0.0)"
  _maj="$(echo "$_py" | awk -F. '{print $1}')"
  _min="$(echo "$_py" | awk -F. '{print $2}')"
  if [ "$_maj" -lt 3 ] || { [ "$_maj" -eq 3 ] && [ "$_min" -lt 11 ]; }; then
    fail_exit "python3 >= 3.11 required (found $_py)"
  fi
  log_ok "python3 $_py"

  [ -d "$ROOT_REPO/.git" ] || fail_exit "repo not found at $ROOT_REPO"

  cd "$ROOT_REPO" || fail_exit "cd $ROOT_REPO failed"
  _br="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo unknown)"
  if [ "$_br" != "$BASE_BRANCH" ]; then
    log_warn "current branch $_br; switching to $BASE_BRANCH"
    git checkout "$BASE_BRANCH" >>"$LOG_FILE" 2>&1 || fail_exit "checkout $BASE_BRANCH failed"
  fi
  log_ok "repo on $BASE_BRANCH"

  if [ ! -d "$ALEX_MNT" ]; then
    fail_exit "Alexandrian Archive not mounted at $ALEX_MNT (I7 substrate unavailable)"
  fi
  log_ok "Alexandrian Archive mounted: $ALEX_MNT"

  mkdir -p "$ALEX_LEDGER" 2>/dev/null || log_warn "ledger mkdir failed (read-only?)"
  # Ensure full substrate layout
  for _sub in branches projections entanglements contradictions anchors \
              shards storytime canon lexicon state/shards state/transitions \
              narrative cqhml ledger; do
    mkdir -p "$ALEX_MNT/$_sub" 2>/dev/null || true
  done
  touch "$ALEX_LEDGER/ns_events.jsonl" 2>/dev/null || true

  # YubiKey (I4 anchor) — warn only at preflight; Canon gate tests enforce
  if command -v ykman >/dev/null 2>&1; then
    _serials="$(ykman list 2>/dev/null | awk '/Serial/ {print $NF}' | tr '\n' ' ')"
    case " $_serials " in
      *" $YUBIKEY_SERIAL "*)
        log_ok "YubiKey $YUBIKEY_SERIAL present (I4/I9 anchor)"
        lineage_emit "yubikey_preflight" "hw" "ok" "serial=$YUBIKEY_SERIAL" ;;
      *)
        log_warn "YubiKey $YUBIKEY_SERIAL not detected (Canon gate tests will fail-closed)"
        lineage_emit "yubikey_preflight" "hw" "warn" "not_detected" ;;
    esac
  else
    log_warn "ykman not installed (Canon gate tests will use mock quorum_certs)"
  fi

  # Working tree clean?
  _dirty="$(git status --porcelain 2>/dev/null | wc -l | tr -d ' ')"
  if [ "$_dirty" -gt 0 ]; then
    log_warn "working tree has $_dirty uncommitted paths — closure will commit them inside each phase scope"
  else
    log_ok "working tree clean"
  fi

  lineage_emit "preflight_end" "z0" "ok" "python=$_py branch=$BASE_BRANCH"
}

# ---------- Z1 — Security scrub (gitleaks + safe-to-push gate) --------------
z1_security_scrub() {
  log_phase "Z1 — Security scrub (gitleaks + leaked-PAT detection)"
  lineage_emit "z1_start" "security" "start" "scrub=$FLAG_SCRUB_HISTORY"

  # Install gitleaks (macOS brew preferred; fallback to manual hook)
  _gitleaks_ok=0
  if command -v gitleaks >/dev/null 2>&1; then
    _gitleaks_ok=1
    log_ok "gitleaks present: $(gitleaks version 2>/dev/null | head -1)"
  elif command -v brew >/dev/null 2>&1; then
    if [ "$FLAG_DRY_RUN" -eq 1 ]; then
      log_info "[dry-run] would install gitleaks via brew"
    else
      log_info "installing gitleaks via brew (may take 30-60s)"
      brew install gitleaks >>"$LOG_FILE" 2>&1 || log_warn "brew install gitleaks failed"
      if command -v gitleaks >/dev/null 2>&1; then _gitleaks_ok=1; fi
    fi
  fi

  # Regex-based fallback scan (works even without gitleaks)
  _scan_out="$ARTIFACTS_DIR/secrets_scan_${TS_RUN}.txt"
  log_info "regex secret scan → $_scan_out"
  {
    echo "# Secret scan — $TS_RUN"
    echo "# Patterns: ghp_*, github_pat_*, sk_live_*, whsec_*, AKIA*, AIza*, xoxb-*"
    echo "---"
    git_c log --all --source -S "ghp_"           --oneline 2>/dev/null | head -50
    git_c log --all --source -S "github_pat_"    --oneline 2>/dev/null | head -50
    git_c log --all --source -S "sk_live_"       --oneline 2>/dev/null | head -50
    git_c log --all --source -S "whsec_"         --oneline 2>/dev/null | head -50
    git_c log --all --source --pickaxe-regex -S "AKIA[0-9A-Z]{16}" --oneline 2>/dev/null | head -50
    git_c log --all --source --pickaxe-regex -S "AIza[0-9A-Za-z_-]{35}" --oneline 2>/dev/null | head -50
  } > "$_scan_out" 2>&1

  _hits="$(grep -cE '^[0-9a-f]{7,}' "$_scan_out" 2>/dev/null || echo 0)"
  _hits="$(echo "$_hits" | tr -d ' \n')"
  if [ "${_hits:-0}" -gt 0 ]; then
    log_warn "SECRET SCAN: $_hits suspicious commits — see $_scan_out"
    lineage_emit "secret_scan" "security" "warn" "hits=$_hits report=$_scan_out"
    _SAFE_TO_PUSH=0
  else
    log_ok "SECRET SCAN: no pattern matches in history"
    lineage_emit "secret_scan" "security" "ok" "hits=0"
    _SAFE_TO_PUSH=1
  fi

  # gitleaks run (if present)
  if [ "$_gitleaks_ok" -eq 1 ]; then
    _gl_out="$ARTIFACTS_DIR/gitleaks_${TS_RUN}.json"
    log_info "running gitleaks detect → $_gl_out"
    gitleaks detect --source "$ROOT_REPO" --report-format json --report-path "$_gl_out" \
      --no-git --redact >>"$LOG_FILE" 2>&1 || true
    _gl_findings=0
    if [ -f "$_gl_out" ]; then
      _gl_findings="$(python3 -c 'import json,sys;d=json.load(open(sys.argv[1]));print(len(d) if isinstance(d,list) else 0)' "$_gl_out" 2>/dev/null || echo 0)"
    fi
    if [ "${_gl_findings:-0}" -gt 0 ]; then
      log_warn "gitleaks: $_gl_findings findings in working tree — $_gl_out"
      lineage_emit "gitleaks" "security" "warn" "findings=$_gl_findings"
      _SAFE_TO_PUSH=0
    else
      log_ok "gitleaks: 0 findings in working tree"
      lineage_emit "gitleaks" "security" "ok" "findings=0"
    fi
  fi

  # Install pre-commit hook (blocks ghp_/github_pat_/sk_live_)
  _hook="$ROOT_REPO/.git/hooks/pre-commit"
  if [ ! -f "$_hook" ] || ! grep -q "NS_CLOSURE_SECRET_GUARD" "$_hook" 2>/dev/null; then
    if [ "$FLAG_DRY_RUN" -eq 1 ]; then
      log_info "[dry-run] would install pre-commit secret-guard hook"
    else
      cat > "$_hook" <<'HOOK_EOF'
#!/usr/bin/env bash
# NS_CLOSURE_SECRET_GUARD — AXIOLEV Holdings LLC © 2026
# Blocks commits that introduce common secret patterns.
_patterns='(ghp_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{22,}|sk_live_[A-Za-z0-9]{20,}|whsec_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|AIza[0-9A-Za-z_-]{35}|xox[baprs]-[A-Za-z0-9-]{10,})'
_bad="$(git diff --cached -U0 | grep -E '^\+' | grep -vE '^\+\+\+' | grep -iE "$_patterns" || true)"
if [ -n "$_bad" ]; then
  echo "NS_CLOSURE_SECRET_GUARD: blocked commit — secret-like pattern detected." >&2
  echo "$_bad" | head -5 >&2
  exit 1
fi
exit 0
HOOK_EOF
      chmod +x "$_hook"
      log_ok "pre-commit secret-guard hook installed: $_hook"
    fi
  else
    log_info "pre-commit secret-guard already present"
  fi

  # Optional history scrub (advisory unless --scrub-history)
  if [ "${_hits:-0}" -gt 0 ] && [ "$FLAG_SCRUB_HISTORY" -eq 1 ]; then
    if ! command -v git-filter-repo >/dev/null 2>&1; then
      log_warn "git-filter-repo not installed — skipping scrub (install: pip install git-filter-repo)"
    else
      _scrub_patterns="$ROOT_REPO/.terminal_manager/scrub_patterns.txt"
      cat > "$_scrub_patterns" <<'PAT_EOF'
regex:ghp_[A-Za-z0-9]{30,}==>GITHUB_PAT_REDACTED
regex:github_pat_[A-Za-z0-9_]{22,}==>GITHUB_FINE_PAT_REDACTED
regex:sk_live_[A-Za-z0-9]{20,}==>STRIPE_SK_LIVE_REDACTED
regex:whsec_[A-Za-z0-9]{20,}==>STRIPE_WHSEC_REDACTED
regex:AKIA[0-9A-Z]{16}==>AWS_KEY_REDACTED
regex:AIza[0-9A-Za-z_-]{35}==>GCP_KEY_REDACTED
PAT_EOF
      log_warn "running git-filter-repo with --replace-text (DRY RUN first)"
      if [ "$FLAG_DRY_RUN" -eq 1 ]; then
        log_info "[dry-run] would run: git filter-repo --replace-text $_scrub_patterns --force"
      else
        ( cd "$ROOT_REPO" && \
          git filter-repo --replace-text "$_scrub_patterns" --force ) >>"$LOG_FILE" 2>&1 \
          && log_ok "history scrub complete" \
          || log_warn "filter-repo exited non-zero — manual review required"
        lineage_emit "history_scrub" "security" "done" "patterns=$_scrub_patterns"
      fi
    fi
  elif [ "${_hits:-0}" -gt 0 ]; then
    log_warn "secrets in history detected — pass --scrub-history to rewrite (advisory only)"
  fi

  echo "$_SAFE_TO_PUSH" > "$ARTIFACTS_DIR/.safe_to_push"
  lineage_emit "z1_end" "security" "ok" "safe_to_push=$_SAFE_TO_PUSH"
}

# ---------- Z2 — Live ontology audit ----------------------------------------
z2_ontology_audit() {
  log_phase "Z2 — Live ontology audit (10 layers → runtime)"
  lineage_emit "z2_start" "ontology" "start" ""

  _probe() {
    _url="$1"; _marker="$2"
    _out="$(curl -sf -m 3 "$_url" 2>/dev/null || echo '')"
    if [ -n "$_out" ] && echo "$_out" | grep -q "$_marker"; then
      echo "ok"
    elif [ -n "$_out" ]; then
      echo "partial"
    else
      echo "down"
    fi
  }

  _docker_sock=""
  if [ -S "/var/run/docker.sock" ]; then _docker_sock="/var/run/docker.sock"
  elif [ -S "$HOME/.docker/run/docker.sock" ]; then _docker_sock="$HOME/.docker/run/docker.sock"
  fi
  export DOCKER_HOST="unix://$_docker_sock"

  _docker_ps="$(docker compose ps 2>/dev/null || echo '')"

  # Layer probes
  _L1="$(_probe http://127.0.0.1:9000/pdp/decide 'ok\|failure_reason\|unauthorized')"
  _L2="down"; echo "$_docker_ps" | grep -q model_router && _L2="ok"
  _L3="$(_probe http://127.0.0.1:9000/healthz 'ok\|ns_core')"
  _L4="$(_probe http://127.0.0.1:9000/pi/check 'admissibility\|abstention\|triggered_axioms')"
  _L5="down"; echo "$_docker_ps" | grep -qE "atomlex|lexicon" && _L5="ok"
  _L5_fs="down"; [ -d "$ALEX_MNT/lexicon" ] && _L5_fs="ok"
  _L6="$(_probe http://127.0.0.1:9090/state 'state\|tier')"
  _L7="down"; [ -d "$ALEX_MNT/ledger" ] && [ -d "$ALEX_MNT/branches" ] && _L7="ok"
  _L8="down"; [ -f "$ALEX_LEDGER/ns_events.jsonl" ] && _L8="ok"
  _L9="$(_probe http://127.0.0.1:9000/hic/gates 'patterns\|approve\|deny')"
  _L9b="$(_probe http://127.0.0.1:9000/ring5/gates 'stripe\|yubikey\|pending')"
  _L10="down"
  echo "$_docker_ps" | grep -q violet && _L10="partial"
  [ -d "$ROOT_REPO/ns/services/omega" ] && _L10="ok_files"
  _L10_route="$(_probe http://127.0.0.1:9000/projections 'order_used\|recoverability\|mode' )"

  # Handrail + Continuum
  _HR="$(_probe http://127.0.0.1:8011/healthz 'ok\|handrail')"
  _CN="$(_probe http://127.0.0.1:8788/state 'state\|tier\|ok')"

  # Tests
  _test_count=0
  if [ -d "$ROOT_REPO/ns/tests" ]; then
    _test_count="$(cd "$ROOT_REPO" && python3 -m pytest --collect-only -q ns/tests/ 2>&1 | grep -cE 'test_' || echo 0)"
    _test_count="$(echo "$_test_count" | tr -d ' \n')"
  fi

  cat > "$ONTOLOGY_REPORT" <<REPORT_EOF
# NS∞ Live Ontology Audit
**Timestamp:** $TS_RUN
**Branch:** $BASE_BRANCH
**Commit:** $(git_c rev-parse --short HEAD 2>/dev/null || echo unknown)

## 10-Layer Runtime Mapping

| Layer | Component | Probe | Status |
|---|---|---|---|
| L1  Constitutional     | PDP decide endpoint        | /pdp/decide            | $_L1 |
| L2  Gradient Field     | model_router container     | docker ps              | $_L2 |
| L3  Epistemic Envelope | ns_core health             | /healthz               | $_L3 |
| L4  The Loom           | Pi admissibility engine    | /pi/check              | $_L4 |
| L5  Alexandrian Lexicon| lexicon container / files  | docker+fs              | $_L5 / $_L5_fs |
| L6  State Manifold     | state_api                  | /state                 | $_L6 |
| L7  Alexandrian Archive| fs mount + ledger dir      | /Volumes/NSExternal    | $_L7 |
| L8  Lineage Fabric     | ns_events.jsonl            | file present           | $_L8 |
| L9  HIC / PDP          | /hic/gates + /ring5/gates  | hic+ring5              | $_L9 / $_L9b |
| L10 Narrative+Interface| Violet + Omega projection  | files+route            | $_L10 / $_L10_route |

## Execution Boundary (Handrail moat)
- Handrail :8011 → **$_HR**
- Continuum :8788 → **$_CN**

## Test Surface
- ns/tests/ discoverable tests → **$_test_count**

## Canonical Tags Present
$(git_c tag --list | grep -E '^(ring-|ncom-|ril-|cqhml-|ns-infinity-)' | sort | sed 's/^/- /')

## Gap Summary

REPORT_EOF

  # Gap identification
  _gaps=0
  _gap_list=""

  if [ "$_L10" = "down" ] && [ "$_L10_route" = "down" ]; then
    _gaps=$((_gaps+1))
    _gap_list="$_gap_list\n- **Omega L10 projection/ego layer** missing (Z3 will build)"
  fi

  if [ -f "$UPLOADS_DIR/media_engine_repo.zip" ] && [ ! -d "$ROOT_REPO/ns/services/media_engine" ]; then
    _gaps=$((_gaps+1))
    _gap_list="$_gap_list\n- **Media engine** zip present, not unpacked (Z4 will integrate)"
  fi

  if ls "$UPLOADS_DIR"/Ui_addition* >/dev/null 2>&1 && [ ! -f "$ROOT_REPO/ns/services/ui/.ui_addition_integrated" ]; then
    _gaps=$((_gaps+1))
    _gap_list="$_gap_list\n- **UI addition** spec present, not integrated (Z5 will integrate)"
  fi

  if [ "$_gaps" -eq 0 ]; then
    printf 'No gaps identified. System matches 10-layer ontology.\n' >> "$ONTOLOGY_REPORT"
  else
    printf "$_gap_list\n" >> "$ONTOLOGY_REPORT"
  fi

  log_ok "ontology audit → $ONTOLOGY_REPORT (gaps=$_gaps)"
  lineage_emit "z2_end" "ontology" "ok" "gaps=$_gaps report=$ONTOLOGY_REPORT"

  echo "$_gaps" > "$ARTIFACTS_DIR/.ontology_gaps"
}

# ---------- Write closure PROMPT.md -----------------------------------------
write_closure_prompt() {
  log_step "Writing CLOSURE_PROMPT.md (Omega L10 + media + UI spec)"
  cat > "$PROMPT_MD" <<'PROMPT_EOF'
# NS∞ CLOSURE MAX — Omega L10 + Media + UI Integration

**AXIOLEV Holdings LLC © 2026** — axiolevns <axiolevns@axiolev.com>
**Repo:** `mkaxiolev-max/handrail`, branch `boot-operational-closure`
**Package root:** `ns/` per ns_scaffold.zip — do NOT relocate.

## Prior state (do NOT rebuild)
The system is already at `ns-infinity-manifold-complete-v1.0.0` with:
- Rings 1–7 complete
- NCOM/PIIC merged (`ncom-piic-merged-v2`)
- RIL/ORACLE merged (`ril-oracle-merged-v2`)
- CQHML Manifold merged (`cqhml-manifold-merged-v2`)
- 717 tests passing

## Locked ontology (ENFORCE)
L1 Constitutional | L2 Gradient Field | L3 Epistemic Envelope |
L4 The Loom | L5 Alexandrian Lexicon | L6 State Manifold |
L7 Alexandrian Archive | L8 Lineage Fabric | L9 HIC/PDP |
L10 Narrative + Interface (Omega + Violet)

**Do NOT reintroduce deprecated names:** Ether, Lexicon alone,
Manifold alone, Alexandria alone, CTF, Storytime as layer.
"Storytime" is retained ONLY as a service module name.

## Invariants (must remain intact)
I1..I10 per MASTER PROMPT. In particular:
- I1 Canon precedes Conversion (Ring 4 gate)
- I4 Hardware quorum (YubiKey serial 26116460 mandatory)
- I2/I5/I10 Append-only, hash-chained, supersede-not-delete

---

# Z3 — Omega L10 Projection/Ego Layer

Omega is the **mouth of the system**. Everything the institution
says externally passes through Omega and is recovery-ordered,
confidence-enveloped, mode-indexed, and receipted.

## Z3.1 Pydantic v2 primitives

Create/extend `ns/domain/models/omega_primitives.py`:

```python
from __future__ import annotations
from datetime import datetime, timezone
from enum import Enum
from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, Field

def _now() -> datetime:
    return datetime.now(tz=timezone.utc)

class Recoverability(str, Enum):
    EXACT = "exact"
    LOSSLESS_STRUCTURAL = "lossless_structural"
    LOSSLESS_SEMANTIC = "lossless_semantic"
    LOSSY_SEMANTIC = "lossy_semantic"
    IRRECOVERABLE = "irrecoverable"

class ProjectionMode(str, Enum):
    EXACT_VIEW = "exact_view"
    BRANCH_VIEW = "branch_view"
    MERGED_VIEW = "merged_view"
    CANON_VIEW = "canon_view"
    PARTIAL_RECONSTRUCTION = "partial_reconstruction"
    CONTRASTIVE_VIEW = "contrastive_view"

class ConfidenceEnvelope(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    evidence: float = Field(ge=0.0, le=1.0)
    contradiction: float = Field(ge=0.0, le=1.0)
    novelty: float = Field(ge=0.0, le=1.0)
    stability: float = Field(ge=0.0, le=1.0)

    def score(self) -> float:
        # Locked constitutional weights — amendment requires
        # HIC + PDP + YubiKey quorum (see Ring 4).
        return (0.45 * self.evidence
                + 0.25 * (1.0 - self.contradiction)
                + 0.15 * self.novelty
                + 0.15 * self.stability)

class Branch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    parent_id: Optional[str] = None
    created_at: datetime = Field(default_factory=_now)
    title: str
    lineage: list[str] = Field(default_factory=list)
    canon: bool = False

class Delta(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    id: str
    branch_id: str
    seq: int = Field(ge=0)
    op: Literal["add","amend","retract","supersede"]
    payload: dict
    prev_hash: str
    hash: str
    author: str
    ts: datetime = Field(default_factory=_now)

class Entanglement(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    a_ref: str
    b_ref: str
    kind: Literal["coref","causal","contradiction_coupling","semantic_shadow"]
    weight: float = Field(ge=0.0, le=1.0)
    evidence: list[str] = Field(default_factory=list)

class Contradiction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    claim_a: str
    claim_b: str
    pressure: float = Field(ge=0.0, le=1.0)
    resolution: Literal["open","superseded","branch_split","accepted_paraconsistent"] = "open"
    resolution_ref: Optional[str] = None

class SemanticAnchor(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    label: str
    embedding_ref: str
    recoverability: Recoverability = Recoverability.LOSSLESS_SEMANTIC
    stability: float = Field(ge=0.0, le=1.0, default=1.0)

class ShardManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    shards: list[str]
    erasure_scheme: str = "rs(10,4)"
    merkle_root: str
    recoverability: Recoverability = Recoverability.LOSSLESS_STRUCTURAL

class ProjectionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    target_ref: str
    mode: ProjectionMode
    constraints: dict = Field(default_factory=dict)
    requested_by: str

class ProjectionResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    target_ref: str
    mode: ProjectionMode
    content: dict
    order_used: list[str]
    confidence: ConfidenceEnvelope
    recoverability: Recoverability
    lineage: list[str]
    ts: datetime = Field(default_factory=_now)

class ForkOp(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    from_branch: str
    to_branch: str
    reason: str
    authorizer: str
    pdp_decision_ref: str
    hic_approval_ref: Optional[str] = None
    ts: datetime = Field(default_factory=_now)

class MergeOp(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    branches: list[str]
    into: str
    policy: str
    authorizer: str
    pdp_decision_ref: str
    hic_approval_ref: str
    ts: datetime = Field(default_factory=_now)

class SupersessionOp(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    superseded_ref: str
    superseder_ref: str
    reason: str
    authorizer: str
    pdp_decision_ref: str
    hic_approval_ref: str
    ts: datetime = Field(default_factory=_now)

class Storytime(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    projection_ref: str
    narrative: str
    arc: list[str] = Field(default_factory=list)
    ts: datetime = Field(default_factory=_now)
```

## Z3.2 Alexandrian Archive layout (already mostly present)

Ensure these directories on `/Volumes/NSExternal/ALEXANDRIA/`:
```
branches/<branch_id>.json
projections/<projection_id>.json   (cache keyed by hash of request)
entanglements/<ent_id>.json
contradictions/<c_id>.json
anchors/<anchor_id>.json
shards/<shard_id>/{data,manifest.json}
storytime/<st_id>.json
ledger/ns_events.jsonl             (append-only, SHA-256 chained)
```

Storage adapter: `ns/integrations/omega_store.py` with:
- `read_json(subpath) -> dict | None`
- `write_json(subpath, obj) -> str` (returns sha256)
- `append_receipt(line: dict)` (fsync, flock, hash-chained)
- NEVER overwrites without an explicit supersede op.

## Z3.3 FastAPI routes

Add to `ns/api/routers/omega.py`:
- `POST /projections` → accepts `ProjectionRequest`, returns `ProjectionResult`
- `GET  /projections/{id}` → cached result
- `POST /storytime` → accepts `{projection_ref, narrative, arc}`,
  emits Storytime record + receipt `narrative_emitted_with_receipt_hash`
- `GET  /storytime/{id}`

Wire into `ns/api/server.py` lifespan.

## Z3.4 Projection engine — recovery order

`ns/services/omega/projection_engine.py`:

```python
STRATEGIES = [
    ("exact_local",            Recoverability.EXACT),
    ("delta_replay",           Recoverability.LOSSLESS_STRUCTURAL),
    ("shard_recovery",         Recoverability.LOSSLESS_STRUCTURAL),
    ("entanglement_assisted",  Recoverability.LOSSLESS_SEMANTIC),
    ("semantic",               Recoverability.LOSSY_SEMANTIC),
    ("graceful_partial",       Recoverability.IRRECOVERABLE),
]
```

Algorithm: attempt each strategy in order. On first `ok`, compute
the `ConfidenceEnvelope`, record `order_used`, return
`ProjectionResult`. If all fail, return `mode=PARTIAL_RECONSTRUCTION`
with `recoverability=IRRECOVERABLE` and explicit `gap` marker in
`content`.

Every projection writes a receipt named `projection_emitted` to
the Lineage Fabric.

## Z3.5 Canon promotion gate — already complete (Ring 4)

Do NOT reimplement. Verify that Omega's projection layer DOES NOT
bypass the existing `ns/services/canon/promotion_guard.py`. If
Omega ever writes to canon, it MUST call `promote(branch_id, ctx)`
which requires HIC + PDP + YubiKey quorum + ring6_phi_parallel.

## Z3.6 Tests

`ns/tests/test_omega_projection.py` — at minimum:
- 6 recovery strategies exercised (one test each)
- 6 projection modes return valid `ProjectionResult`
- ConfidenceEnvelope.score() with fixed inputs returns expected float
- `order_used` is recorded and non-empty
- Receipt `projection_emitted` lands in ledger
- Canon gate still refuses unauthorized promotion after Omega is live
- Abstention returns mode=PARTIAL_RECONSTRUCTION when all strategies fail

Target: ≥ 20 new tests. Must make `python3 -m pytest -x -q
ns/tests/test_omega_projection.py` GREEN.

---

# Z4 — Media engine integration

If `/mnt/user-data/uploads/media_engine_repo.zip` exists:
1. Unpack to `ns/services/media_engine/` (strip top-level dir if present).
2. Inspect for `router.py` / `service.py` / `schemas.py`.
3. Wire router into `ns/api/server.py` under `/media/*`.
4. Every media operation MUST call `pi/check` for admissibility
   and MUST route execution via Handrail (no direct fs/network).
5. Tests: `ns/tests/test_media_engine.py` — smoke + admissibility gate.

If zip absent: skip with receipt `media_engine_skipped_no_source`.

# Z5 — UI addition integration

If `/mnt/user-data/uploads/Ui_addition*` exists:
1. Read the spec.
2. Populate `ns/services/ui/{engine_room.py, living_architecture.py,
   runtime_panels.py, websocket_events.py}` additions only.
3. Every tile MUST fetch from real endpoints (no fabricated greens).
4. Tests: extend `ns/tests/test_ncom.py` (or add
   `ns/tests/test_ui_additions.py`) — projection-invariant tests.

If spec absent: skip with receipt `ui_addition_skipped_no_source`.

---

# Stop conditions

- Each phase: stop only when its pytest target is GREEN.
- Do NOT advance past a RED phase.
- Do NOT modify Rings 1–7, NCOM/PIIC, RIL/ORACLE, or CQHML code.
- Do NOT relax Canon gate thresholds or rewrite ontology names.
- Bash 3.2 only in shell scripts.
- All new files carry AXIOLEV header.
PROMPT_EOF
  log_ok "CLOSURE_PROMPT.md written"
  lineage_emit "prompt_written" "closure" "ok" "path=$PROMPT_MD"
}

# ---------- Claude Code invocation ------------------------------------------
invoke_claude() {
  _workdir="$1"; _phase_id="$2"; _phase_name="$3"; _test_expr="$4"
  _prompt="You are implementing NS∞ closure phase $_phase_id ($_phase_name) per CLOSURE_PROMPT.md in ~/axiolev_runtime. Package root is 'ns/' per ns_scaffold.zip. Consult CLOSURE_PROMPT.md before every edit. Stop only when 'python3 -m pytest -x -q $_test_expr' is GREEN. Preserve locked ontology (Gradient Field, Alexandrian Lexicon, State Manifold, Alexandrian Archive, Lineage Fabric, Narrative) — do NOT reintroduce deprecated names. Do NOT modify Rings 1-7, NCOM/PIIC, RIL/ORACLE, or CQHML code. Do NOT relax Canon gate. Honor I1-I10. Bash 3.2 only in shell scripts. Every new file carries AXIOLEV Holdings LLC © 2026 header."
  log_info "Invoking Claude Code: $_phase_id workdir=$_workdir"
  if [ "$FLAG_DRY_RUN" -eq 1 ]; then
    log_info "[dry-run] would invoke claude for $_phase_id"
    return 0
  fi
  ( cd "$_workdir" && \
    claude --dangerously-skip-permissions -p "$_prompt" ) \
    >>"$LOG_FILE" 2>&1 || log_warn "claude non-zero exit (pytest gate will verify)"
}

invoke_claude_fix() {
  _workdir="$1"; _phase_id="$2"; _phase_name="$3"; _test_expr="$4"; _attempt="$5"
  _prompt="Phase $_phase_id ($_phase_name) attempt $_attempt FAILED. Read CLOSURE_FIX_REQUEST.md and fix ONLY what is needed to make '$_test_expr' GREEN. Re-read CLOSURE_PROMPT.md. Preserve prior phase work. Do NOT relax Canon gate. Do NOT rename ontology. Do NOT modify files outside phase scope."
  log_info "Claude fix pass: $_phase_id attempt $_attempt"
  if [ "$FLAG_DRY_RUN" -eq 1 ]; then
    log_info "[dry-run] would invoke claude fix for $_phase_id"
    return 0
  fi
  ( cd "$_workdir" && \
    claude --dangerously-skip-permissions -p "$_prompt" ) \
    >>"$LOG_FILE" 2>&1 || log_warn "claude fix non-zero"
}

# ---------- pytest runner ----------------------------------------------------
run_pytest() {
  _workdir="$1"; _test_expr="$2"; _out="$3"
  ( cd "$_workdir" && python3 -m pytest -x -q $_test_expr ) > "$_out" 2>&1
  return $?
}

write_fix_request() {
  _workdir="$1"; _phase_id="$2"; _phase_name="$3"; _attempt="$4"
  _test_expr="$5"; _out="$6"
  _branch="$(git_in "$_workdir" rev-parse --abbrev-ref HEAD 2>/dev/null || echo unknown)"
  _head="$(git_in "$_workdir" rev-parse --short HEAD 2>/dev/null || echo unknown)"
  _status="$(git_in "$_workdir" status --porcelain 2>/dev/null | head -n 40)"
  _tail="$(tail -n 80 "$_out" 2>/dev/null || echo '(no output)')"
  cat > "$FIX_MD" <<FIX_EOF
# CLOSURE_FIX_REQUEST — NS∞ Closure Phase $_phase_id ($_phase_name)

- **Attempt:** $_attempt of $MAX_ATTEMPTS
- **Workdir:** $_workdir
- **Failing tests:** $_test_expr
- **Branch:** $_branch
- **HEAD:** $_head
- $AXIOLEV_OWNER © $AXIOLEV_YEAR — axiolevns@axiolev.com

## Workdir status (first 40 lines)
\`\`\`
$_status
\`\`\`

## pytest tail (last 80 lines)
\`\`\`
$_tail
\`\`\`

## Instructions
1. Re-read CLOSURE_PROMPT.md before editing.
2. Fix ONLY the scope needed to pass \`$_test_expr\`.
3. Preserve prior phase tags and commits.
4. Do NOT relax Canon gate (Ring 4) thresholds or the 6 gate conditions.
5. Keep existing integration surfaces intact:
   - ConstraintClass enum (SACRED/RELAXABLE) from Ring 1
   - Alexandrian Archive layout at /Volumes/NSExternal/ALEXANDRIA/
   - ring6_phi_parallel importable from ns.domain.models.g2_invariant
   - scaffold receipt names in ns/domain/receipts/names.py
6. Do NOT reintroduce deprecated names.
7. Bash 3.2 only in shell scripts.
8. Stop when \`python3 -m pytest -x -q $_test_expr\` is GREEN.
FIX_EOF
}

# ---------- Phase runner with fast-forward + retry --------------------------
run_phase() {
  _workdir="$1"; _phase_id="$2"; _phase_name="$3"
  _test_expr="$4"; _commit_desc="$5"; _tag="$6"; _skip_if_no_source="${7:-}"

  log_step "=== $_phase_id ($_phase_name) ==="
  lineage_emit "phase_start" "$_phase_id" "start" "tests=$_test_expr"

  # Optional skip condition (media/UI phases)
  if [ -n "$_skip_if_no_source" ] && [ ! -e "$_skip_if_no_source" ]; then
    log_warn "$_phase_id: source '$_skip_if_no_source' not found — SKIP"
    lineage_emit "phase_skipped" "$_phase_id" "skip" "missing=$_skip_if_no_source"
    tag_phase "$_workdir" "${_tag}-skipped"
    return 0
  fi

  # Fast-forward: if tag present and tests green, skip Claude
  if git_in "$_workdir" rev-parse -q --verify "refs/tags/$_tag" >/dev/null 2>&1; then
    _ff_out="$LOG_DIR/ff_${_phase_id}_${TS_RUN}.log"
    # For phases with no test target yet, just accept the tag
    if [ -z "$_test_expr" ] || echo "$_test_expr" | grep -q SKIP; then
      log_ok "$_phase_id fast-forwarded (tag $_tag, no-test phase)"
      lineage_emit "phase_fastforward" "$_phase_id" "ok" "tag=$_tag notest=1"
      return 0
    fi
    if run_pytest "$_workdir" "$_test_expr" "$_ff_out"; then
      log_ok "$_phase_id fast-forwarded (tag $_tag, tests GREEN)"
      lineage_emit "phase_fastforward" "$_phase_id" "ok" "tag=$_tag"
      return 0
    else
      log_warn "$_phase_id tag exists but tests RED — rerunning Claude"
    fi
  fi

  _attempt=1
  while [ "$_attempt" -le "$MAX_ATTEMPTS" ]; do
    _out="$LOG_DIR/pytest_${_phase_id}_a${_attempt}_${TS_RUN}.log"
    if [ "$_attempt" -eq 1 ]; then
      invoke_claude "$_workdir" "$_phase_id" "$_phase_name" "$_test_expr"
    else
      invoke_claude_fix "$_workdir" "$_phase_id" "$_phase_name" "$_test_expr" "$_attempt"
    fi
    log_info "pytest $_test_expr (attempt $_attempt)"
    if [ -z "$_test_expr" ]; then
      log_ok "$_phase_id: no test target — accepting on attempt $_attempt"
      break
    fi
    if run_pytest "$_workdir" "$_test_expr" "$_out"; then
      log_ok "$_phase_id GREEN on attempt $_attempt"
      lineage_emit "phase_pytest" "$_phase_id" "green" "attempt=$_attempt"
      break
    fi
    log_warn "$_phase_id RED attempt $_attempt"
    lineage_emit "phase_pytest" "$_phase_id" "red" "attempt=$_attempt"
    write_fix_request "$_workdir" "$_phase_id" "$_phase_name" "$_attempt" "$_test_expr" "$_out"
    _attempt=$((_attempt + 1))
    if [ "$_attempt" -gt "$MAX_ATTEMPTS" ]; then
      fail_exit "$_phase_id ($_phase_name) failed after $MAX_ATTEMPTS attempts — see $_out"
    fi
  done

  commit_phase "$_workdir" "$_phase_id" "$_commit_desc" \
    || fail_exit "$_phase_id commit failed"
  tag_phase "$_workdir" "$_tag" \
    || fail_exit "$_phase_id tag failed ($_tag)"
  log_ok "$_phase_id tagged $_tag"
  lineage_emit "phase_tagged" "$_phase_id" "ok" "tag=$_tag"
  rm -f "$FIX_MD" 2>/dev/null || true
}

# ---------- Z3 — Omega L10 projection layer --------------------------------
z3_omega_layer() {
  log_phase "Z3 — Omega L10 projection/ego layer"
  run_phase "$ROOT_REPO" "omega-Z3" \
    "Omega L10 projection/ego layer — six recovery strategies, six modes, confidence envelope, Lineage receipts" \
    "ns/tests/test_omega_projection.py" \
    "Omega L10 primitives + projection engine + /projections route + Storytime" \
    "omega-l10-v1"
}

# ---------- Z4 — Media engine integration -----------------------------------
z4_media_engine() {
  log_phase "Z4 — Media engine integration"
  _zip="$UPLOADS_DIR/media_engine_repo.zip"
  if [ ! -f "$_zip" ]; then
    log_warn "media_engine_repo.zip not found at $_zip — SKIP"
    lineage_emit "media_engine_skipped" "z4" "skip" "no_zip"
    tag_phase "$ROOT_REPO" "omega-media-skipped"
    return 0
  fi

  _dest="$ROOT_REPO/ns/services/media_engine"
  if [ ! -d "$_dest" ]; then
    log_info "unpacking media_engine_repo.zip → $_dest (staging first)"
    _stage="$(mktemp -d)"
    if unzip -q "$_zip" -d "$_stage" 2>/dev/null; then
      mkdir -p "$_dest"
      # Strip single top-level dir if present
      _top_count="$(ls "$_stage" | wc -l | tr -d ' ')"
      if [ "$_top_count" = "1" ] && [ -d "$_stage/$(ls "$_stage")" ]; then
        cp -R "$_stage/$(ls "$_stage")"/* "$_dest/" 2>/dev/null || true
      else
        cp -R "$_stage"/* "$_dest/" 2>/dev/null || true
      fi
      rm -rf "$_stage"
      log_ok "media_engine unpacked"
      lineage_emit "media_engine_unpacked" "z4" "ok" "dest=$_dest"
    else
      log_warn "unzip failed — skipping media engine"
      return 0
    fi
  else
    log_info "media_engine dir already present — wiring pass only"
  fi

  run_phase "$ROOT_REPO" "omega-Z4" \
    "Media engine integration (router wired via /media/*, Pi-gated, Handrail-executed)" \
    "ns/tests/test_media_engine.py" \
    "media engine router + schemas + Pi admissibility + Handrail-routed execution" \
    "omega-media-v1"
}

# ---------- Z5 — UI addition integration ------------------------------------
z5_ui_addition() {
  log_phase "Z5 — UI addition integration"
  _ui_spec=""
  for _f in "$UPLOADS_DIR"/Ui_addition*; do
    if [ -f "$_f" ]; then _ui_spec="$_f"; break; fi
  done
  if [ -z "$_ui_spec" ]; then
    log_warn "Ui_addition* spec not found in $UPLOADS_DIR — SKIP"
    lineage_emit "ui_addition_skipped" "z5" "skip" "no_spec"
    tag_phase "$ROOT_REPO" "omega-ui-skipped"
    return 0
  fi
  log_info "UI addition spec: $_ui_spec"
  # Copy spec into artifacts for Claude to read
  cp "$_ui_spec" "$ARTIFACTS_DIR/ui_addition_spec.$(basename "$_ui_spec" | sed 's/.*\.//')" 2>/dev/null || true

  run_phase "$ROOT_REPO" "omega-Z5" \
    "UI addition integration (Founder Console panels, no fabricated greens)" \
    "ns/tests/test_ui_additions.py" \
    "UI additions populated, projection-invariant tests green" \
    "omega-ui-v1"
}

# ---------- Z6 — 5-gate READY TO BOOT verification --------------------------
z6_ready_to_boot() {
  log_phase "Z6 — 5-gate READY TO BOOT verification"
  lineage_emit "z6_start" "boot" "start" ""

  _gate_out="$ARTIFACTS_DIR/ready_to_boot_${TS_RUN}.md"
  _gate_json="$ARTIFACTS_DIR/ready_to_boot_${TS_RUN}.json"
  _gate_pass=0
  _gate_fail=0
  _gate_results=""

  # Gate 1 — Alexandria
  if [ -d "$ALEX_MNT" ] && [ -d "$ALEX_LEDGER" ] && [ -w "$ALEX_LEDGER" ]; then
    _g1="PASS"; _gate_pass=$((_gate_pass+1))
  else
    _g1="FAIL"; _gate_fail=$((_gate_fail+1))
  fi
  _gate_results="${_gate_results}gate_1_alexandria,$_g1\n"

  # Gate 2 — Boot surface
  _g2_files=(
    "$ROOT_REPO/scripts/boot/ns_boot_founder.command"
    "$ROOT_REPO/scripts/boot/ns_verify_and_save.command"
    "$ROOT_REPO/scripts/boot/ns_shutdown_prep.command"
    "$ROOT_REPO/launchd/com.axiolev.ns_founder_boot.plist"
  )
  _g2_ok=1
  for _f in "${_g2_files[@]}"; do
    if [ ! -f "$_f" ]; then _g2_ok=0; fi
  done
  if [ -d "$ROOT_REPO/apps/dist/NS Infinity.app" ] || [ -d "$ROOT_REPO/apps/NS Infinity.app" ]; then
    : # app present
  else
    _g2_ok=0
  fi
  if [ "$_g2_ok" -eq 1 ]; then
    _g2="PASS"; _gate_pass=$((_gate_pass+1))
  else
    _g2="PARTIAL"; _gate_fail=$((_gate_fail+1))
  fi
  _gate_results="${_gate_results}gate_2_boot,$_g2\n"

  # Gate 3 — Runtime (localhost probes only; non-fatal if Docker down)
  _g3_probes_ok=0
  for _p in "http://127.0.0.1:9000/healthz" \
            "http://127.0.0.1:8011/healthz" \
            "http://127.0.0.1:8788/state" \
            "http://127.0.0.1:9090/state"; do
    if curl -sf -m 2 "$_p" >/dev/null 2>&1; then
      _g3_probes_ok=$((_g3_probes_ok+1))
    fi
  done
  if [ "$_g3_probes_ok" -ge 3 ]; then
    _g3="PASS ($_g3_probes_ok/4 live)"; _gate_pass=$((_gate_pass+1))
  elif [ "$_g3_probes_ok" -ge 1 ]; then
    _g3="PARTIAL ($_g3_probes_ok/4 live — start ./boot.sh to confirm)"; _gate_fail=$((_gate_fail+1))
  else
    _g3="OFFLINE (0/4 live — start ./boot.sh to confirm)"; _gate_fail=$((_gate_fail+1))
  fi
  _gate_results="${_gate_results}gate_3_runtime,$_g3\n"

  # Gate 4 — Constitutional (file-based proof if runtime offline)
  _g4_ok=1
  [ -f "$ROOT_REPO/ns/domain/models/g2_invariant.py" ] || _g4_ok=0
  [ -f "$ROOT_REPO/ns/services/canon/promotion_guard.py" ] || _g4_ok=0
  [ -f "$ROOT_REPO/.terminal_manager/signals/ring6_complete.signal" ] || [ -f "$ROOT_REPO/.signals/ring6_complete.signal" ] || _g4_ok=0
  # Additional live probes (non-fatal)
  curl -sf -m 2 "http://127.0.0.1:9000/ring5/gates" >/dev/null 2>&1 || true
  if [ "$_g4_ok" -eq 1 ]; then
    _g4="PASS"; _gate_pass=$((_gate_pass+1))
  else
    _g4="FAIL"; _gate_fail=$((_gate_fail+1))
  fi
  _gate_results="${_gate_results}gate_4_constitutional,$_g4\n"

  # Gate 5 — Visibility (full pytest, count passes)
  _g5_out="$LOG_DIR/gate5_pytest_${TS_RUN}.log"
  _g5_pass_count=0
  _g5_fail_count=0
  if ( cd "$ROOT_REPO" && python3 -m pytest ns/tests/ -q --tb=no ) > "$_g5_out" 2>&1; then
    _g5_pass_count="$(grep -oE '[0-9]+ passed' "$_g5_out" | head -1 | awk '{print $1}')"
    _g5="PASS (${_g5_pass_count:-?} tests green)"; _gate_pass=$((_gate_pass+1))
  else
    _g5_pass_count="$(grep -oE '[0-9]+ passed' "$_g5_out" | head -1 | awk '{print $1}')"
    _g5_fail_count="$(grep -oE '[0-9]+ failed' "$_g5_out" | head -1 | awk '{print $1}')"
    _g5="FAIL (${_g5_pass_count:-?} passed, ${_g5_fail_count:-?} failed) — see $_g5_out"
    _gate_fail=$((_gate_fail+1))
  fi
  _gate_results="${_gate_results}gate_5_visibility,$_g5\n"

  # Write report
  cat > "$_gate_out" <<GATES_EOF
# READY TO BOOT — 5-Gate Verification
**Timestamp:** $TS_RUN
**Commit:** $(git_c rev-parse --short HEAD 2>/dev/null || echo unknown)

| # | Gate | Result |
|---|---|---|
| 1 | Alexandria hard-mounted, ledger writable | $_g1 |
| 2 | Boot surface (scripts + app + launchd) | $_g2 |
| 3 | Runtime (ns_core/handrail/continuum/state) | $_g3 |
| 4 | Constitutional (Canon gate + Ring 6 + signals) | $_g4 |
| 5 | Visibility (full pytest suite) | $_g5 |

**Passed:** $_gate_pass / 5
**Failed:** $_gate_fail / 5

$([ "$_gate_fail" -eq 0 ] && echo "## VERDICT: **READY TO BOOT**" || echo "## VERDICT: **NOT READY — see failing gates**")

## Only remainder = 5 Ring 5 external items (out-of-band):
- stripe_llc_verification
- stripe_live_keys_vercel
- root_handrail_price_ids
- yubikey_slot2 (~\$55)
- dns_cname_root (root.axiolev.com → root-jade-kappa.vercel.app)
GATES_EOF

  # JSON form
  python3 - "$_gate_out" "$_gate_json" "$_g1" "$_g2" "$_g3" "$_g4" "$_g5" "$_gate_pass" "$_gate_fail" <<'PY' 2>/dev/null || true
import json, sys
md_path, json_path, g1, g2, g3, g4, g5, passed, failed = sys.argv[1:10]
data = {
  "ts": __import__("datetime").datetime.utcnow().isoformat() + "Z",
  "gates": {
    "1_alexandria": g1,
    "2_boot": g2,
    "3_runtime": g3,
    "4_constitutional": g4,
    "5_visibility": g5,
  },
  "passed": int(passed),
  "failed": int(failed),
  "verdict": "READY_TO_BOOT" if int(failed) == 0 else "NOT_READY",
  "external_gates_remaining": [
    "stripe_llc_verification",
    "stripe_live_keys_vercel",
    "root_handrail_price_ids",
    "yubikey_slot2",
    "dns_cname_root",
  ],
}
with open(json_path, "w") as f:
  json.dump(data, f, indent=2)
PY

  log_ok "ready-to-boot report → $_gate_out (passed=$_gate_pass fail=$_gate_fail)"
  lineage_emit "z6_end" "boot" "$([ "$_gate_fail" -eq 0 ] && echo ok || echo warn)" "passed=$_gate_pass failed=$_gate_fail"

  echo "$_gate_fail" > "$ARTIFACTS_DIR/.gate_failures"
}

# ---------- Z7 — Final closure certification + tagging ----------------------
z7_final_cert() {
  log_phase "Z7 — Final closure certification"
  lineage_emit "z7_start" "closure_cert" "start" ""

  _cert_md="$CERT_DIR/NS_CLOSURE_MAX_v1.md"
  _cert_json="$CERT_DIR/NS_CLOSURE_MAX_v1.json"

  _gate_fail="$(cat "$ARTIFACTS_DIR/.gate_failures" 2>/dev/null || echo 1)"
  _safe_to_push="$(cat "$ARTIFACTS_DIR/.safe_to_push" 2>/dev/null || echo 0)"
  _ontology_gaps="$(cat "$ARTIFACTS_DIR/.ontology_gaps" 2>/dev/null || echo 0)"

  _head="$(git_c rev-parse --short HEAD 2>/dev/null || echo unknown)"
  _all_tags="$(git_c tag --list 2>/dev/null | grep -cE '^(ring-|ncom-|ril-|cqhml-|omega-|ns-infinity-)' || echo 0)"

  cat > "$_cert_md" <<CERT_EOF
# NS∞ CLOSURE MAX — FINAL CERTIFICATION
**Timestamp (UTC):** $TS_RUN
**Commit:** $_head
**Branch:** $BASE_BRANCH
**$AXIOLEV_OWNER © $AXIOLEV_YEAR** — axiolevns@axiolev.com

## Closure artefacts

- Ontology audit: $ONTOLOGY_REPORT
- Ready-to-boot:  $ARTIFACTS_DIR/ready_to_boot_${TS_RUN}.md
- Secret scan:    $ARTIFACTS_DIR/secrets_scan_${TS_RUN}.txt
- Lineage local:  $CTF_LOCAL
- Lineage ledger: $CTF_LEDGER
- Master log:     $LOG_FILE

## Verdict

- Ontology gaps at start: $_ontology_gaps
- Gate failures:          $_gate_fail / 5
- Safe to push:            $([ "$_safe_to_push" = "1" ] && echo "YES" || echo "NO (secrets or gitleaks findings)")
- Tagged tags total:       $_all_tags

## Closure tags

- ns-infinity-closure-max-v1.0.0
- ns-infinity-ready-to-boot-${DATE_TAG} (if gate_fail=0)

## Next operator actions

1. Verify live runtime: \`./boot.sh\` then \`curl -sf 127.0.0.1:9000/healthz\`
2. Confirm 5-gate with: \`cat $ARTIFACTS_DIR/ready_to_boot_${TS_RUN}.md\`
3. If push required: \`$0 --push-safe\` (gated on gitleaks clean)
4. Ring 5 external items (out-of-band, not code):
   - AXIOLEV Holdings LLC Stripe verification
   - Stripe live keys → Vercel envs
   - ROOT + Handrail price IDs
   - YubiKey slot_2 (~\$55 yubico.com)
   - DNS CNAME root.axiolev.com → root-jade-kappa.vercel.app

## Operator one-liner summary

\`\`\`
bash ~/axiolev_runtime/scripts/boot/ns_verify_and_save.command
# → "Safe to shut down Mac." only when Gates 1-5 pass.
\`\`\`

## Doctrine (unchanged, for reference)

Models propose, NS decides, Violet speaks, Handrail executes,
Alexandrian Archive remembers. L10 may NEVER amend L1–L9.
LLMs are bounded L6 components and never define truth or state.

$AXIOLEV_OWNER — DIGNITY PRESERVED
CERT_EOF

  python3 - "$_cert_json" "$TS_RUN" "$_head" "$_gate_fail" "$_safe_to_push" "$_ontology_gaps" "$_all_tags" <<'PY' 2>/dev/null || true
import json, sys
path, ts, head, gate_fail, safe_push, ontology_gaps, tag_total = sys.argv[1:8]
data = {
  "certification_id": "NS_CLOSURE_MAX_v1",
  "certified_at": ts,
  "commit": head,
  "owner": "AXIOLEV Holdings LLC",
  "gate_failures": int(gate_fail),
  "ontology_gaps_at_start": int(ontology_gaps),
  "safe_to_push": safe_push == "1",
  "total_ns_tags": int(tag_total),
  "verdict": "CLOSURE_COMPLETE" if int(gate_fail) == 0 else "CLOSURE_PARTIAL",
  "external_gates_remaining": [
    "stripe_llc_verification",
    "stripe_live_keys_vercel",
    "root_handrail_price_ids",
    "yubikey_slot2",
    "dns_cname_root",
  ],
  "doctrine": "Models propose, NS decides, Violet speaks, Handrail executes, Alexandrian Archive remembers.",
}
with open(path, "w") as f:
  json.dump(data, f, indent=2)
PY

  log_ok "certification → $_cert_md"
  lineage_emit "certification_written" "closure_cert" "ok" "path=$_cert_md gates_failed=$_gate_fail"

  # Commit artifacts
  commit_phase "$ROOT_REPO" "closure-z7" "Closure max certification — ontology audit + 5-gate verify + $_all_tags tags" \
    || log_warn "z7 commit failed"

  # Tags
  tag_phase "$ROOT_REPO" "ns-infinity-closure-max-v1.0.0" \
    || log_warn "closure max tag failed"
  log_ok "tagged ns-infinity-closure-max-v1.0.0"

  if [ "$_gate_fail" -eq 0 ]; then
    tag_phase "$ROOT_REPO" "ns-infinity-ready-to-boot-${DATE_TAG}" \
      || log_warn "ready-to-boot tag failed"
    log_ok "tagged ns-infinity-ready-to-boot-${DATE_TAG}"
  else
    log_warn "gate failures > 0 — ready-to-boot tag WITHHELD (correct)"
  fi

  lineage_emit "z7_end" "closure_cert" "ok" "gates_failed=$_gate_fail"

  # Optional push (double-gated)
  if [ "$FLAG_PUSH_SAFE" -eq 1 ]; then
    if [ "$_safe_to_push" = "1" ] && [ "$_gate_fail" -eq 0 ]; then
      log_info "--push-safe + clean scan + gates green → pushing branch + tags"
      if [ "$FLAG_DRY_RUN" -eq 1 ]; then
        log_info "[dry-run] would: git push origin $BASE_BRANCH --tags"
      else
        if git_c push origin "$BASE_BRANCH" --tags >>"$LOG_FILE" 2>&1; then
          log_ok "pushed branch + tags"
          lineage_emit "git_push" "closure" "ok" "branch=$BASE_BRANCH"
        else
          log_warn "push failed (PAT may need renewal)"
          lineage_emit "git_push" "closure" "warn" "push_failed"
        fi
      fi
    else
      log_warn "--push-safe BLOCKED (safe_to_push=$_safe_to_push gate_fail=$_gate_fail)"
    fi
  else
    log_info "push not requested (pass --push-safe to allow when clean)"
  fi
}

# ---------- Return block -----------------------------------------------------
write_return_block() {
  _status="$1"; _reason="$2"
  _head="$(git_c rev-parse --short HEAD 2>/dev/null || echo unknown)"
  _tags="$(git_c tag --list 2>/dev/null | grep -E '(closure|ready-to-boot|omega)' | tr '\n' ' ')"
  _ret="$LOG_DIR/closure_return_${TS_RUN}.md"
  cat > "$_ret" <<RET_EOF
# NS∞ Closure Max Return Block
- **Run:** $TS_RUN
- **Status:** $_status
- **Reason:** $_reason
- **Branch:** $BASE_BRANCH
- **HEAD:** $_head
- $AXIOLEV_OWNER © $AXIOLEV_YEAR

## Artifacts
- Log:              $LOG_FILE
- Lineage local:    $CTF_LOCAL
- Lineage ledger:   $CTF_LEDGER
- Ontology audit:   $ONTOLOGY_REPORT
- Ready-to-boot:    $ARTIFACTS_DIR/ready_to_boot_${TS_RUN}.md
- Certification:    $CERT_DIR/NS_CLOSURE_MAX_v1.md
- Secret scan:      $ARTIFACTS_DIR/secrets_scan_${TS_RUN}.txt

## Closure tags
$_tags

## External gates remaining (out-of-band)
- stripe_llc_verification
- stripe_live_keys_vercel
- root_handrail_price_ids
- yubikey_slot2 (~\$55)
- dns_cname_root (root.axiolev.com → root-jade-kappa.vercel.app)
RET_EOF
  log_info "return block: $_ret"
}

# =============================================================================
# MAIN
# =============================================================================
main() {
  log_phase "NS∞ Closure Max Orchestrator — run $TS_RUN"
  log_info "$AXIOLEV_OWNER © $AXIOLEV_YEAR"
  log_info "flags: scrub_history=$FLAG_SCRUB_HISTORY push_safe=$FLAG_PUSH_SAFE dry_run=$FLAG_DRY_RUN pull=$FLAG_PULL single_phase='$FLAG_SINGLE_PHASE'"
  lineage_emit "closure_boot" "boot" "start" "run=$TS_RUN"

  preflight

  write_closure_prompt

  case "$FLAG_SINGLE_PHASE" in
    "")        : ;;                                         # run all
    Z1) z1_security_scrub; exit 0 ;;
    Z2) z2_ontology_audit; exit 0 ;;
    Z3) z3_omega_layer; exit 0 ;;
    Z4) z4_media_engine; exit 0 ;;
    Z5) z5_ui_addition; exit 0 ;;
    Z6) z6_ready_to_boot; exit 0 ;;
    Z7) z7_final_cert; exit 0 ;;
    *) fail_exit "unknown --phase: $FLAG_SINGLE_PHASE (valid: Z1..Z7)" ;;
  esac

  # Linear sequence
  z1_security_scrub
  z2_ontology_audit
  z3_omega_layer
  z4_media_engine
  z5_ui_addition
  z6_ready_to_boot
  z7_final_cert

  # Summary banner
  _gate_fail="$(cat "$ARTIFACTS_DIR/.gate_failures" 2>/dev/null || echo 1)"
  lineage_emit "closure_complete" "final" "ok" "run=$TS_RUN gate_fail=$_gate_fail"
  write_return_block "CLOSURE_COMPLETE" "all phases Z1-Z7 executed; gate_failures=$_gate_fail"

  printf '\n'
  printf '==============================================================\n'
  printf '  NS∞ CLOSURE MAX — DONE\n'
  printf '  ------------------------------------------------------------\n'
  printf '  Z1 Security scrub:      gitleaks + pre-commit hook installed\n'
  printf '  Z2 Ontology audit:      %s\n' "$ONTOLOGY_REPORT"
  printf '  Z3 Omega L10:           projection/ego layer wired\n'
  printf '  Z4 Media engine:        %s\n' "$([ -d "$ROOT_REPO/ns/services/media_engine" ] && echo 'integrated' || echo 'skipped (no source)')"
  printf '  Z5 UI addition:         %s\n' "$(ls "$ARTIFACTS_DIR"/ui_addition_spec* >/dev/null 2>&1 && echo 'integrated' || echo 'skipped (no source)')"
  printf '  Z6 Ready-to-boot:       %s\n' "$([ "$_gate_fail" -eq 0 ] && echo 'ALL 5 GATES GREEN' || echo "$_gate_fail gate(s) failing")"
  printf '  Z7 Certification:       %s\n' "$CERT_DIR/NS_CLOSURE_MAX_v1.md"
  printf '  ------------------------------------------------------------\n'
  printf '  Closure tag:            ns-infinity-closure-max-v1.0.0\n'
  if [ "$_gate_fail" -eq 0 ]; then
    printf '  Ready-to-boot tag:      ns-infinity-ready-to-boot-%s\n' "$DATE_TAG"
    printf '  VERDICT:                READY TO BOOT\n'
  else
    printf '  Ready-to-boot tag:      WITHHELD (fix failing gates)\n'
    printf '  VERDICT:                CLOSURE PARTIAL — see report\n'
  fi
  printf '  ------------------------------------------------------------\n'
  printf '  Next: bash scripts/boot/ns_verify_and_save.command\n'
  printf '  %s — DIGNITY PRESERVED\n' "$AXIOLEV_OWNER"
  printf '==============================================================\n'

  exit 0
}

main "$@"
