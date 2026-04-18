#!/usr/bin/env bash
# =============================================================================
# ns_master.sh — NS∞ Single-Terminal Master Orchestrator
# AXIOLEV Holdings LLC © 2026
# Author: axiolevns <axiolevns@axiolev.com>
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
SIG_DIR="${SIG_DIR:-$ROOT_REPO/.signals}"
TM_DIR="${TM_DIR:-$ROOT_REPO/.terminal_manager}"
LOG_DIR="${LOG_DIR:-$TM_DIR/logs}"
ALEX_MNT="${ALEX_MNT:-/Volumes/NSExternal/ALEXANDRIA}"
ALEX_LEDGER="${ALEX_LEDGER:-$ALEX_MNT/ledger}"

TS_RUN="$(date -u +%Y%m%dT%H%M%SZ)"
DATE_TAG="$(date -u +%Y%m%d)"
LOG_FILE="${LOG_DIR}/master_${TS_RUN}.log"
CTF_LOCAL="${LOG_DIR}/lineage_MASTER_${TS_RUN}.jsonl"
CTF_LEDGER="${ALEX_LEDGER}/ns_events.jsonl"
RETURN_MD="${LOG_DIR}/master_return_${TS_RUN}.md"
PROMPT_MD="${ROOT_REPO}/PROMPT.md"
FIX_MD="${ROOT_REPO}/FIX_REQUEST.md"

MAX_ATTEMPTS=3

# ---------- Color (tty-gated) -----------------------------------------------
if [ -t 1 ]; then
  C_RESET=$'\033[0m'; C_BOLD=$'\033[1m'
  C_RED=$'\033[31m'; C_GREEN=$'\033[32m'
  C_YEL=$'\033[33m'; C_CYAN=$'\033[36m'; C_MAG=$'\033[35m'
else
  C_RESET=""; C_BOLD=""; C_RED=""; C_GREEN=""; C_YEL=""; C_CYAN=""; C_MAG=""
fi

# ---------- Logging ----------------------------------------------------------
mkdir -p "${LOG_DIR}" 2>/dev/null || true
touch "${LOG_FILE}" 2>/dev/null || true

log()      { printf '%s [MASTER] %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*" | tee -a "${LOG_FILE}"; }
log_info() { log "${C_CYAN}INFO${C_RESET} $*"; }
log_ok()   { log "${C_GREEN}OK${C_RESET}   $*"; }
log_warn() { log "${C_YEL}WARN${C_RESET} $*"; }
log_err()  { log "${C_RED}ERR${C_RESET}  $*"; }
log_step() { log "${C_BOLD}${C_CYAN}==>${C_RESET} $*"; }
log_phase(){ log "${C_BOLD}${C_MAG}>>>${C_RESET} $*"; }

# ---------- Lineage Fabric emit (JSONL append-only) -------------------------
lineage_emit() {
  _event="$1"; shift
  _subject="$1"; shift
  _status="$1"; shift
  _detail="$*"
  _ts="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  _line="$(python3 -c '
import json,sys
ts,terminal,event,subject,status,detail=sys.argv[1:7]
print(json.dumps({"ts":ts,"terminal":terminal,"event":event,"subject":subject,"status":status,"detail":detail},ensure_ascii=False))
' "${_ts}" "MASTER" "${_event}" "${_subject}" "${_status}" "${_detail}" 2>/dev/null)"
  if [ -z "${_line}" ]; then
    _line="{\"ts\":\"${_ts}\",\"terminal\":\"MASTER\",\"event\":\"${_event}\",\"subject\":\"${_subject}\",\"status\":\"${_status}\",\"detail\":\"escape_failed\"}"
  fi
  printf '%s\n' "${_line}" >> "${CTF_LOCAL}" 2>/dev/null || true
  if [ -d "${ALEX_LEDGER}" ]; then
    printf '%s\n' "${_line}" >> "${CTF_LEDGER}" 2>/dev/null || true
  fi
}

# ---------- Fatal ------------------------------------------------------------
fail_exit() {
  _reason="$*"
  log_err "FATAL: ${_reason}"
  lineage_emit "build_failed" "master" "error" "${_reason}"
  write_return_block "BUILD_FAILED" "${_reason}"
  exit 1
}

# ---------- Prereqs ----------------------------------------------------------
need() {
  command -v "$1" >/dev/null 2>&1 || fail_exit "missing required tool: $1"
}

check_python() {
  _v="$(python3 -c 'import sys;print("%d.%d"%(sys.version_info.major,sys.version_info.minor))' 2>/dev/null || echo 0.0)"
  _maj="$(printf '%s' "${_v}" | awk -F. '{print $1}')"
  _min="$(printf '%s' "${_v}" | awk -F. '{print $2}')"
  if [ "${_maj}" -lt 3 ] || { [ "${_maj}" -eq 3 ] && [ "${_min}" -lt 11 ]; }; then
    fail_exit "python3 >= 3.11 required (found ${_v})"
  fi
  log_info "python3 ${_v} OK"
}

check_yubikey() {
  if command -v ykman >/dev/null 2>&1; then
    _serials="$(ykman list 2>/dev/null | awk '/Serial/ {print $NF}' | tr '\n' ' ')"
    case " ${_serials} " in
      *" ${YUBIKEY_SERIAL} "*)
        log_ok "YubiKey serial ${YUBIKEY_SERIAL} present (I9 anchor verified)"
        lineage_emit "yubikey_preflight" "hardware" "ok" "serial=${YUBIKEY_SERIAL}"
        return 0
        ;;
      *)
        log_warn "YubiKey serial ${YUBIKEY_SERIAL} NOT detected"
        lineage_emit "yubikey_preflight" "hardware" "warn" "not_detected"
        return 1
        ;;
    esac
  else
    log_warn "ykman CLI not installed; cannot verify YubiKey ${YUBIKEY_SERIAL}"
    lineage_emit "yubikey_preflight" "hardware" "warn" "ykman_missing"
    return 2
  fi
}

check_repo() {
  [ -d "${ROOT_REPO}/.git" ] || fail_exit "repo not found at ${ROOT_REPO}"
  cd "${ROOT_REPO}" || fail_exit "cd ${ROOT_REPO} failed"
  _br="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo unknown)"
  if [ "${_br}" != "${BASE_BRANCH}" ]; then
    log_warn "current branch ${_br}; switching to ${BASE_BRANCH}"
    git checkout "${BASE_BRANCH}" >>"${LOG_FILE}" 2>&1 || fail_exit "checkout ${BASE_BRANCH} failed"
  fi
  log_ok "repo ${ROOT_REPO} on branch ${BASE_BRANCH}"
}

check_alex() {
  [ -d "${ALEX_MNT}" ] || fail_exit "Alexandrian Archive mount not present at ${ALEX_MNT}"
  log_ok "Alexandrian Archive mount OK: ${ALEX_MNT}"
}

