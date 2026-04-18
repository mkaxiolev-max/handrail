#!/usr/bin/env bash
# =============================================================================
# final_completion_v3.sh — NS∞ Terminal 1 Orchestrator (7-Ring build, v3)
# =============================================================================
# AXIOLEV Holdings LLC © 2026 — axiolevns <axiolevns@axiolev.com>
#
# PURPOSE
#   Drive Claude Code through the NS∞ 7-Ring build on boot-operational-closure
#   inside the scaffolded `ns/` package, enforcing the locked canonical
#   ontology (Research_Report.pdf) and the scaffold floor (ns_scaffold.zip).
#
# LAYER COVERAGE (T1 owns L1..L8 substrate + G2 invariant; T2/T3/T4 own L9/L10
# extensions as named below):
#   Ring 1  L1 Constitutional Layer (Dignity Kernel / Sentinel Gate /
#                                    Constitutional Canon / Canon Barrier)
#                                    + I1..I10 predicates
#   Ring 2  L5 Alexandrian Lexicon + L6 State Manifold
#         + L7 Alexandrian Archive + L8 Lineage Fabric  (substrate grouping)
#   Ring 3  L4 The Loom (reflector functor L: Gradient Field → Canon)
#   Ring 4  L3 Epistemic Envelope + Canon promotion gate
#                                    (I1 canon-before-conversion, I4 hw quorum)
#   Ring 5  External gates noted (Stripe/DNS/YubiKey procurement/price IDs)
#   Ring 6  G₂ 3-form invariant (ring6_phi_parallel, FANO_TRIPLES)
#            → emits ring6_complete.signal
#   Ring 7  Final certification — waits on T2+T3 signals, runs full pytest,
#           emits umbrella tag ns-infinity-cqhml+ncom+ril-v1.0.0
#           + ns-infinity-founder-grade-<date>.
#
# INVARIANT ENFORCEMENT
#   I1  Canon precedes Conversion — gate is Ring 4
#   I2  Append-only memory (Lineage inertness) — Ring 2 Lineage Fabric writer
#   I3  No LLM authority over Canon — no LLM writes to canon/rules.jsonl
#   I4  Hardware quorum on canon changes — YubiKey 26116460 preflight (Ring 4+)
#   I5  Provenance inertness — Ring 2 hash-chain receipts
#   I6  Sentinel Gate soundness — Ring 1 predicate
#   I7  Bisimulation with replay — Ring 3 Loom determinism tests
#   I8  Distributed eventual consistency — Ring 2 CRDT semilattice merge
#   I9  Hardware quorum required for authority change (≥2f+1 w/ YubiKey 26116460
#       mandatory) — Ring 4 promotion_guard
#   I10 Supersession monotone (never-delete, supersede only) — Ring 2 ledger
#
# COORDINATION PROTOCOL (ASCII)
#
#   T1 builds Rings 1–6 ──► emits ring6_complete.signal
#            │
#            ▼
#   T2 (waits on signal) ──► builds NCOM/PIIC ──► emits ncom_piic_complete.signal
#            │
#            ▼
#   T3 (waits on BOTH)   ──► builds RIL/ORACLE ──► emits ril_oracle_complete.signal
#            │
#            ▼
#   T1 Ring 7 (waits on T2+T3) ──► umbrella tag ns-infinity-cqhml+ncom+ril-v1.0.0
#            │
#            ▼
#   T4 (waits on umbrella) ──► CQHML/Manifold ──► final tag
#                                                 ns-infinity-manifold-complete-v1.0.0
#
# BASH 3.2 compatibility: no associative arrays, no mapfile, no ${var,,},
#                         case/esac only; every variable quoted.
# =============================================================================

set -u
set -o pipefail

# ---------- Globals ----------------------------------------------------------
AXIOLEV_RUNTIME="${HOME}/axiolev_runtime"
SIGNALS_DIR="${AXIOLEV_RUNTIME}/.signals"
TM_DIR="${AXIOLEV_RUNTIME}/.terminal_manager"
LOG_DIR="${TM_DIR}/logs"
ALEX_ROOT="/Volumes/NSExternal/ALEXANDRIA"
ALEX_LEDGER="${ALEX_ROOT}/ledger"
BRANCH_MAIN="boot-operational-closure"
GIT_USER_NAME="axiolevns"
GIT_USER_EMAIL="axiolevns@axiolev.com"
YUBIKEY_SERIAL_REQUIRED="26116460"
TS_RUN="$(date -u +%Y%m%dT%H%M%SZ)"
DATE_TAG="$(date -u +%Y%m%d)"
LINEAGE_LOCAL="${LOG_DIR}/lineage_T1_${TS_RUN}.jsonl"
LINEAGE_ARCHIVE="${ALEX_LEDGER}/ns_events.jsonl"
MAIN_LOG="${LOG_DIR}/t1_run_${TS_RUN}.log"
RETURN_MD="${LOG_DIR}/T1_return_${TS_RUN}.md"
PROMPT_MD="${AXIOLEV_RUNTIME}/PROMPT.md"
FIX_MD="${AXIOLEV_RUNTIME}/FIX_REQUEST.md"
MAX_ATTEMPTS=3
WATCHDOG_SECONDS=$((8 * 3600))
POLL_INTERVAL=15
STATUS_INTERVAL=60

# ---------- Color (tty-gated) ------------------------------------------------
if [ -t 1 ]; then
  C_RESET=$'\033[0m'; C_BOLD=$'\033[1m'
  C_RED=$'\033[31m'; C_GREEN=$'\033[32m'; C_YEL=$'\033[33m'; C_CYAN=$'\033[36m'
else
  C_RESET=""; C_BOLD=""; C_RED=""; C_GREEN=""; C_YEL=""; C_CYAN=""
fi

# ---------- Logging ----------------------------------------------------------
mkdir -p "${LOG_DIR}" 2>/dev/null || true
touch "${MAIN_LOG}" 2>/dev/null || true