setup_dirs() {
  mkdir -p "${SIG_DIR}" "${LOG_DIR}" || fail_exit "dir setup failed"
  mkdir -p "${ALEX_LEDGER}" 2>/dev/null || log_warn "ledger dir create failed (read-only?)"
  log_ok "logs=${LOG_DIR}"
  lineage_emit "dirs_ready" "boot" "ok" "logs_ledger"
}

# ---------- Git helpers ------------------------------------------------------
git_c() {
  ( cd "${ROOT_REPO}" && \
    git -c "user.name=${GIT_USER_NAME}" -c "user.email=${GIT_USER_EMAIL}" "$@" )
}

git_cin() {
  _dir="$1"; shift
  ( cd "${_dir}" && \
    git -c "user.name=${GIT_USER_NAME}" -c "user.email=${GIT_USER_EMAIL}" "$@" )
}

commit_phase() {
  _dir="$1"; _phase_label="$2"; _desc="$3"
  _msg="${_phase_label}: ${_desc} green — ${AXIOLEV_OWNER} © ${AXIOLEV_YEAR}"
  git_cin "${_dir}" add -A || return 1
  if ! git_cin "${_dir}" diff --cached --quiet 2>/dev/null; then
    git_cin "${_dir}" commit -m "${_msg}" >>"${LOG_FILE}" 2>&1 || return 1
  else
    log_info "${_phase_label}: no staged changes (idempotent)"
  fi
  return 0
}

tag_phase() {
  _dir="$1"; _tag="$2"
  if git_cin "${_dir}" rev-parse -q --verify "refs/tags/${_tag}" >/dev/null 2>&1; then
    log_info "tag ${_tag} already present"
    return 0
  fi
  git_cin "${_dir}" tag -a "${_tag}" -m "${_tag} — ${AXIOLEV_OWNER} © ${AXIOLEV_YEAR}" >>"${LOG_FILE}" 2>&1
}

# ---------- Alexandrian Archive layout --------------------------------------
ensure_alexandria_layout() {
  log_info "Ensuring Alexandrian Archive layout"
  for sub in branches projections canon ledger \
             lexicon state/shards state/transitions narrative cqhml; do
    mkdir -p "${ALEX_MNT}/${sub}" 2>/dev/null || log_warn "mkdir ${sub} failed"
  done
  touch "${ALEX_MNT}/canon/rules.jsonl" 2>/dev/null || true
  touch "${ALEX_MNT}/ledger/ns_events.jsonl" 2>/dev/null || true
  touch "${ALEX_MNT}/lexicon/baptisms.jsonl" 2>/dev/null || true
  touch "${ALEX_MNT}/lexicon/supersessions.jsonl" 2>/dev/null || true
  lineage_emit "alex_layout" "substrate" "ok" "root=${ALEX_MNT}"
}

# ---------- Worktree helpers -------------------------------------------------
worktree_create() {
  _wt_dir="$1"; _feat_branch="$2"
  if [ -d "${_wt_dir}" ]; then
    log_info "removing stale worktree ${_wt_dir}"
    git_c worktree remove --force "${_wt_dir}" >/dev/null 2>&1 || rm -rf "${_wt_dir}"
  fi
  git_c worktree add -B "${_feat_branch}" "${_wt_dir}" "${BASE_BRANCH}" >>"${LOG_FILE}" 2>&1 \
    || fail_exit "worktree add failed: ${_wt_dir} (${_feat_branch})"
  git_cin "${_wt_dir}" commit --allow-empty -m "chore: init ${_feat_branch} worktree — ${AXIOLEV_OWNER} © ${AXIOLEV_YEAR}" >>"${LOG_FILE}" 2>&1
  log_ok "worktree ${_wt_dir} on ${_feat_branch}"
  lineage_emit "worktree_create" "${_feat_branch}" "ok" "dir=${_wt_dir}"
}

worktree_merge_and_cleanup() {
  _wt_dir="$1"; _feat_branch="$2"; _merge_tag="$3"
  cd "${ROOT_REPO}" || fail_exit "cd ${ROOT_REPO} failed"
  git_c checkout "${BASE_BRANCH}" >>"${LOG_FILE}" 2>&1 \
    || fail_exit "checkout ${BASE_BRANCH} failed (pre-merge)"
  if git_c merge --no-ff "${_feat_branch}" \
       -m "merge: ${_feat_branch} auto-merge — ${AXIOLEV_OWNER} © ${AXIOLEV_YEAR}" >>"${LOG_FILE}" 2>&1; then
    log_ok "merged ${_feat_branch} → ${BASE_BRANCH}"
    lineage_emit "merge" "${_feat_branch}" "ok" "into=${BASE_BRANCH}"
  else
    fail_exit "merge ${_feat_branch} failed; manual resolution required"
  fi
  tag_phase "${ROOT_REPO}" "${_merge_tag}" || log_warn "merge tag ${_merge_tag} not applied"
  log_info "worktree retained for audit: ${_wt_dir}"
  lineage_emit "merge_tagged" "${_feat_branch}" "ok" "tag=${_merge_tag}"
}

# ---------- Claude Code invocation ------------------------------------------
invoke_claude() {
  _work_dir="$1"; _phase_id="$2"; _phase_name="$3"; _test_expr="$4"
  _prompt="You are implementing NS∞ phase ${_phase_id} (${_phase_name}) per PROMPT.md in ~/axiolev_runtime. Package root is 'ns/' per ns_scaffold.zip. Consult PROMPT.md before every edit. Stop only when 'python3 -m pytest -x -q ${_test_expr}' is green. Preserve the locked ontology: Gradient Field, Alexandrian Lexicon, State Manifold, Alexandrian Archive, Lineage Fabric, Narrative. Do NOT reintroduce deprecated names (Ether, Lexicon alone, Manifold alone, Alexandria alone, CTF, Storytime as layer). Bash 3.2 only in shell scripts. Honor the 10 invariants I1-I10."
  log_info "Invoking Claude Code: phase=${_phase_id} (${_phase_name}) workdir=${_work_dir}"
  ( cd "${_work_dir}" && \
    claude --dangerously-skip-permissions -p "${_prompt}" ) \
    >>"${LOG_FILE}" 2>&1 || log_warn "claude non-zero exit (continuing to pytest gate)"
}

invoke_claude_fix() {
  _work_dir="$1"; _phase_id="$2"; _phase_name="$3"; _test_expr="$4"; _attempt="$5"
  _prompt="Phase ${_phase_id} (${_phase_name}) attempt ${_attempt} FAILED. Read FIX_REQUEST.md in ~/axiolev_runtime (not in the worktree) and fix ONLY what is required to make '${_test_expr}' green. Re-read PROMPT.md. Preserve prior phase work and their tags. Do NOT relax Canon gate thresholds. Do NOT break the scaffold ontology. Keep ring6_phi_parallel importable from ns.domain.models.g2_invariant. Bash 3.2 only in shell scripts."
  log_info "Claude fix pass: phase=${_phase_id} attempt=${_attempt}"
  ( cd "${_work_dir}" && \
    claude --dangerously-skip-permissions -p "${_prompt}" ) \
    >>"${LOG_FILE}" 2>&1 || log_warn "claude fix non-zero exit"
}

# ---------- pytest gate ------------------------------------------------------
run_pytest_for() {
  _work_dir="$1"; _test_expr="$2"; _out="$3"
  ( cd "${_work_dir}" && python3 -m pytest -x -q ${_test_expr} ) > "${_out}" 2>&1
  return $?
}

write_fix_request() {
  _work_dir="$1"; _phase_id="$2"; _phase_name="$3"; _attempt="$4"
  _test_expr="$5"; _out="$6"
  _branch="$(git_cin "${_work_dir}" rev-parse --abbrev-ref HEAD 2>/dev/null || echo unknown)"
  _head="$(git_cin "${_work_dir}" rev-parse --short HEAD 2>/dev/null || echo unknown)"
  _status="$(git_cin "${_work_dir}" status --porcelain 2>/dev/null | head -n 40)"
  _tail="$(tail -n 80 "${_out}" 2>/dev/null || echo '(no output)')"
  cat > "${FIX_MD}" <<FIX_EOF
# FIX_REQUEST — NS∞ Master — Phase ${_phase_id} (${_phase_name})

- **Attempt:** ${_attempt} of ${MAX_ATTEMPTS}
- **Workdir:** ${_work_dir}
- **Failing test:** ${_test_expr}
- **Branch:** ${_branch}
- **HEAD:** ${_head}
- ${AXIOLEV_OWNER} © ${AXIOLEV_YEAR} — axiolevns <axiolevns@axiolev.com>

## Workdir status (first 40 lines)
\`\`\`
${_status}
\`\`\`

## pytest tail (last 80 lines)
\`\`\`
${_tail}
\`\`\`

## Instructions
1. Re-read PROMPT.md before editing.
2. Fix ONLY the scope needed to pass \`${_test_expr}\`.
3. Preserve prior phase tags and commits.
4. Do NOT relax Canon gate thresholds or the 6 gate conditions.
5. Keep the T2/T3/T4 integration surface intact:
   - ConstraintClass enum (SACRED/RELAXABLE) exported from Ring 1
   - Alexandrian Archive layout keeps ledger/ at /Volumes/NSExternal/ALEXANDRIA/ledger/
   - ring6_phi_parallel importable from ns.domain.models.g2_invariant
   - scaffold receipt names (ns/domain/receipts/names.py) preserved
6. Do NOT reintroduce deprecated names:
   Ether, Lexicon alone, Manifold alone, Alexandria alone, CTF,
   Storytime as a layer name.
7. Bash 3.2 only in shell scripts.
8. Stop when \`python3 -m pytest -x -q ${_test_expr}\` is green.
FIX_EOF
}

# ---------- Phase runner — fast-forward if already tagged + green ------------
# run_phase <work_dir> <phase_id> <phase_name> <test_expr> <commit_desc> <tag>
run_phase() {
  _work_dir="$1"; _phase_id="$2"; _phase_name="$3"
  _test_expr="$4"; _commit_desc="$5"; _tag="$6"

  log_step "=== ${_phase_id} (${_phase_name}) ==="
  lineage_emit "phase_start" "${_phase_id}" "start" "name=${_phase_name} test=${_test_expr}"

  # Fast-forward: if tag already exists and tests are already green, skip Claude
  if git_cin "${_work_dir}" rev-parse -q --verify "refs/tags/${_tag}" >/dev/null 2>&1; then
    _ff_out="${LOG_DIR}/ff_${_phase_id}_${TS_RUN}.log"
    if run_pytest_for "${_work_dir}" "${_test_expr}" "${_ff_out}"; then
      log_ok "${_phase_id} fast-forwarded (tag ${_tag} present, tests green)"
      lineage_emit "phase_fastforward" "${_phase_id}" "ok" "tag=${_tag}"
      return 0
    else
      log_warn "${_phase_id} tag exists but tests RED — re-running Claude"
    fi
  fi

  _attempt=1
  while [ "${_attempt}" -le "${MAX_ATTEMPTS}" ]; do
    _out="${LOG_DIR}/pytest_${_phase_id}_a${_attempt}_${TS_RUN}.log"
    if [ "${_attempt}" -eq 1 ]; then
      invoke_claude "${_work_dir}" "${_phase_id}" "${_phase_name}" "${_test_expr}"
    else
      invoke_claude_fix "${_work_dir}" "${_phase_id}" "${_phase_name}" "${_test_expr}" "${_attempt}"
    fi
    log_info "pytest ${_test_expr} (attempt ${_attempt})"
    if run_pytest_for "${_work_dir}" "${_test_expr}" "${_out}"; then
      log_ok "${_phase_id} GREEN on attempt ${_attempt}"
      lineage_emit "phase_pytest" "${_phase_id}" "green" "attempt=${_attempt}"
      commit_phase "${_work_dir}" "${_phase_id}" "${_commit_desc}" \
        || fail_exit "${_phase_id} commit failed"
      tag_phase "${_work_dir}" "${_tag}" \
        || fail_exit "${_phase_id} tag failed (${_tag})"
      lineage_emit "phase_tagged" "${_phase_id}" "ok" "tag=${_tag}"
      log_ok "${_phase_id} tagged ${_tag}"
      rm -f "${FIX_MD}" 2>/dev/null || true
      return 0
    fi
    log_warn "${_phase_id} RED attempt ${_attempt}"
    lineage_emit "phase_pytest" "${_phase_id}" "red" "attempt=${_attempt}"
    write_fix_request "${_work_dir}" "${_phase_id}" "${_phase_name}" "${_attempt}" "${_test_expr}" "${_out}"
    _attempt=$((_attempt + 1))
  done
  fail_exit "${_phase_id} (${_phase_name}) failed after ${MAX_ATTEMPTS} attempts"
}

# ---------- Return block -----------------------------------------------------
write_return_block() {
  _status="$1"; _reason="$2"
  _head="$(git_c rev-parse --short HEAD 2>/dev/null || echo unknown)"
  _tags="$(git_c tag --list 2>/dev/null | tr '\n' ' ')"
  cat > "${RETURN_MD}" <<RET_EOF
# NS∞ Master Orchestrator Return Block
- **Run:** ${TS_RUN}
- **Status:** ${_status}
- **Reason:** ${_reason}
- **Branch:** ${BASE_BRANCH}
- **HEAD:** ${_head}
- ${AXIOLEV_OWNER} © ${AXIOLEV_YEAR} — axiolevns <axiolevns@axiolev.com>

## Artifacts
- Main log:              ${LOG_FILE}
- Lineage Fabric local:  ${CTF_LOCAL}
- Lineage Fabric ledger: ${CTF_LEDGER}

## Tags at exit
${_tags}

## External gates — pending, out-of-band
- stripe_llc_verification
- stripe_live_keys_vercel
- root_handrail_price_ids
- yubikey_slot2 (~\$55)
- dns_cname_root (root.axiolev.com -> root-jade-kappa.vercel.app)
RET_EOF
  log_info "return block: ${RETURN_MD}"
}

# ---------- PROMPT.md (master — covers ALL phases) --------------------------
write_prompt_md() {
  log_step "Writing master PROMPT.md (all phases)"
  cat > "${PROMPT_MD}" <<'PROMPT_EOF'
# NS∞ (NorthStar Infinity) — MASTER Implementation Prompt
**AXIOLEV Holdings LLC © 2026**
**Author:** axiolevns <axiolevns@axiolev.com>
**Repo:** mkaxiolev-max/handrail, branch `boot-operational-closure`
**Package root:** `ns/` per ns_scaffold.zip — DO NOT relocate.

## Locked Ontology (ENFORCE THROUGHOUT ALL PHASES)

**10-Layer Stack:**
- L1 Constitutional: Dignity Kernel, Sentinel Gate, Constitutional Canon, Canon Barrier
- L2 Gradient: Gradient Field (was "Ether" — deprecated)
- L3 Intake: Epistemic Envelope, admissibility predicates
- L4 Conversion: The Loom (reflector functor GradientField → Canon)
- L5 Semantic: Alexandrian Lexicon (was "Lexicon"/"Atomlex" — deprecated)
- L6 State: State Manifold (was "Manifold" alone — deprecated)
- L7 Memory: Alexandrian Archive (was "Alexandria" alone — deprecated)
- L8 Lineage: Lineage Fabric (was "CTF" — deprecated)
- L9 Error & Correction: HIC, PDP, supersession routers
- L10 Narrative & Interface: Ω-Link Narrative Interface, Violet Interface
  (layer name "Narrative"; Storytime retained ONLY as service module name)

**10 Invariants (honor in every phase):**
- I1 Canon precedes Conversion
- I2 Append-only memory (Lineage inertness)
- I3 No LLM authority over Canon
- I4 Hardware quorum on canon changes (YubiKey 26116460 mandatory)
- I5 Provenance inertness (cryptographic hash-chain)
- I6 Sentinel Gate soundness
- I7 Bisimulation with replay (2-safety)
- I8 Distributed eventual consistency (CRDT/SEC)
- I9 Hardware quorum for authority change (Byzantine ≥2f+1)
- I10 Supersession monotone (never delete)

**Doctrinal partition:**
Models propose, NS decides, Violet speaks, Handrail executes,
Alexandrian Archive remembers. L10 may NEVER amend L1–L9.
LLMs are bounded L6 components and never define truth or state.

---

# PHASE A — T1 RINGS 1-6

## Ring 1 — L1 Constitutional Layer + I1–I10
**Paths:**
- `ns/domain/models/constitutional.py` — ConstraintClass enum (SACRED, RELAXABLE),
  ConstitutionalRule, DignityCheck, SentinelGateDecision
- `ns/domain/models/sacred.py` — 7 sacred rules (all SACRED):
  dignity_kernel, append_only_lineage, receipt_requirement,
  no_unauthorized_canon, no_deletion_rewriting, no_identity_falsification,
  truthful_provenance
- `ns/domain/models/invariants.py` — I1..I10 exported as checkable predicates

**Test:** `ns/tests/test_ring1_constitutional_layer.py`
**Tag:** `ring-1-constitutional-layer-v1`

## Ring 2 — L5/L6/L7/L8 substrate
**Paths:**
- `ns/integrations/alexandrian_archive.py` (rename/alias from alexandria.py)
- `ns/integrations/alexandrian_lexicon.py` (NEW)
- `ns/integrations/state_manifold.py` (NEW)
- `ns/integrations/lineage_fabric.py` (NEW)

Storage on `/Volumes/NSExternal/ALEXANDRIA/`:
```
branches/<branch_id>.json
projections/<projection_id>.json
canon/rules.jsonl
ledger/ns_events.jsonl
lexicon/baptisms.jsonl
lexicon/supersessions.jsonl
state/shards/<shard_id>/deltas.jsonl
state/shards/<shard_id>/manifest.json
state/transitions/
narrative/
cqhml/
```
Append-only (I2), SHA-256 hash-chain (I5), fsync, fcntl.flock, supersession
only (I10), Alexandrian Lexicon baptism receipts.

**Test:** `ns/tests/test_ring2_substrate_layers.py`
**Tag:** `ring-2-substrate-layers-v1`

## Ring 3 — L4 The Loom
**Paths:** `ns/services/loom/service.py`, `ns/services/loom/mode_switching.py`

Reflector functor L : GradientField → Canon. ConfidenceEnvelope:
```
score = 0.45*evidence + 0.25*(1 - contradiction) + 0.15*novelty + 0.15*stability
```
(weights exact, sum = 1.0).

Loop: generate → test → contradict → reweight → narrate → store → re-enter.

**Test:** `ns/tests/test_ring3_loom.py`
**Tag:** `ring-3-loom-v1`

## Ring 4 — L3 Intake + Canon Promotion Gate
**Paths:**
- `ns/services/canon/service.py`
- `ns/services/canon/promotion_guard.py`
- `ns/services/canon/relation_binding.py`
- `ns/api/routers/canon.py` (POST /canon/promote)

Six-condition gate + I1 + I4:
1. confidence.score() ≥ 0.82
2. contradiction_weight ≤ 0.25
3. reconstructability ≥ 0.90
4. lineage_valid(branch) == True
5. HIC approval receipt present
6. PDP approval receipt present
Plus Lineage Fabric receipt written, I1 (Canon-before-Conversion), I4
(hardware quorum with YubiKey 26116460 as mandatory singleton Byzantine
≥2f+1 signer).

```python
def verify_hardware_quorum(quorum_certs: list[dict]) -> bool:
    yubi_present = any(c.get("serial") == "26116460" for c in quorum_certs)
    f = (len(quorum_certs) - 1) // 3
    return yubi_present and len(quorum_certs) >= 2*f + 1
```

Receipts emitted:
- `canon_promoted_with_hardware_quorum` on success
- `canon_promotion_denied_i9_quorum_missing` on failure

**Test:** `ns/tests/test_ring4_canon_promotion.py`
**Tag:** `ring-4-canon-promotion-v1`

## Ring 5 — External Gates (noted, out-of-band)
**Path:** `ns/domain/policies/external_gates.py`
```python
EXTERNAL_GATES = [
    {"id": "stripe_llc_verification", "status": "pending", "note": "out-of-band"},
    {"id": "stripe_live_keys_vercel", "status": "pending", "note": "out-of-band"},
    {"id": "root_handrail_price_ids", "status": "pending", "note": "out-of-band"},
    {"id": "yubikey_slot2", "status": "pending", "note": "~$55 procurement"},
    {"id": "dns_cname_root", "status": "pending",
     "note": "root.axiolev.com -> root-jade-kappa.vercel.app"},
]
```
No network calls.

**Test:** `ns/tests/test_ring5_external_gates_noted.py`
**Tag:** `ring-5-external-gates-noted-v1`

## Ring 6 — G₂ 3-form invariant ∇φ=0
**Path:** `ns/domain/models/g2_invariant.py` (T3/T4 import from this).

Fano plane (standard order): φ = e^123 + e^145 + e^167 + e^246 + e^257 + e^347 + e^356

```python
FANO_TRIPLES = ((1,2,3),(1,4,5),(1,6,7),(2,4,6),(2,5,7),(3,4,7),(3,5,6))
def phi_components() -> tuple: return FANO_TRIPLES
def nabla_phi_zero(state) -> bool: ...
def ring6_phi_parallel(state) -> bool: return nabla_phi_zero(state)
```

Ring 4 canon promotion MUST call `ring6_phi_parallel(state)`.
Receipt: `ring6_g2_invariant_checked`.

**Test:** `ns/tests/test_ring6_g2_invariant.py`
**Tag:** `ring-6-g2-invariant-v1`

---

# PHASE B — T2 NCOM/PIIC + FOUNDER CONSOLE (worktree feature/ncom-piic-v2)

## B1 doctrine-scaffold
Create `docs/doctrine/NCOM_PIIC_DOCTRINE.md` (Krishnamurti-aligned synthesis).
Add I12..I15 as sibling invariants.

**Tag:** `ncom-piic-doctrine-v2`

## B2 ncom-runtime
- `ns/services/ncom/__init__.py`
- `ns/services/ncom/state.py` — 8-state machine (inactive / priming /
  observing / branching / stabilizing / ready_for_collapse /
  forced_collapse / aborted)
- `ns/services/ncom/readiness.py` — CollapseReadiness (ERS, CRS, IPI,
  contradictionPressure, branchDiversityAdequacy, hardVetoes, recommendedAction)

**Tag:** `ncom-runtime-v2`

## B3 piic-chain
- `ns/services/piic/__init__.py`
- `ns/services/piic/chain.py` — monotonic forward progression with stage
  gates (perception → interpretation → identification → commitment)

**Tag:** `piic-chain-v2`

## B4 pi-gate-integration
Extend `ns/services/canon/promotion_guard.py` to require at promotion time:
- NCOM state in {ready_for_collapse, forced_collapse}
- PIIC stage == commitment
- readiness.recommendedAction == "collapse"
- hardVetoes == []

Receipt: `ncom_veto_emitted` when vetoed.

**Tag:** `ncom-pi-gate-v2`

## B5 founder-console-api
Extend `ns/api/routers/ui_runtime.py` with:
- GET /founder-console/snapshot
- GET /founder-console/history
- GET /founder-console/contradictions/active
- GET /founder-console/observations/open
- GET /founder-console/routing/current
- GET /founder-console/receipts/recent

Schemas: `ns/api/schemas/ncom_piic.py` (NEW).
Receipt names added: `ncom_state_transitioned`, `piic_stage_advanced`, `ncom_veto_emitted`.

**Tag:** `founder-console-api-v2`

## B6 founder-console-ui
Populate `ns/services/ui/engine_room.py`, `living_architecture.py`,
`runtime_panels.py`, `websocket_events.py`. Live-fetch snapshot from
`/founder-console/snapshot`. Render NCOM state pill, PIIC stage chain,
IPI/ERS/CRS gauges, contradiction list, top interpretation.

**Tag:** `founder-console-ui-v2`

## B7 tests-and-proof
- `ns/tests/test_ncom.py` (state transitions + readiness vetoes + collapse gate)
- `ns/tests/test_piic.py` (monotonic advance + no-skip + gate-on-NCOM)
- Proof: `proofs/ncom/ncom_piic_proof_v2.json`

**Tag:** `ncom-piic-tests-green-v2`

---

# PHASE C — T3 RIL + ORACLE v2 (worktree feature/ril-oracle-v2)

## C1 doctrine-scaffold
`docs/doctrine/RIL_ORACLE_DOCTRINE.md` — seven integrity engines, two-stage
adjudication, precedence ladder. Add I16..I20 extension invariants.

**Tag:** `ril-oracle-doctrine-v2`

## C2 ril-pydantic-models
Populate:
- `ns/domain/models/integrity.py` (full model)
- `ns/api/schemas/ril.py`
- `ns/api/schemas/common.py` (IntegrityRouteEffect, RouteIntent,
  ReflexiveIntegrityState, IntegritySummary)

**Tag:** `ril-models-v2`

## C3 ril-engines (8 scaffold files)
- `ns/services/ril/drift_engine.py`
- `ns/services/ril/grounding_engine.py`
- `ns/services/ril/commitment_engine.py`
- `ns/services/ril/encounter_engine.py`
- `ns/services/ril/founder_loop_breaker.py`
- `ns/services/ril/reality_binding_engine.py`
- `ns/services/ril/rendering_capture.py`
- `ns/services/ril/interface_recalibration.py`

**Tag:** `ril-engines-v2`

## C4 ril-evaluator
Populate `ns/services/ril/service.py` (compose all 8 engines).

**Tag:** `ril-evaluator-v2`

## C5 oracle-v2-contract
Populate `ns/api/schemas/oracle.py`:
OracleDecision, HandrailScope, OracleSeverity, ConstitutionalContext,
OracleCondition, OracleBlockingReason, HandrailExecutionEnvelope,
OracleAdjudicationRequest, OracleAdjudicationResponse.

**Tag:** `oracle-v2-contract-v2`

## C6 oracle-v2-adjudicator
Populate `ns/services/oracle/adjudicator.py`, `service.py`,
`constitutional_overlays.py` (MUST import `ring6_phi_parallel` from
`ns.domain.models.g2_invariant`), `decision_selector.py`,
`envelope_builder.py`, `founder_translation.py`, `trace_builder.py`.

**Tag:** `oracle-v2-adjudicator-v2`

## C7 policy-matrix
Populate `ns/services/oracle/policy_matrix.py`.

**Tag:** `oracle-policy-matrix-v2`

## C8 route-integration
Populate `ns/api/routers/ril.py` and `ns/api/routers/oracle.py`.

**Tag:** `ril-oracle-bridge-v2`

## C9 tests-and-proofs
- `ns/tests/test_ril_engines.py` (≥6 tests)
- `ns/tests/test_oracle_v2.py` (≥5 tests)
- Proof: `proofs/ril/ril_oracle_proof_v2.json`

**Tags:** `ril-oracle-tests-green-v2`, umbrella `ril-oracle-v2`, merge tag `ril-oracle-merged-v2`.

---

# PHASE D — T1 RING 7 FINAL CERTIFICATION

**Path:** `ns/services/canon/final_cert.py`

1. Verify tags `ncom-piic-merged-v2` and `ril-oracle-merged-v2` exist.
2. Verify feature branches `feature/ncom-piic-v2` and `feature/ril-oracle-v2`.
3. Run full `ns/tests/` suite (must be green).
4. Emit umbrella tag `ns-infinity-cqhml+ncom+ril-v1.0.0`.
5. Emit founder-grade tag `ns-infinity-founder-grade-<YYYYMMDD>`.

**Test:** `ns/tests/test_ring7_final_cert.py`
**Tag:** `ring-7-final-cert-v1`

---

# PHASE E — T4 CQHML MANIFOLD ENGINE (worktree feature/cqhml-manifold-v2)

## E1 doctrine-scaffold
`docs/doctrine/CQHML_MANIFOLD_DOCTRINE.md`.

**Tag:** `cqhml-manifold-doctrine-v2`

## E2 dimensions-pydantic-models
`ns/api/schemas/cqhml.py` (NEW):
DimensionalCoordinate, SemanticMode, PolicyMode, ObserverFrame,
DimensionalEnvelope, ProjectionRequest, ProjectionResult.

**Tag:** `cqhml-dimensions-v2`

## E3 cqhml-quaternion-core
`ns/services/cqhml/quaternion.py` (pure NumPy).

**Tag:** `cqhml-quaternion-core-v2`

## E4 cqhml-story-atom-loom
`ns/services/cqhml/story_atom_loom.py`.

**Tag:** `cqhml-story-atom-loom-v2`

## E5 dimensional-contradiction-engine
`ns/services/cqhml/contradiction_engine.py`.

**Tag:** `cqhml-contradiction-engine-v2`

## E6 dimensional-projection-service
`ns/services/cqhml/projection_service.py`.

**Tag:** `cqhml-projection-service-v2`

## E7 spin7-cayley-phi
`ns/domain/models/spin7_invariant.py`.

**Tag:** `cqhml-spin7-phi-v2`

## E8 omega-manifold-router
`ns/services/omega/manifold_router.py`.

**Tag:** `cqhml-omega-router-v2`

## E9 oracle-dimensional-gate
`ns/services/oracle/dimensional_gate.py`.

**Tag:** `cqhml-oracle-dim-gate-v2`

## E10 tests-and-proofs (>=24 tests)
`ns/tests/test_cqhml_*.py` (8 files).
Proof: `proofs/cqhml/cqhml_manifold_proof_v2.json`.

**Tags:** `cqhml-manifold-tests-green-v2`, umbrella `cqhml-manifold-v2`,
merge tag `cqhml-manifold-merged-v2`, final tag `ns-infinity-manifold-complete-v1.0.0`.

---

## Commit & tag conventions
- Author via `-c user.name/email` (axiolevns / axiolevns@axiolev.com)
- Commit: `<phase-id>: <desc> green — AXIOLEV Holdings LLC © 2026`
- Master never force-pushes.
PROMPT_EOF
  log_ok "PROMPT.md written (${PROMPT_MD})"
  lineage_emit "prompt_written" "boot" "ok" "path=${PROMPT_MD}"
}

# =============================================================================
# MAIN
# =============================================================================
main() {
  log_phase "NS∞ Master Orchestrator — run ${TS_RUN}"
  log_info "${AXIOLEV_OWNER} © ${AXIOLEV_YEAR}"
  lineage_emit "master_boot" "boot" "start" "run=${TS_RUN} repo=${ROOT_REPO}"

  need git; need curl; need node; need python3; need claude
  check_python
  check_repo
  check_alex
  setup_dirs
  check_yubikey || log_warn "YubiKey not verified; Ring 4 will re-check (fail-hard)"

  write_prompt_md
  ensure_alexandria_layout

  # ============================ PHASE A ======================================
  log_phase "PHASE A — T1 Rings 1-6"
  lineage_emit "phase_boundary" "phase-A" "start" "T1 Rings 1-6"

  run_phase "${ROOT_REPO}" "ring-1" "Constitutional Layer" \
    "ns/tests/test_ring1_constitutional_layer.py" \
    "L1 constitutional layer + 7 sacred rules + I1-I10 predicates" \
    "ring-1-constitutional-layer-v1"

  run_phase "${ROOT_REPO}" "ring-2" "Substrate Layers" \
    "ns/tests/test_ring2_substrate_layers.py" \
    "L5 Alexandrian Lexicon + L6 State Manifold + L7 Alexandrian Archive + L8 Lineage Fabric" \
    "ring-2-substrate-layers-v1"

  run_phase "${ROOT_REPO}" "ring-3" "The Loom" \
    "ns/tests/test_ring3_loom.py" \
    "L4 The Loom reflector functor with ConfidenceEnvelope" \
    "ring-3-loom-v1"

  check_yubikey || fail_exit "Ring 4 requires YubiKey serial ${YUBIKEY_SERIAL}"

  run_phase "${ROOT_REPO}" "ring-4" "Canon Promotion Gate" \
    "ns/tests/test_ring4_canon_promotion.py" \
    "L3 Intake + Canon gate (6 conditions + I1 + I4)" \
    "ring-4-canon-promotion-v1"

  run_phase "${ROOT_REPO}" "ring-5" "External Gates Noted" \
    "ns/tests/test_ring5_external_gates_noted.py" \
    "external gates noted (Stripe/DNS/YubiKey pending)" \
    "ring-5-external-gates-noted-v1"

  run_phase "${ROOT_REPO}" "ring-6" "G2 3-form Invariant" \
    "ns/tests/test_ring6_g2_invariant.py" \
    "G2 3-form invariant ring6_phi_parallel" \
    "ring-6-g2-invariant-v1"

  lineage_emit "phase_boundary" "phase-A" "end" "Rings 1-6 GREEN"

  # ============================ PHASE B ======================================
  log_phase "PHASE B — T2 NCOM/PIIC + Founder Console (worktree feature/ncom-piic-v2)"
  lineage_emit "phase_boundary" "phase-B" "start" "T2 NCOM/PIIC"

  WT_NCOM="${HOME}/axiolev_runtime_ncom_wt"
  worktree_create "${WT_NCOM}" "feature/ncom-piic-v2"

  run_phase "${WT_NCOM}" "ncom-P1" "doctrine scaffold" \
    "ns/tests/test_ring1_constitutional_layer.py" \
    "NCOM/PIIC doctrine (I12-I15)" \
    "ncom-piic-doctrine-v2"

  run_phase "${WT_NCOM}" "ncom-P2" "NCOM runtime (8-state machine + readiness)" \
    "ns/tests/test_ncom.py" \
    "NCOM 8-state runtime + CollapseReadiness (ERS/CRS/IPI + vetoes)" \
    "ncom-runtime-v2"

  run_phase "${WT_NCOM}" "ncom-P3" "PIIC chain (monotonic)" \
    "ns/tests/test_piic.py" \
    "PIIC monotonic chain with stage gates" \
    "piic-chain-v2"

  run_phase "${WT_NCOM}" "ncom-P4" "Pi-gate integration" \
    "ns/tests/test_ring4_canon_promotion.py" \
    "promotion_guard extended with NCOM/PIIC collapse-readiness gate" \
    "ncom-pi-gate-v2"

  run_phase "${WT_NCOM}" "ncom-P5" "Founder Console API" \
    "ns/tests/test_ncom.py" \
    "ui_runtime.py extended with /founder-console/* endpoints" \
    "founder-console-api-v2"

  run_phase "${WT_NCOM}" "ncom-P6" "Founder Console UI" \
    "ns/tests/test_ncom.py" \
    "engine_room + living_architecture + runtime_panels + websocket_events" \
    "founder-console-ui-v2"

  run_phase "${WT_NCOM}" "ncom-P7" "tests + proof" \
    "ns/tests/test_ncom.py ns/tests/test_piic.py" \
    "NCOM + PIIC test suite with proof json" \
    "ncom-piic-tests-green-v2"

  tag_phase "${WT_NCOM}" "ncom-piic-v2" || log_warn "umbrella tag ncom-piic-v2 failed"
  worktree_merge_and_cleanup "${WT_NCOM}" "feature/ncom-piic-v2" "ncom-piic-merged-v2"

  lineage_emit "phase_boundary" "phase-B" "end" "NCOM/PIIC merged"

  # ============================ PHASE C ======================================
  log_phase "PHASE C — T3 RIL + ORACLE v2 (worktree feature/ril-oracle-v2)"
  lineage_emit "phase_boundary" "phase-C" "start" "T3 RIL/ORACLE"

  WT_RIL="${HOME}/axiolev_runtime_ril_wt"
  worktree_create "${WT_RIL}" "feature/ril-oracle-v2"

  run_phase "${WT_RIL}" "ril-P1" "doctrine scaffold" \
    "ns/tests/test_ring1_constitutional_layer.py" \
    "RIL/ORACLE doctrine (I16-I20)" \
    "ril-oracle-doctrine-v2"

  run_phase "${WT_RIL}" "ril-P2" "RIL Pydantic models" \
    "ns/tests/test_ril_engines.py" \
    "integrity.py + schemas/ril.py + common.py populated" \
    "ril-models-v2"

  run_phase "${WT_RIL}" "ril-P3" "8 RIL engines" \
    "ns/tests/test_ril_engines.py" \
    "drift + grounding + commitment + encounter + founder_loop_breaker + reality_binding + rendering_capture + interface_recalibration" \
    "ril-engines-v2"

  run_phase "${WT_RIL}" "ril-P4" "RIL evaluator" \
    "ns/tests/test_ril_engines.py" \
    "services/ril/service.py composes all 8 engines" \
    "ril-evaluator-v2"

  run_phase "${WT_RIL}" "ril-P5" "ORACLE v2 contract" \
    "ns/tests/test_oracle_v2.py" \
    "schemas/oracle.py populated" \
    "oracle-v2-contract-v2"

  run_phase "${WT_RIL}" "ril-P6" "ORACLE v2 adjudicator (imports ring6_phi_parallel)" \
    "ns/tests/test_oracle_v2.py" \
    "adjudicator + service + constitutional_overlays + decision_selector + envelope_builder + founder_translation + trace_builder" \
    "oracle-v2-adjudicator-v2"

  run_phase "${WT_RIL}" "ril-P7" "Policy matrix" \
    "ns/tests/test_oracle_v2.py" \
    "policy_matrix precedence ladder" \
    "oracle-policy-matrix-v2"

  run_phase "${WT_RIL}" "ril-P8" "Route integration (Omega→RIL→ORACLE)" \
    "ns/tests/test_oracle_v2.py" \
    "routers/ril.py + routers/oracle.py + route bridge" \
    "ril-oracle-bridge-v2"

  run_phase "${WT_RIL}" "ril-P9" "RIL + ORACLE tests + proof" \
    "ns/tests/test_ril_engines.py ns/tests/test_oracle_v2.py" \
    "RIL + ORACLE v2 full test suite with proof json" \
    "ril-oracle-tests-green-v2"

  tag_phase "${WT_RIL}" "ril-oracle-v2" || log_warn "umbrella tag ril-oracle-v2 failed"
  worktree_merge_and_cleanup "${WT_RIL}" "feature/ril-oracle-v2" "ril-oracle-merged-v2"

  lineage_emit "phase_boundary" "phase-C" "end" "RIL/ORACLE merged"

  # ============================ PHASE D ======================================
  log_phase "PHASE D — T1 Ring 7 Final Certification"
  lineage_emit "phase_boundary" "phase-D" "start" "Ring 7 final cert"

  git_c checkout "${BASE_BRANCH}" >>"${LOG_FILE}" 2>&1 \
    || fail_exit "Ring 7: checkout ${BASE_BRANCH} failed"
  for _t in ncom-piic-merged-v2 ril-oracle-merged-v2; do
    git_c rev-parse -q --verify "refs/tags/${_t}" >/dev/null 2>&1 \
      || fail_exit "Ring 7: required merge tag missing: ${_t}"
    log_ok "merge tag present: ${_t}"
  done

  run_phase "${ROOT_REPO}" "ring-7" "Final Certification" \
    "ns/tests/test_ring7_final_cert.py" \
    "final certification record" \
    "ring-7-final-cert-v1"

  log_step "Ring 7: FULL ns/tests/ integration suite"
  _full_out="${LOG_DIR}/pytest_full_${TS_RUN}.log"
  if ( cd "${ROOT_REPO}" && python3 -m pytest -q ns/tests/ ) > "${_full_out}" 2>&1; then
    log_ok "full suite GREEN"
    lineage_emit "ring7_full_suite" "ring-7" "green" "log=${_full_out}"
  else
    _failed="$(grep -E 'FAILED|ERROR' "${_full_out}" | head -n 40 | tr '\n' ';')"
    lineage_emit "ring7_full_suite" "ring-7" "red" "failed=${_failed}"
    fail_exit "Ring 7 full suite RED — see ${_full_out}"
  fi

  tag_phase "${ROOT_REPO}" "ns-infinity-cqhml+ncom+ril-v1.0.0" \
    || fail_exit "umbrella tag failed"
  log_ok "tagged ns-infinity-cqhml+ncom+ril-v1.0.0"
  lineage_emit "umbrella_tag" "ring-7" "ok" "tag=ns-infinity-cqhml+ncom+ril-v1.0.0"

  tag_phase "${ROOT_REPO}" "ns-infinity-founder-grade-${DATE_TAG}" \
    || log_warn "founder-grade tag failed"
  log_ok "tagged ns-infinity-founder-grade-${DATE_TAG}"
  lineage_emit "founder_tag" "ring-7" "ok" "tag=ns-infinity-founder-grade-${DATE_TAG}"

  lineage_emit "phase_boundary" "phase-D" "end" "Ring 7 + umbrella + founder-grade tagged"

  # ============================ PHASE E ======================================
  log_phase "PHASE E — T4 CQHML Manifold Engine (worktree feature/cqhml-manifold-v2)"
  lineage_emit "phase_boundary" "phase-E" "start" "T4 CQHML/Manifold"

  WT_CQHML="${HOME}/axiolev_runtime_cqhml_wt"
  worktree_create "${WT_CQHML}" "feature/cqhml-manifold-v2"

  run_phase "${WT_CQHML}" "cqhml-P1" "CQHML doctrine" \
    "ns/tests/test_ring1_constitutional_layer.py" \
    "CQHML doctrine with non-goals and 7 axioms" \
    "cqhml-manifold-doctrine-v2"

  run_phase "${WT_CQHML}" "cqhml-P2" "dimensions / schemas" \
    "ns/tests/test_cqhml_dimensions.py" \
    "schemas/cqhml.py with 5D-11D + SemanticMode + PolicyMode + ObserverFrame + ProjectionRequest/Result" \
    "cqhml-dimensions-v2"

  run_phase "${WT_CQHML}" "cqhml-P3" "quaternion core (pure NumPy)" \
    "ns/tests/test_cqhml_quaternion.py" \
    "Spin(4) sandwich + Van Elfrinkhof decompose + HNF reorientation" \
    "cqhml-quaternion-core-v2"

  run_phase "${WT_CQHML}" "cqhml-P4" "Story Atom Loom" \
    "ns/tests/test_cqhml_story_atom_loom.py" \
    "StoryAtom + StoryAtomLoom (non-mutating)" \
    "cqhml-story-atom-loom-v2"

  run_phase "${WT_CQHML}" "cqhml-P5" "dimensional contradiction engine (7 detectors)" \
    "ns/tests/test_cqhml_contradiction_engine.py" \
    "7 D5-D11 detectors + severity aggregation + collapse blocking" \
    "cqhml-contradiction-engine-v2"

  run_phase "${WT_CQHML}" "cqhml-P6" "dimensional projection service" \
    "ns/tests/test_cqhml_projection_service.py" \
    "projection_service (read-only Alexandrian Archive; append-only receipts)" \
    "cqhml-projection-service-v2"

  run_phase "${WT_CQHML}" "cqhml-P7" "Spin(7) Cayley 4-form Phi" \
    "ns/tests/test_cqhml_spin7_phi.py" \
    "spin7_invariant.py complementing G2 invariant" \
    "cqhml-spin7-phi-v2"

  run_phase "${WT_CQHML}" "cqhml-P8" "Omega manifold router (tri-objective)" \
    "ns/tests/test_cqhml_omega_router.py" \
    "omega/manifold_router.py with truth/optionality/identity scoring" \
    "cqhml-omega-router-v2"

  run_phase "${WT_CQHML}" "cqhml-P9" "ORACLE dimensional gate (optional)" \
    "ns/tests/test_cqhml_oracle_dim_gate.py" \
    "oracle/dimensional_gate.py additive D11 check" \
    "cqhml-oracle-dim-gate-v2"

  run_phase "${WT_CQHML}" "cqhml-P10" "tests + proof (>=24 tests)" \
    "ns/tests/test_cqhml_dimensions.py ns/tests/test_cqhml_quaternion.py ns/tests/test_cqhml_story_atom_loom.py ns/tests/test_cqhml_contradiction_engine.py ns/tests/test_cqhml_projection_service.py ns/tests/test_cqhml_spin7_phi.py ns/tests/test_cqhml_omega_router.py ns/tests/test_cqhml_oracle_dim_gate.py" \
    "CQHML full test suite with proof json" \
    "cqhml-manifold-tests-green-v2"

  tag_phase "${WT_CQHML}" "cqhml-manifold-v2" || log_warn "umbrella tag cqhml-manifold-v2 failed"
  worktree_merge_and_cleanup "${WT_CQHML}" "feature/cqhml-manifold-v2" "cqhml-manifold-merged-v2"

  tag_phase "${ROOT_REPO}" "ns-infinity-manifold-complete-v1.0.0" \
    || fail_exit "final tag ns-infinity-manifold-complete-v1.0.0 failed"
  log_ok "tagged ns-infinity-manifold-complete-v1.0.0"
  lineage_emit "final_tag" "phase-E" "ok" "tag=ns-infinity-manifold-complete-v1.0.0"

  if git_c push origin "${BASE_BRANCH}" --tags >>"${LOG_FILE}" 2>&1; then
    log_ok "pushed branch + tags"
    lineage_emit "git_push" "final" "ok" "branch=${BASE_BRANCH}"
  else
    log_warn "git push failed (non-fatal)"
    lineage_emit "git_push" "final" "warn" "push_nonfatal"
  fi

  lineage_emit "phase_boundary" "phase-E" "end" "CQHML merged; final tag applied"

  # ============================ DONE =========================================
  lineage_emit "master_complete" "final" "ok" "run=${TS_RUN}"
  write_return_block "BUILD_COMPLETE" "Phases A-E green; all tags applied"

  printf '\n'
  printf '==============================================================\n'
  printf '  NS∞ MASTER BUILD COMPLETE\n'
  printf '  ------------------------------------------------------------\n'
  printf '  Phase A: Rings 1-6 green\n'
  printf '  Phase B: NCOM/PIIC merged   (ncom-piic-merged-v2)\n'
  printf '  Phase C: RIL/ORACLE merged  (ril-oracle-merged-v2)\n'
  printf '  Phase D: Ring 7 certified\n'
  printf '           umbrella  ns-infinity-cqhml+ncom+ril-v1.0.0\n'
  printf '           founder   ns-infinity-founder-grade-%s\n' "${DATE_TAG}"
  printf '  Phase E: CQHML Manifold merged (cqhml-manifold-merged-v2)\n'
  printf '           final tag ns-infinity-manifold-complete-v1.0.0\n'
  printf '  ------------------------------------------------------------\n'
  printf '  %s — DIGNITY PRESERVED\n' "${AXIOLEV_OWNER}"
  printf '==============================================================\n'
  exit 0
}

main "$@"