log() {
  _msg="$*"
  _ts="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  printf '%s [T1] %s\n' "${_ts}" "${_msg}" | tee -a "${MAIN_LOG}"
}
log_info()  { log "${C_CYAN}INFO${C_RESET} $*"; }
log_ok()    { log "${C_GREEN}OK${C_RESET}   $*"; }
log_warn()  { log "${C_YEL}WARN${C_RESET} $*"; }
log_err()   { log "${C_RED}ERR${C_RESET}  $*"; }
log_step()  { log "${C_BOLD}${C_CYAN}==>${C_RESET} $*"; }

# ---------- Lineage Fabric emit (JSONL append-only) --------------------------
lineage_emit() {
  # lineage_emit <event> <subject> <status> <detail...>
  _event="$1"; shift
  _subject="$1"; shift
  _status="$1"; shift
  _detail="$*"
  _ts="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  _line="$(python3 -c '
import json,sys
ts,terminal,event,subject,status,detail = sys.argv[1:7]
print(json.dumps({"ts":ts,"terminal":terminal,"event":event,"subject":subject,"status":status,"detail":detail}, ensure_ascii=False))
' "${_ts}" "T1" "${_event}" "${_subject}" "${_status}" "${_detail}" 2>/dev/null)"
  if [ -z "${_line}" ]; then
    _line="{\"ts\":\"${_ts}\",\"terminal\":\"T1\",\"event\":\"${_event}\",\"subject\":\"${_subject}\",\"status\":\"${_status}\",\"detail\":\"lineage_escape_failed\"}"
  fi
  printf '%s\n' "${_line}" >> "${LINEAGE_LOCAL}" 2>/dev/null || true
  if [ -d "${ALEX_LEDGER}" ]; then
    printf '%s\n' "${_line}" >> "${LINEAGE_ARCHIVE}" 2>/dev/null || true
  fi
}

# ---------- Fail-exit --------------------------------------------------------
fail_exit() {
  _reason="$*"
  log_err "FATAL: ${_reason}"
  lineage_emit "build_failed" "t1" "error" "${_reason}"
  write_return_block "BUILD_FAILED" "${_reason}"
  exit 1
}

# ---------- Prerequisites ----------------------------------------------------
check_prereqs() {
  log_step "Prerequisite checks"
  for tool in git python3 curl node unzip claude; do
    if ! command -v "${tool}" >/dev/null 2>&1; then
      fail_exit "missing required tool: ${tool}"
    fi
  done

  _pyver="$(python3 -c 'import sys;print("%d.%d"%(sys.version_info.major,sys.version_info.minor))' 2>/dev/null || echo 0.0)"
  _pymaj="$(printf '%s' "${_pyver}" | awk -F. '{print $1}')"
  _pymin="$(printf '%s' "${_pyver}" | awk -F. '{print $2}')"
  if [ "${_pymaj}" -lt 3 ] || { [ "${_pymaj}" -eq 3 ] && [ "${_pymin}" -lt 11 ]; }; then
    fail_exit "python3 >= 3.11 required (found ${_pyver})"
  fi

  if [ ! -d "${AXIOLEV_RUNTIME}/.git" ]; then
    fail_exit "repo not found at ${AXIOLEV_RUNTIME}"
  fi
  _cur_branch="$(cd "${AXIOLEV_RUNTIME}" && git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "")"
  if [ "${_cur_branch}" != "${BRANCH_MAIN}" ]; then
    log_warn "current branch is '${_cur_branch}' — attempting checkout of ${BRANCH_MAIN}"
    ( cd "${AXIOLEV_RUNTIME}" && git checkout "${BRANCH_MAIN}" ) \
      || fail_exit "could not checkout ${BRANCH_MAIN}"
  fi

  if [ ! -d "${ALEX_ROOT}" ]; then
    fail_exit "Alexandrian Archive mount not present at ${ALEX_ROOT}"
  fi

  DOCKER_SOCK=""
  if [ -S "/var/run/docker.sock" ]; then
    DOCKER_SOCK="/var/run/docker.sock"
  elif [ -S "${HOME}/.docker/run/docker.sock" ]; then
    DOCKER_SOCK="${HOME}/.docker/run/docker.sock"
  fi
  if [ -n "${DOCKER_SOCK}" ]; then
    log_info "docker socket: ${DOCKER_SOCK}"
  else
    log_warn "docker socket not detected (non-fatal)"
  fi

  log_ok "prerequisites satisfied (python ${_pyver}, branch ${BRANCH_MAIN})"
  lineage_emit "prereq_check" "boot" "ok" "python=${_pyver} branch=${BRANCH_MAIN}"
}

# ---------- YubiKey preflight (I4/I9) ---------------------------------------
check_yubikey() {
  _ring="$1"   # integer 1..7
  if ! command -v ykman >/dev/null 2>&1; then
    log_warn "ykman not installed — cannot verify YubiKey ${YUBIKEY_SERIAL_REQUIRED} presence"
    lineage_emit "yubikey_preflight" "ring-${_ring}" "warn" "ykman_missing"
    return 0
  fi
  _serials="$(ykman list 2>/dev/null | awk '/Serial number:/ {print $3}' | tr '\n' ' ')"
  case " ${_serials} " in
    *" ${YUBIKEY_SERIAL_REQUIRED} "*)
      log_ok "YubiKey ${YUBIKEY_SERIAL_REQUIRED} present"
      lineage_emit "yubikey_preflight" "ring-${_ring}" "ok" "serial=${YUBIKEY_SERIAL_REQUIRED}"
      return 0
      ;;
    *)
      if [ "${_ring}" -ge 4 ]; then
        fail_exit "YubiKey serial ${YUBIKEY_SERIAL_REQUIRED} required for Ring ${_ring} (I4/I9). Connect device and retry."
      else
        log_warn "YubiKey ${YUBIKEY_SERIAL_REQUIRED} not detected (non-fatal before Ring 4)"
        lineage_emit "yubikey_preflight" "ring-${_ring}" "warn" "missing_pre_ring4"
        return 0
      fi
      ;;
  esac
}

# ---------- Directory setup --------------------------------------------------
setup_dirs() {
  log_step "Directory setup"
  mkdir -p "${SIGNALS_DIR}" || fail_exit "cannot create ${SIGNALS_DIR}"
  mkdir -p "${LOG_DIR}"     || fail_exit "cannot create ${LOG_DIR}"
  if ! mkdir -p "${ALEX_LEDGER}" 2>/dev/null; then
    log_warn "ledger dir create failed (read-only?) — best-effort ledger writes"
  fi
  log_ok "signals=${SIGNALS_DIR} logs=${LOG_DIR} ledger=${ALEX_LEDGER}"
  lineage_emit "dirs_ready" "boot" "ok" "signals,logs,ledger"
}

# ---------- Alexandrian Archive layout (Ring 2 pre-seed) ---------------------
ensure_alexandrian_archive_layout() {
  log_info "Ensuring Alexandrian Archive layout on ${ALEX_ROOT}"
  for sub in branches projections canon ledger lexicon \
             state/shards state/transitions narrative cqhml; do
    if ! mkdir -p "${ALEX_ROOT}/${sub}" 2>/dev/null; then
      log_warn "could not create ${ALEX_ROOT}/${sub} (continuing)"
    fi
  done
  touch "${ALEX_ROOT}/canon/rules.jsonl" 2>/dev/null || true
  touch "${ALEX_ROOT}/ledger/ns_events.jsonl" 2>/dev/null || true
  touch "${ALEX_ROOT}/lexicon/baptisms.jsonl" 2>/dev/null || true
  touch "${ALEX_ROOT}/lexicon/supersessions.jsonl" 2>/dev/null || true
  lineage_emit "archive_layout" "ring-2" "ok" "root=${ALEX_ROOT}"
}

# ---------- PROMPT.md generation --------------------------------------------
write_prompt_md() {
  log_step "Writing PROMPT.md (Claude Code master specification)"
  cat > "${PROMPT_MD}" <<'PROMPT_EOF'
# NS∞ (NorthStar Infinity) — Master Implementation Prompt  v3

**AXIOLEV Holdings LLC © 2026** — axiolevns <axiolevns@axiolev.com>
**Repo:** mkaxiolev-max/handrail, branch `boot-operational-closure`
**Runtime root:** `~/axiolev_runtime`
**Alexandrian Archive:** `/Volumes/NSExternal/ALEXANDRIA`

This is the canonical specification for Terminal 1 (T1). T1 builds **Rings 1–6**
under the scaffolded `ns/` package, then performs **Ring 7 final certification**
after Terminal 2 (NCOM/PIIC) and Terminal 3 (RIL/ORACLE) have auto-merged.

## Locked ontology (Research_Report.pdf)

- L1 Constitutional Layer — Dignity Kernel, Sentinel Gate, Constitutional Canon, Canon Barrier
- L2 Gradient Layer — Gradient Field (formerly "Ether")
- L3 Intake Layer — Epistemic Envelope
- L4 Conversion Layer — The Loom
- L5 Semantic Layer — Alexandrian Lexicon (formerly "Lexicon/Atomlex")
- L6 State Layer — State Manifold (formerly "Manifold")
- L7 Memory Layer — Alexandrian Archive (formerly "Alexandria")
- L8 Lineage Layer — Lineage Fabric (formerly "CTF")
- L9 Error & Correction Layer — HIC, PDP, divergence/supersession
- L10 Narrative & Interface Layer — Ω-Link, Violet (layer name = Narrative;
       Storytime retained only as service module name per scaffold)

Never use deprecated names in code or docs.

## Ten invariants (I1..I10)

- I1  Canon precedes Conversion  (Ring 4 gate)
- I2  Append-only memory (Lineage inertness)  (Ring 2 writer)
- I3  No LLM authority over Canon
- I4  Hardware quorum on canon changes — YubiKey serial 26116460 mandatory
- I5  Provenance inertness (hash-chain)
- I6  Sentinel Gate soundness
- I7  Bisimulation with replay (2-safety)
- I8  Distributed eventual consistency (CRDT/SEC)
- I9  Hardware quorum for authority change (≥2f+1 w/ YubiKey 26116460 mandatory)
- I10 Supersession monotone (never-delete, supersede only)

LTL/TLA+ forms:
- I1:  G(emit(o) ⇒ (∃c : canon_committed(c) S emit(o)) ∧ c ⊨ o.spec)
- I2:  G(lineage = ℓ ⇒ X(Prefix(ℓ, lineage)))
- I5:  ∀i : lineage[i].id = Hash(lineage[i].content, prev_id)
- I6:  G(executed(a) ⇒ CB(canon)(a) = ⊤)
- I7:  ∀s1,s2 : lineage(s1)=lineage(s2) ⇒ Obs(s1) ~ Obs(s2)
- I10: canon ⊑ canon' ∧ ImmutableAxioms(canon) ⊆ canon'

## Scaffold floor (paths are exact)

```
ns/
  api/
    server.py
    deps/{config.py, receipts.py}
    routers/{health.py, ril.py, oracle.py, handrail.py, canon.py,
             storytime.py, ui_runtime.py}
    schemas/{common.py, canon.py, handrail.py, omega.py, oracle.py,
             ril.py, storytime.py, ui_runtime.py}
  domain/
    models/{integrity.py, g2_invariant.py (T1 Ring 6), spin7_invariant.py (T4)}
    receipts/{emitter.py, names.py, store.py}
  integrations/{alexandria.py (alias alexandrian_archive),
                ether.py (alias gradient_field),
                handrail_transport.py, hic.py, model_router.py, pdp.py}
  services/
    canon/{service.py, promotion_guard.py, relation_binding.py}
    handrail/{service.py, action_runner.py, envelope_guard.py,
              observation_runner.py, probe_runner.py, reconcile_callback.py}
    loom/{service.py, mode_switching.py}
    omega/{service.py, packet_builder.py}
    oracle/{service.py, adjudicator.py, constitutional_overlays.py,
            decision_selector.py, envelope_builder.py, founder_translation.py,
            policy_matrix.py, trace_builder.py}
    ril/{service.py, commitment_engine.py, drift_engine.py,
         encounter_engine.py, founder_loop_breaker.py, grounding_engine.py,
         interface_recalibration.py, reality_binding_engine.py,
         rendering_capture.py}
    storytime/{service.py, founder_view.py, humility_mode.py,
               narrative_trace.py}
    ui/{service.py, engine_room.py, living_architecture.py,
        runtime_panels.py, websocket_events.py}
  tests/{test_smoke.py, plus per-ring/per-packet tests added}
```

## Ownership (do NOT cross)

- T1 owns Rings 1–7 (this prompt)
- T2 owns NCOM/PIIC under `ns/services/ncom/` and `ns/services/piic/`
- T3 owns RIL + ORACLE v2 — populates the scaffold's existing files
- T4 owns CQHML/Manifold + 5D–11D under `ns/services/cqhml/` and
      `ns/domain/models/spin7_invariant.py`

Claude Code in T1 must NOT implement NCOM, PIIC, RIL, ORACLE, or CQHML work.
Limit all edits to the Ring scope described below.

## Ring 1 — L1 Constitutional Layer

Modules:
- `ns/api/schemas/canon.py` — `ConstraintClass(SACRED|RELAXABLE)`,
  `ConstitutionalRule`, `DignityCheck`, `NeverEvent`
- `ns/services/canon/service.py` — initial stub loads seven sacred constraints:
  dignity_kernel, append_only_lineage, receipt_requirement,
  no_unauthorized_canon, no_deletion_rewriting, no_identity_falsification,
  truthful_provenance
- `ns/services/canon/promotion_guard.py` — bare-minimum stub (Ring 4 fills it)
- `ns/domain/models/integrity.py` — basic types used across rings

Integration test: `ns/tests/test_ring1_constitutional_layer.py`
Tag: `ring1-constitutional-layer-v1`

## Ring 2 — Substrate (L5/L6/L7/L8)

Alexandrian Archive layout on `/Volumes/NSExternal/ALEXANDRIA/`:
```
branches/<branch_id>.json
projections/<projection_id>.json
canon/rules.jsonl              (append-only)
ledger/ns_events.jsonl         (append-only Lineage Fabric)
lexicon/baptisms.jsonl         (append-only Alexandrian Lexicon)
lexicon/supersessions.jsonl    (append-only)
state/shards/<id>/deltas.jsonl (append-only)
state/shards/<id>/manifest.json
state/transitions/
narrative/
cqhml/                         (T4 adds)
```

Modules to populate:
- `ns/integrations/alexandria.py` — expose `alexandrian_archive` as alias
- `ns/integrations/ether.py` — expose `gradient_field` as alias
- `ns/domain/receipts/emitter.py` — fsync'd append-only JSONL writer
- `ns/domain/receipts/store.py` — hash-chain reader
- `ns/domain/receipts/names.py` — extend authoritative set (see below)

Authoritative receipt names (extend, do not remove):
```
ril_evaluation_started
ril_drift_checked
ril_grounding_checked
ril_encounter_interrupt_triggered
ril_reality_binding_checked
ril_route_effects_emitted
oracle_received_ril_packet
oracle_adjudicated_with_integrity_state
oracle_handrail_envelope_built
storytime_humility_entered
interface_recalibration_entered
interface_recalibration_completed
handrail_scope_narrowed_by_ril
ring6_g2_invariant_checked                    (added by T1)
canon_promoted_with_hardware_quorum           (added by T1)
canon_promotion_denied_i9_quorum_missing      (added by T1)
lineage_fabric_appended                       (added by T1)
alexandrian_lexicon_baptism_receipted         (added by T1)
alexandrian_lexicon_drift_blocked             (added by T1)
narrative_emitted_with_receipt_hash           (added by T1)
dimensional_contradiction_detected            (added by T4)
manifold_projection_lawful                    (added by T4)
```

Integration test: `ns/tests/test_ring2_substrate_layers.py`
Tag: `ring2-substrate-layers-v1`

## Ring 3 — L4 The Loom

Modules:
- `ns/services/loom/service.py` — reflector functor L: Gradient → Canon with
  `apply(gradient_triple, canon) -> proposition_with_provenance`
- `ns/services/loom/mode_switching.py` — deterministic mode selection

I7 bisimulation test: running the same lineage prefix twice must produce
bisimilar observations.

Integration test: `ns/tests/test_ring3_loom.py`
Tag: `ring3-loom-v1`

## Ring 4 — L3 Intake + Canon promotion gate

Modules:
- `ns/api/routers/canon.py` — POST /canon/promote
- `ns/services/canon/service.py` — `promote(branch_id, context)`
- `ns/services/canon/promotion_guard.py` — gate logic

Gate — ALL six conditions must hold:
1. `confidence.score() >= 0.82`
2. `contradiction_weight <= 0.25`
3. `reconstructability >= 0.90`
4. `lineage_valid(branch)` is True
5. `HIC.approves` is True
6. `PDP.approves` is True
7. Lineage Fabric receipt is written (`canon_promoted_with_hardware_quorum`)
8. I1: candidate branch must have commitIdx of a canon axiom < emit-tick
9. I4/I9: QuorumCert(YubiKey 26116460) mandatory; 2f+1 validators

If I9 quorum missing → emit `canon_promotion_denied_i9_quorum_missing` and
return structured error `{"error":"I9_QUORUM_MISSING"}`.

Integration test: `ns/tests/test_ring4_canon_promotion.py`
Tag: `ring4-canon-promotion-v1`

## Ring 5 — External gates (noted)

`ns/services/canon/relation_binding.py` or a new `ns/domain/policies/external_gates.py`
declares the pending external gates without performing network calls:
```
stripe_llc_verification          pending
stripe_live_keys_vercel          pending
root_handrail_price_ids          pending
yubikey_slot2                    pending  (~$55 procurement)
dns_cname_root                   pending  (root.axiolev.com → Vercel)
```

Integration test: `ns/tests/test_ring5_external_gates_noted.py`
Tag: `ring5-external-gates-noted-v1`

## Ring 6 — G₂ 3-form invariant

`ns/domain/models/g2_invariant.py` — exact surface T3/T4 will import:
```python
FANO_TRIPLES = (
    (1,2,3),(1,4,5),(1,6,7),(2,4,6),(2,5,7),(3,4,7),(3,5,6),
)
def phi_components() -> tuple: return FANO_TRIPLES
def nabla_phi_zero(state) -> bool: ...
def ring6_phi_parallel(state) -> bool:
    return nabla_phi_zero(state)
```

Every canonical promotion in Ring 4 must call `ring6_phi_parallel(state)` and
refuse promotion if False. Emit receipt `ring6_g2_invariant_checked`.

Integration test: `ns/tests/test_ring6_g2_invariant.py`
Tag: `ring6-g2-invariant-v1`

## Ring 7 — Final certification

T1 will:
1. Wait for BOTH signals: `ncom_piic_complete.signal`, `ril_oracle_complete.signal`
2. `git fetch --all --tags && git checkout ${BRANCH_MAIN} && git pull --ff-only`
3. Verify merge tags: `ncom-piic-merged-v2`, `ril-oracle-merged-v2`
4. Verify feature branches: `feature/ncom-piic-v2`, `feature/ril-oracle-v2`
5. Run FULL `ns/tests/` integration suite
6. Tag `ns-infinity-cqhml+ncom+ril-v1.0.0` (umbrella)
7. Tag `ns-infinity-founder-grade-<YYYYMMDD>` (founder)
8. Emit `build_complete` Lineage Fabric receipt

Integration test: `ns/tests/test_ring7_final_cert.py`
Tag: `ring7-final-cert-v1`

## Conventions

- Author every commit via `git -c user.name=axiolevns -c user.email=axiolevns@axiolev.com commit`
- Commit message: `ring-N: <description> green — AXIOLEV © 2026`
- Per-ring tag: `ringN-<kebab>-v1`
- Ring 7 special: `ring7-final-cert-v1`
- All timestamps UTC ISO-8601
- Pydantic v2 everywhere (`model_config = ConfigDict(extra="forbid")`)
- No print() in library code; use `structlog` if adding logging

## Ownership guardrails

Do NOT create or modify files under any of these paths — those belong to
other terminals:
- `ns/services/ncom/*`          (T2)
- `ns/services/piic/*`          (T2)
- `ns/services/cqhml/*`         (T4)
- `ns/domain/models/spin7_invariant.py`  (T4)
- `ns/services/omega/manifold_router.py` (T4)
- `ns/services/oracle/dimensional_gate.py` (T4)

For RIL/ORACLE scaffolded files, populate ONLY a minimal stub sufficient for
Ring 1–4 imports; T3 will fill bodies.

PROMPT_EOF
  log_ok "PROMPT.md written (${PROMPT_MD})"
  lineage_emit "prompt_written" "boot" "ok" "path=${PROMPT_MD}"
}

# ---------- Git helpers ------------------------------------------------------
git_in_repo() {
  ( cd "${AXIOLEV_RUNTIME}" && \
    git -c "user.name=${GIT_USER_NAME}" -c "user.email=${GIT_USER_EMAIL}" "$@" )
}

commit_ring() {
  _ring="$1"
  _desc="$2"
  _msg="ring-${_ring}: ${_desc} green — AXIOLEV © 2026"
  git_in_repo add -A || return 1
  if ! git_in_repo diff --cached --quiet 2>/dev/null; then
    git_in_repo commit -m "${_msg}" || return 1
  else
    log_info "ring-${_ring}: no changes to commit (idempotent)"
  fi
  return 0
}

tag_ring() {
  _tag="$1"
  if git_in_repo rev-parse -q --verify "refs/tags/${_tag}" >/dev/null 2>&1; then
    log_info "tag ${_tag} already present — skip"
    return 0
  fi
  git_in_repo tag -a "${_tag}" -m "${_tag} — AXIOLEV © 2026" || return 1
  return 0
}

# ---------- Claude Code invocation ------------------------------------------
invoke_claude() {
  _ring_num="$1"
  _ring_name="$2"
  _test_path="$3"
  _prompt="Implement NS∞ Ring ${_ring_num} (${_ring_name}) per PROMPT.md in ~/axiolev_runtime. Consult PROMPT.md before every edit. Stop when 'python3 -m pytest -x -q ${_test_path}' is green. Do NOT implement NCOM/PIIC (T2), RIL/ORACLE (T3), or CQHML/Manifold/5D-11D (T4). Preserve all prior ring work and tags. Do not relax the Canon gate. Honor Bash 3.2 constraints in any shell scripts you touch. Use locked ontology names: Gradient Field, Alexandrian Lexicon, State Manifold, Alexandrian Archive, Lineage Fabric, Narrative — not their deprecated forms."
  log_info "Invoking Claude Code for Ring ${_ring_num} (${_ring_name})"
  ( cd "${AXIOLEV_RUNTIME}" && \
    claude --dangerously-skip-permissions -p "${_prompt}" ) \
    >> "${MAIN_LOG}" 2>&1 || log_warn "claude exited non-zero (continuing to test gate)"
}

invoke_claude_fix() {
  _ring_num="$1"
  _ring_name="$2"
  _test_path="$3"
  _attempt="$4"
  _prompt="Ring ${_ring_num} (${_ring_name}) attempt ${_attempt} FAILED. Read FIX_REQUEST.md in ~/axiolev_runtime and fix ONLY what is needed to make '${_test_path}' green. Re-read PROMPT.md. Do not relax Canon gate. Do not rename any ontology terms. Do not modify files outside Ring ${_ring_num} scope. Preserve prior ring tags and commits."
  log_info "Invoking Claude Code fix pass for Ring ${_ring_num} attempt ${_attempt}"
  ( cd "${AXIOLEV_RUNTIME}" && \
    claude --dangerously-skip-permissions -p "${_prompt}" ) \
    >> "${MAIN_LOG}" 2>&1 || log_warn "claude fix exited non-zero (continuing to test gate)"
}

# ---------- pytest gate ------------------------------------------------------
run_ring_test() {
  _test_path="$1"
  _out_file="$2"
  ( cd "${AXIOLEV_RUNTIME}" && \
    python3 -m pytest -x -q "${_test_path}" ) > "${_out_file}" 2>&1
  return $?
}

write_fix_request() {
  _ring_num="$1"
  _ring_name="$2"
  _attempt="$3"
  _test_path="$4"
  _pytest_out="$5"
  _branch="$(git_in_repo rev-parse --abbrev-ref HEAD 2>/dev/null || echo unknown)"
  _head="$(git_in_repo rev-parse --short HEAD 2>/dev/null || echo unknown)"
  _status="$(git_in_repo status --porcelain 2>/dev/null | head -n 40)"
  _tail="$(tail -n 80 "${_pytest_out}" 2>/dev/null || echo "(no pytest output captured)")"

  cat > "${FIX_MD}" <<FIX_EOF
# FIX_REQUEST — NS∞ Ring ${_ring_num} (${_ring_name})

- Attempt: ${_attempt} of ${MAX_ATTEMPTS}
- Failing test: ${_test_path}
- Branch: ${_branch}
- HEAD: ${_head}
- AXIOLEV Holdings LLC © 2026 — axiolevns <axiolevns@axiolev.com>

## Repo status (first 40 lines)

\`\`\`
${_status}
\`\`\`

## pytest tail (last 80 lines)

\`\`\`
${_tail}
\`\`\`

## Instructions to Claude Code

1. Re-read \`PROMPT.md\` in full before editing.
2. Fix ONLY the scope required to make \`${_test_path}\` pass.
3. Preserve all prior ring work (Rings 1..$((_ring_num - 1))) and their tags.
4. Do NOT relax the Canon gate thresholds or rules.
5. Do NOT rename any locked-ontology terms:
   - Gradient Field (not Ether)
   - Alexandrian Lexicon (not Lexicon/Atomlex)
   - State Manifold (not Manifold)
   - Alexandrian Archive (not Alexandria)
   - Lineage Fabric (not CTF)
   - Narrative (not Storytime as layer name)
6. Do NOT modify files outside Ring ${_ring_num} scope.
7. Do NOT implement NCOM/PIIC (T2), RIL/ORACLE (T3), or CQHML (T4).
8. Bash 3.2 only for any shell code (no assoc arrays, no mapfile, no \${var,,}).
9. Re-run \`python3 -m pytest -x -q ${_test_path}\` and stop when green.
FIX_EOF
}

# ---------- Ring runner ------------------------------------------------------
run_ring() {
  _ring_num="$1"
  _ring_name="$2"
  _kebab="$3"
  _test_path="$4"
  _desc="$5"

  check_yubikey "${_ring_num}"

  log_step "=== RING ${_ring_num} (${_ring_name}) BEGIN ==="
  lineage_emit "ring_start" "ring-${_ring_num}" "start" "name=${_ring_name} test=${_test_path}"

  _attempt=1
  while [ "${_attempt}" -le "${MAX_ATTEMPTS}" ]; do
    _pytest_out="${LOG_DIR}/pytest_ring${_ring_num}_a${_attempt}_${TS_RUN}.log"
    if [ "${_attempt}" -eq 1 ]; then
      invoke_claude "${_ring_num}" "${_ring_name}" "${_test_path}"
    else
      invoke_claude_fix "${_ring_num}" "${_ring_name}" "${_test_path}" "${_attempt}"
    fi

    log_info "Running pytest: ${_test_path} (attempt ${_attempt})"
    if run_ring_test "${_test_path}" "${_pytest_out}"; then
      log_ok "Ring ${_ring_num} GREEN on attempt ${_attempt}"
      lineage_emit "ring_pytest" "ring-${_ring_num}" "green" "attempt=${_attempt} test=${_test_path}"

      if ! commit_ring "${_ring_num}" "${_desc}"; then
        fail_exit "ring-${_ring_num}: git commit failed"
      fi
      _tag="ring${_ring_num}-${_kebab}-v1"
      case "${_ring_num}" in
        7) _tag="ring7-final-cert-v1" ;;
      esac
      if ! tag_ring "${_tag}"; then
        fail_exit "ring-${_ring_num}: git tag ${_tag} failed"
      fi
      lineage_emit "ring_tagged" "ring-${_ring_num}" "ok" "tag=${_tag}"
      log_ok "Ring ${_ring_num} tagged ${_tag}"
      rm -f "${FIX_MD}" 2>/dev/null || true
      return 0
    fi

    log_warn "Ring ${_ring_num} RED on attempt ${_attempt} — writing FIX_REQUEST.md"
    lineage_emit "ring_pytest" "ring-${_ring_num}" "red" "attempt=${_attempt} test=${_test_path}"
    write_fix_request "${_ring_num}" "${_ring_name}" "${_attempt}" "${_test_path}" "${_pytest_out}"
    _attempt=$((_attempt + 1))
  done

  fail_exit "Ring ${_ring_num} (${_ring_name}) failed after ${MAX_ATTEMPTS} attempts — see ${LOG_DIR}"
}

# ---------- Signal helpers ---------------------------------------------------
drop_signal() {
  _name="$1"
  _path="${SIGNALS_DIR}/${_name}"
  _head="$(git_in_repo rev-parse HEAD 2>/dev/null || echo unknown)"
  _ts="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  {
    printf 'signal=%s\n' "${_name}"
    printf 'ts=%s\n'     "${_ts}"
    printf 'head=%s\n'   "${_head}"
    printf 'terminal=T1\n'
  } > "${_path}" 2>/dev/null || fail_exit "cannot drop signal ${_name}"
  log_ok "SIGNAL EMITTED: ${_name} — downstream terminals unblocked"
  lineage_emit "signal_emit" "signals" "ok" "name=${_name} ts=${_ts} head=${_head}"
}

wait_for_signals() {
  _sig1="$1"
  _sig2="$2"
  log_step "Awaiting downstream signals: ${_sig1} AND ${_sig2} (watchdog=${WATCHDOG_SECONDS}s)"
  _start=$(date +%s)
  _last_status=0
  _got1=0
  _got2=0
  while :; do
    _now=$(date +%s)
    _elapsed=$((_now - _start))
    if [ "${_got1}" -eq 0 ] && [ -f "${SIGNALS_DIR}/${_sig1}" ]; then
      _got1=1
      log_ok "received: ${_sig1}"
      lineage_emit "signal_recv" "signals" "ok" "name=${_sig1} elapsed=${_elapsed}s"
    fi
    if [ "${_got2}" -eq 0 ] && [ -f "${SIGNALS_DIR}/${_sig2}" ]; then
      _got2=1
      log_ok "received: ${_sig2}"
      lineage_emit "signal_recv" "signals" "ok" "name=${_sig2} elapsed=${_elapsed}s"
    fi
    if [ "${_got1}" -eq 1 ] && [ "${_got2}" -eq 1 ]; then
      log_ok "both downstream signals received after ${_elapsed}s"
      return 0
    fi
    if [ "${_elapsed}" -ge "${WATCHDOG_SECONDS}" ]; then
      lineage_emit "watchdog" "signals" "error" "elapsed=${_elapsed}s got1=${_got1} got2=${_got2}"
      fail_exit "watchdog timeout awaiting signals (got ${_sig1}=${_got1} ${_sig2}=${_got2})"
    fi
    if [ $((_now - _last_status)) -ge "${STATUS_INTERVAL}" ]; then
      log_info "waiting... elapsed=${_elapsed}s ${_sig1}=${_got1} ${_sig2}=${_got2}"
      _last_status=${_now}
    fi
    sleep "${POLL_INTERVAL}"
  done
}

# ---------- Ring 7 auto-merge verification ----------------------------------
ring7_verify_merges() {
  log_step "Ring 7 merge verification"
  git_in_repo fetch --all --tags --prune || log_warn "git fetch non-zero"
  git_in_repo checkout "${BRANCH_MAIN}" || fail_exit "checkout ${BRANCH_MAIN} failed"
  git_in_repo pull --ff-only origin "${BRANCH_MAIN}" || log_warn "pull non-fatal failure"

  for _tag in ncom-piic-merged-v2 ril-oracle-merged-v2; do
    if ! git_in_repo rev-parse -q --verify "refs/tags/${_tag}" >/dev/null 2>&1; then
      fail_exit "required merge tag missing: ${_tag}"
    fi
    log_ok "merge tag present: ${_tag}"
  done

  for _br in feature/ncom-piic-v2 feature/ril-oracle-v2; do
    if ! git_in_repo branch -a | grep -F "${_br}" >/dev/null 2>&1; then
      fail_exit "required feature branch missing: ${_br}"
    fi
    log_ok "feature branch present: ${_br}"
  done
  lineage_emit "ring7_merges" "ring-7" "ok" "tags_and_branches_verified"
}

ring7_full_suite() {
  log_step "Ring 7: FULL integration suite"
  _full_out="${LOG_DIR}/pytest_full_${TS_RUN}.log"
  if ( cd "${AXIOLEV_RUNTIME}" && python3 -m pytest -q ns/tests/ ) > "${_full_out}" 2>&1; then
    log_ok "full integration suite GREEN"
    lineage_emit "ring7_full_suite" "ring-7" "green" "log=${_full_out}"
    return 0
  fi
  _failed="$(grep -E 'FAILED|ERROR' "${_full_out}" | head -n 40 | tr '\n' ';')"
  lineage_emit "ring7_full_suite" "ring-7" "red" "failed=${_failed}"
  fail_exit "Ring 7 full suite RED — see ${_full_out}"
}

ring7_tag_and_push() {
  log_step "Ring 7: umbrella + founder-grade tag"
  _umbrella="ns-infinity-cqhml+ncom+ril-v1.0.0"
  _founder="ns-infinity-founder-grade-${DATE_TAG}"

  if ! tag_ring "${_umbrella}"; then
    fail_exit "could not apply umbrella tag ${_umbrella}"
  fi
  log_ok "tagged ${_umbrella}"
  lineage_emit "umbrella_tag" "ring-7" "ok" "tag=${_umbrella}"

  if ! tag_ring "${_founder}"; then
    log_warn "could not apply founder-grade tag ${_founder}"
  else
    log_ok "tagged ${_founder}"
    lineage_emit "founder_tag" "ring-7" "ok" "tag=${_founder}"
  fi

  if git_in_repo push origin "${BRANCH_MAIN}" --tags; then
    log_ok "pushed branch + tags"
    lineage_emit "git_push" "ring-7" "ok" "branch=${BRANCH_MAIN}"
  else
    log_warn "git push failed (non-fatal)"
    lineage_emit "git_push" "ring-7" "warn" "push_failed_nonfatal"
  fi
}

# ---------- Return block -----------------------------------------------------
write_return_block() {
  _status="$1"
  _reason="$2"
  _head="$(git_in_repo rev-parse --short HEAD 2>/dev/null || echo unknown)"
  _tags="$(git_in_repo tag --list 2>/dev/null | tr '\n' ' ')"
  _signals_present="$(ls -1 "${SIGNALS_DIR}" 2>/dev/null | tr '\n' ' ')"

  cat > "${RETURN_MD}" <<RET_EOF
# NS∞ Terminal 1 Return Block

- Run timestamp (UTC): ${TS_RUN}
- Final status: ${_status}
- Reason: ${_reason}
- Branch: ${BRANCH_MAIN}
- HEAD: ${_head}
- Attribution: AXIOLEV Holdings LLC © 2026
- Author: axiolevns <axiolevns@axiolev.com>

## Rings

| Ring | Name                                    | Tag                              |
|------|-----------------------------------------|----------------------------------|
| 1    | L1 Constitutional Layer                 | ring1-constitutional-layer-v1    |
| 2    | L5/L6/L7/L8 Substrate                   | ring2-substrate-layers-v1        |
| 3    | L4 The Loom                             | ring3-loom-v1                    |
| 4    | L3 Intake + Canon Promotion Gate        | ring4-canon-promotion-v1         |
| 5    | External Gates (noted)                  | ring5-external-gates-noted-v1    |
| 6    | G₂ 3-form Invariant                     | ring6-g2-invariant-v1            |
| 7    | Final Certification                     | ring7-final-cert-v1              |

## Signals

- emitted by T1:   ring6_complete.signal
- awaited from T2: ncom_piic_complete.signal
- awaited from T3: ril_oracle_complete.signal
- signals present at exit: ${_signals_present}

## Lineage Fabric receipts

- Local (append-only): ${LINEAGE_LOCAL}
- Archive (best-effort): ${LINEAGE_ARCHIVE}
- Main log: ${MAIN_LOG}

## Tags in repo (at exit)

${_tags}

## External gates — pending, noted

- stripe_llc_verification: pending
- stripe_live_keys_vercel: pending
- root_handrail_price_ids: pending
- yubikey_slot2: pending (~\$55 procurement)
- dns_cname_root: pending (root.axiolev.com → root-jade-kappa.vercel.app)

## Next action

- If BUILD_COMPLETE: T4 (CQHML/Manifold) can now run. It awaits the umbrella
  tag ns-infinity-cqhml+ncom+ril-v1.0.0 which this script emits on success.
- If BUILD_FAILED: inspect ${MAIN_LOG} and the most recent pytest log in
  ${LOG_DIR}; re-run after fix.
RET_EOF
  log_info "return block written: ${RETURN_MD}"
}

# ---------- Main -------------------------------------------------------------
main() {
  log_step "NS∞ Terminal 1 Orchestrator v3 — run ${TS_RUN}"
  lineage_emit "t1_boot" "boot" "start" "run=${TS_RUN} repo=${AXIOLEV_RUNTIME}"

  check_prereqs
  check_yubikey 0
  setup_dirs
  ensure_alexandrian_archive_layout
  write_prompt_md

  # Ring 1
  run_ring "1" "L1 Constitutional Layer" "constitutional-layer" \
    "ns/tests/test_ring1_constitutional_layer.py" \
    "L1 constitutional layer + I1-I10 predicates"

  # Ring 2 — substrate (L5/L6/L7/L8)
  run_ring "2" "L5/L6/L7/L8 Substrate" "substrate-layers" \
    "ns/tests/test_ring2_substrate_layers.py" \
    "alexandrian lexicon + state manifold + alexandrian archive + lineage fabric"

  # Ring 3 — Loom
  run_ring "3" "L4 The Loom" "loom" \
    "ns/tests/test_ring3_loom.py" \
    "the loom reflector functor"

  # Ring 4 — Canon promotion gate (YubiKey enforced at preflight)
  run_ring "4" "L3 Intake + Canon Promotion Gate" "canon-promotion" \
    "ns/tests/test_ring4_canon_promotion.py" \
    "canon promotion gate with i4 hardware quorum"

  # Ring 5 — external gates noted
  run_ring "5" "External Gates (noted)" "external-gates-noted" \
    "ns/tests/test_ring5_external_gates_noted.py" \
    "external gates noted (stripe/dns/yubikey pending)"

  # Ring 6 — G₂ 3-form invariant
  run_ring "6" "G2 3-form Invariant" "g2-invariant" \
    "ns/tests/test_ring6_g2_invariant.py" \
    "g2 3-form invariant nabla-phi=0"

  drop_signal "ring6_complete.signal"
  log_ok "SIGNAL EMITTED: ring6_complete — T2 and T3 now unblocked"

  # Wait for both downstream signals before Ring 7 certification.
  wait_for_signals "ncom_piic_complete.signal" "ril_oracle_complete.signal"

  # Ring 7 — final certification
  ring7_verify_merges
  run_ring "7" "Final Certification" "final-cert" \
    "ns/tests/test_ring7_final_cert.py" \
    "final certification record"
  ring7_full_suite
  ring7_tag_and_push

  lineage_emit "t1_complete" "final" "ok" "run=${TS_RUN} branch=${BRANCH_MAIN}"
  write_return_block "BUILD_COMPLETE" "all 7 rings green, umbrella tagged, signals coordinated"
  log_ok "NS∞ BUILD_COMPLETE — founder-grade tag ns-infinity-founder-grade-${DATE_TAG}"
  printf '\n'
  printf '  ----------------------------------------------------------\n'
  printf '  NS∞ Rings 1–7 GREEN. Umbrella tag applied.\n'
  printf '  Feature branch: %s\n' "${BRANCH_MAIN}"
  printf '  Umbrella tag:   ns-infinity-cqhml+ncom+ril-v1.0.0\n'
  printf '  Founder tag:    ns-infinity-founder-grade-%s\n' "${DATE_TAG}"
  printf '  Ready for T4 (CQHML/Manifold).\n'
  printf '  AXIOLEV HOLDINGS LLC — DIGNITY PRESERVED\n'
  printf '  ----------------------------------------------------------\n'
  exit 0
}

main "$@"
