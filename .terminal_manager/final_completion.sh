#!/usr/bin/env bash
# =============================================================================
# NS∞ FINAL COMPLETION — 7-Phase Build-to-Founder-Ready+ Orchestrator
# -----------------------------------------------------------------------------
# AXIOLEV HOLDINGS LLC — DIGNITY PRESERVED
# Owner: Mike Kenworthy · Mead, WA
#
# PURPOSE
#   Single terminal-1 script that runs the 7-phase completion plan end-to-end,
#   honoring the parallel terminal-2 brokerage build via signal handshake.
#   Claude-in-terminal is instructed to CONTINUE until every phase's acceptance
#   criterion is green. Ambiguity fails closed.
#
#   Phase 1 — Re-prove live base organism (boot services + v2 probe pass)
#   Phase 2 — Ring 6 constitutional core (AC-1..AC-7)
#   Phase 3 — Hallucination Doctrine runtime (D-1..D-3 + _violet_llm)
#   Phase 4 — Clearing Layer runtime classes (CL-1)
#   Phase 5 — Living Architecture constitutional UI (UI tiles + live wiring)
#   Phase 6 — Minimal Autopoiesis (compiler + runtime + self-loop + autonarration)
#   Phase 7 — Final truthful certification (single state probe, single deep
#             verifier, single end-to-end proof, single final report)
#
# PARALLEL TRACK (terminal-2, already running its own script)
#   Terminal-2 built whisper_brokerage_residential_starter_v1 in isolated
#   worktree ~/axiolev_runtime_brokerage_wt on feature/brokerage-v1 and is
#   watching for ring6_complete.signal. This script drops that signal at
#   the end of Phase 4 (once the constitutional/doctrine/clearing foundation
#   is structurally in place), so brokerage can land against a Ring 6-complete
#   boot-operational-closure.
#
# HARDWARE GATES (cannot close via software — reported, not blocked on)
#   YK slot_2 (~$55 yubico.com)
#   Ring 5 gates 1–5 (Stripe LLC, live SK, price IDs, DNS CNAME, slot_2)
#
# INVARIANTS HONORED BY THIS SCRIPT
#   - Dignity Kernel read-only (no mutations to DK source)
#   - Violet is projection (UI reads endpoints, never computes truth)
#   - Alexandria append-only (receipts flow, never rewrite)
#   - LLMs never define truth (NER math is pure, force_ground derives from ledger)
#   - Voice loop untouched (voice-loop-v1 tag, /voice/respond, Polly.Matthew,
#     Twilio SID AC9d6c185542b20bf7d1145bc0f2e96028 — zero packets modify)
#   - In-flight work preserved (organism.py, state_api.py, OrganismPage.jsx)
#
# CLAUDE-IN-TERMINAL DIRECTIVES
#   This script emits a manifest and 7 sequential packet prompts. Each packet
#   MUST be executed by Claude Code in bounded scope, with RETURN BLOCK
#   written to ~/axiolev_runtime/.terminal_manager/packets/inbox/. The script
#   gates phase N+1 on phase N's return block being present AND showing
#   acceptance=true. If any phase returns acceptance=false, the script halts
#   and prints the exact residual gap — no false green.
#
# USAGE
#   bash ~/axiolev_runtime/.terminal_manager/final_completion.sh
#
# ENV OVERRIDES
#   STRICT_WAIT=1          # default 1; if 0, prints prompts but does not wait
#   PHASE_TIMEOUT_MIN=180  # per-phase timeout (3h default)
#   SKIP_PHASE=""          # csv of phase numbers to skip (e.g. "1" if already done)
#   NO_AUTOPUSH=1          # default 1; force AUTO_PUSH=false for brokerage merge
# =============================================================================

set -u   # not -e: phase gating is explicit, not via shell errexit

REPO="${REPO:-$HOME/axiolev_runtime}"
ALEX="${ALEX:-/Volumes/NSExternal/ALEXANDRIA}"
TM="$REPO/.terminal_manager"
OUTBOX="$TM/packets/outbox"
INBOX="$TM/packets/inbox"
FINAL_DIR="$TM/final_completion"
SIGNAL_DIR_LOCAL="$TM/signals"
SIGNAL_DIR_ALEX="$ALEX/signals"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
DIGNITY='AXIOLEV HOLDINGS LLC — DIGNITY PRESERVED'
CANON_VERSION="canon-2026.04.16"

STRICT_WAIT="${STRICT_WAIT:-1}"
PHASE_TIMEOUT_MIN="${PHASE_TIMEOUT_MIN:-180}"
SKIP_PHASE="${SKIP_PHASE:-}"
NO_AUTOPUSH="${NO_AUTOPUSH:-1}"

mkdir -p "$OUTBOX" "$INBOX" "$FINAL_DIR" "$SIGNAL_DIR_LOCAL" "$TM/preflight"
[ -d "$ALEX" ] && mkdir -p "$SIGNAL_DIR_ALEX" 2>/dev/null || true

# -------- cosmetic ----------------------------------------------------------
R='\033[0;31m'; G='\033[0;32m'; Y='\033[0;33m'; C='\033[0;36m'
W='\033[1;37m'; M='\033[0;35m'; B='\033[0;34m'; NC='\033[0m'; BOLD='\033[1m'
now()    { date -u +%H:%M:%SZ; }
log()    { printf '[%s] %s\n' "$(now)" "$*"; }
hdr()    { printf '\n%s%s%s\n' "$M$BOLD" "════════════════════════════════════════════════════════════════════════" "$NC"
           printf '%s %s %s\n' "$M$BOLD" "$*" "$NC"
           printf '%s%s%s\n'   "$M$BOLD" "════════════════════════════════════════════════════════════════════════" "$NC"; }
sec()    { printf '\n%s─── %s%s\n' "$C$BOLD" "$*" "$NC"; }
ok()     { printf '%s  [ OK ]%s %s\n' "$G" "$NC" "$*"; }
warn()   { printf '%s  [WARN]%s %s\n' "$Y" "$NC" "$*"; }
fail()   { printf '%s  [FAIL]%s %s\n' "$R" "$NC" "$*"; }
info()   { printf '%s  [INFO]%s %s\n' "$C" "$NC" "$*"; }

skip_phase() {
  local p="$1"
  case ",$SKIP_PHASE," in
    *,"$p",*) return 0 ;;
    *)        return 1 ;;
  esac
}

cat <<BANNER

$M$BOLD╔══════════════════════════════════════════════════════════════════════╗$NC
$M$BOLD║  NS∞ FINAL COMPLETION — 7-Phase Founder-Ready+ Orchestrator        ║$NC
$M$BOLD║  AXIOLEV Holdings LLC · Wyoming · $STAMP            ║$NC
$M$BOLD║  Repo: $REPO                                ║$NC
$M$BOLD║  $DIGNITY                        ║$NC
$M$BOLD╚══════════════════════════════════════════════════════════════════════╝$NC

Phases:
  1 · Re-prove live base organism (boot + v2 probe green)
  2 · Ring 6 constitutional core (AC-1..AC-7)
  3 · Hallucination Doctrine runtime (D-1..D-3 + _violet_llm)
  4 · Clearing Layer runtime classes (CL-1)
       → drop ring6_complete.signal for terminal-2 brokerage auto-merge
  5 · Living Architecture constitutional UI (forces backend truth)
  6 · Minimal Autopoiesis (compiler + runtime + self-loop + narration)
  7 · Final truthful certification (ONE probe, ONE verifier, ONE report)

BANNER

# =============================================================================
# PREFLIGHT
# =============================================================================
hdr "§PF · Preflight"

cd "$REPO" 2>/dev/null || { fail "cannot cd to $REPO"; exit 1; }

# PF-1 in-flight snapshot
INFLIGHT_SNAP="$TM/preflight/inflight_${STAMP}.diff"
INFLIGHT_LIST="$TM/preflight/inflight_${STAMP}.list"
git diff HEAD > "$INFLIGHT_SNAP" 2>/dev/null || true
git status --porcelain > "$INFLIGHT_LIST" 2>/dev/null || true
MOD_COUNT="$(wc -l < "$INFLIGHT_LIST" 2>/dev/null | tr -d ' ')"
info "inflight snapshot: $INFLIGHT_SNAP ($MOD_COUNT lines)"

PRESERVED_FILES=(organism.py OrganismPage.jsx state_api.py)
for f in "${PRESERVED_FILES[@]}"; do
  h="$(find "$REPO" -type f -name "$f" 2>/dev/null | head -1)"
  [ -n "$h" ] && info "preserved in-flight file: $h" || true
done

# PF-2 Docker
if [ -S "$HOME/.docker/run/docker.sock" ] || [ -S "/var/run/docker.sock" ]; then
  ok "Docker socket present"
else
  fail "Docker socket missing — open Docker Desktop before proceeding"
  warn "Phase 1 will block until Docker is up"
fi

# PF-3 Alexandria
if [ -d "$ALEX" ] && [ -w "$ALEX" ]; then ok "Alexandria mounted at $ALEX"; else warn "Alexandria not mounted"; fi

# PF-4 YubiKey slot_1
if command -v ykman >/dev/null 2>&1 && ykman list 2>/dev/null | grep -q "26116460"; then
  ok "YubiKey slot_1 (26116460) present"
else
  warn "YubiKey slot_1 not detected (Ring 6 promotion will fail-closed — correct posture)"
fi

# PF-5 terminal-2 worktree detection
TERMINAL2_WT="$HOME/axiolev_runtime_brokerage_wt"
if [ -d "$TERMINAL2_WT/.git" ] || [ -f "$TERMINAL2_WT/.git" ]; then
  ok "terminal-2 brokerage worktree detected at $TERMINAL2_WT"
  BROKERAGE_PARALLEL=true
else
  warn "terminal-2 brokerage worktree not detected — will still drop signal after Phase 4"
  BROKERAGE_PARALLEL=false
fi

# PF-6 v2 probe present
V2_PROBE="$TM/ns_state_check_v2.sh"
if [ -x "$V2_PROBE" ]; then
  ok "v2 state probe present at $V2_PROBE"
else
  fail "v2 probe MISSING at $V2_PROBE — cannot run Phase 1 or Phase 7 without it"
  fail "  ask terminal-manager for ns_state_check_v2.sh before continuing"
  exit 2
fi

# =============================================================================
# HELPER — wait for return block
# =============================================================================
wait_for_return() {
  local packet_id="$1"
  local timeout_sec=$(( PHASE_TIMEOUT_MIN * 60 ))
  local rb="$INBOX/${packet_id}.return.json"
  local start=$(date -u +%s)
  local elapsed=0

  if [ "$STRICT_WAIT" != "1" ]; then
    info "STRICT_WAIT=0 → not blocking on return block"
    return 0
  fi

  info "waiting for $rb (timeout ${PHASE_TIMEOUT_MIN} min)..."
  while [ ! -f "$rb" ]; do
    sleep 15
    elapsed=$(( $(date -u +%s) - start ))
    if [ "$elapsed" -ge "$timeout_sec" ]; then
      fail "timeout waiting for $rb"
      return 1
    fi
    # heartbeat every 5 min
    if [ $(( elapsed % 300 )) -lt 15 ]; then
      info "… still waiting ($(( elapsed / 60 )) min elapsed)"
    fi
  done
  ok "return block present: $rb"

  # Extract acceptance verdict
  local acc
  acc="$(python3 -c "import json; print(json.load(open('$rb')).get('acceptance','unknown'))" 2>/dev/null || echo "unknown")"
  if [ "$acc" = "True" ] || [ "$acc" = "true" ]; then
    ok "acceptance=true"
    return 0
  else
    fail "acceptance=$acc — phase did NOT close cleanly"
    return 1
  fi
}

# =============================================================================
# PHASE 1 — Re-prove live base organism
# =============================================================================
if ! skip_phase 1; then
  hdr "§Phase 1 · Re-prove live base organism"

  PKT_P1="$OUTBOX/P1_live_reprove_${STAMP}.md"
  cat > "$PKT_P1" <<PKT
# NS∞ PHASE 1 — Re-prove live base organism
# AXIOLEV Holdings LLC — DIGNITY PRESERVED

## STATE FIRST
Repo: $REPO
Branch expected: boot-operational-closure
Baseline claim (04-14 SOTU): LIVE · EXECUTION_ENABLED · 11/11 services
Last v2 probe showed 2/12 services up (postgres+redis only).
In-flight files present — DO NOT clobber: ${PRESERVED_FILES[*]}

## BOUNDED SCOPE
You MAY:
  - docker compose up -d       (from \$REPO)
  - docker compose ps
  - curl http://127.0.0.1:\$port/healthz  (read-only)
  - bash $V2_PROBE
  - read Alexandria boot_receipts.jsonl (read-only)

You MUST NOT:
  - edit any source file
  - commit, tag, push, or run any mutating proof
  - touch organism.py / state_api.py / OrganismPage.jsx
  - invoke /intent/execute with real-world side-effects
  - modify Canon / PolicyBundle / Dignity Kernel

## OBJECTIVE
Restore the live 11/11 baseline AND prove it green via the v2 probe.

Expected service matrix (name:port):
  postgres:5432, redis:6379, ns_core:9000, alexandria:9001,
  model_router:9002, violet:9003, canon:9004, integrity:9005,
  omega:9010, handrail:8011, continuum:8788, state_api:9090

Policy-dominance probes (must pass as in prior SOTU):
  - POST /hic/evaluate with bypass payload → VETO verdict
  - POST /pdp/decide anon canon.promote → DENY verdict
  - POST /api/v1/omega/simulate with allow_promotion:true → HTTP 403

Receipt chain: verify SHA-256 self_hash chain in boot_receipts.jsonl
(v2 probe already does this — you just read the result).

## ACCEPTANCE
Phase 1 closes ONLY when BOTH conditions true:
  a) docker compose ps shows 11/11 (or 12/12 including state_api) healthy
  b) v2 probe return block has:
       live_services.live_count >= 11
       voice_loop.respond_route == true
       voice_loop.inbound_route == true
       voice_loop.polly_matthew == true
       voice_loop.twilio_sid_present == true

If a) or b) fails, DO NOT mark acceptance=true. Report the specific
service/endpoint that did not come up.

## RETURN BLOCK (write to $INBOX/P1_live_reprove.return.json)
{
  "return_block_version": 2,
  "phase": 1,
  "phase_name": "live_reprove",
  "acceptance": <true|false>,
  "services_up": <int>,
  "services_expected": 11,
  "v2_probe_report_json": "<path>",
  "hic_veto_confirmed": <bool>,
  "pdp_deny_confirmed": <bool>,
  "omega_advisory_confirmed": <bool>,
  "voice_loop_intact": <bool>,
  "receipt_chain_valid": <bool>,
  "residual_gaps": [ "<anything not yet green>" ],
  "dignity_banner": "$DIGNITY"
}

## COMPRESSION FIRST. No narration. Run, probe, return.
PKT
  ok "Phase 1 packet written: $PKT_P1"
  info "Operator: dispatch this packet to a Claude Code terminal now."
  wait_for_return "P1_live_reprove" || { fail "Phase 1 did not close — halting"; exit 10; }
  ok "Phase 1 ACCEPTED"
else
  warn "Phase 1 SKIPPED (SKIP_PHASE)"
fi

# =============================================================================
# PHASE 2 — Ring 6 constitutional core
# =============================================================================
if ! skip_phase 2; then
  hdr "§Phase 2 · Ring 6 constitutional core"

  PKT_P2="$OUTBOX/P2_ring6_${STAMP}.md"
  cat > "$PKT_P2" <<PKT
# NS∞ PHASE 2 — Ring 6 Constitutional Core
# AXIOLEV Holdings LLC — DIGNITY PRESERVED

## STATE FIRST
Phase 1 closed green (11/11 services, live baseline proved).
Canon: $CANON_VERSION (this phase DRAFTS Canon; G5 ratification is separate).
Source spec: AXIOLEV_NS_Integration_Spec_Ring6.pdf §§1–9.
Hardware gate: YubiKey slot_2 PENDING — promotion endpoint must return
423 Locked on operator-initiated promotion until slot_2 lands (correct
fail-closed posture).

## BOUNDED SCOPE
Create ONLY:
  canon/axioms/ax_core.json                # AX-1..AX-14
  canon/core_policy/.gitkeep
  canon/adaptive/.gitkeep
  canon/promotions/.gitkeep
  pi/__init__.py
  pi/check.py                              # service entrypoint
  pi/stages/__init__.py
  pi/stages/s1_consistency.py              # A ∪ B ∪ candidate ⊬ ⊥
  pi/stages/s2_dignity.py                  # AX-5 never-event check
  pi/stages/s3_evidence.py                 # AX-1 provenance check
  pi/stages/s4_quarantine.py               # AX-8 tag-mutation check
  pi/stages/s5_authority.py                # AX-2 kind-transition check
  pi/stages/s6_replay.py                   # AX-11 receipt dry-run
  pi/stages/s7_typed_lane.py               # AX-10 lane-registration check
  pi/stages/s8_sentinel.py                 # AX-12 meta-governance advisory
  pi/endpoints.py                          # /pi/check, /canon/promote
  pi/receipts.py                           # AdmissibilityReceipt, etc.
  ns_core/ns_resume.py                     # /ns/resume + StateManifest
  resume_ns.sh                             # AX-13 resume protocol
  scripts/axiolev_push.sh                  # AC-7 dignity IP push
  scripts/file_header_check.sh             # header compliance scan
  tests/pi/never_events/__init__.py
  tests/pi/never_events/ax5_dignity_veto.py
  tests/pi/never_events/ax1_evidence_required.py
  tests/pi/never_events/ax8_quarantine.py
  tests/pi/never_events/ax2_authority.py
  tests/pi/never_events/ax10_typed_lane.py
  tests/pi/never_events/ax11_replayable.py
  tests/pi/test_pi_check_fail_closed.py
  tests/pi/test_canon_promote_rejects.py
  tests/pi/test_ns_resume_canon_drift.py

MUST NOT touch:
  Dignity Kernel · ns_core/isr/* (Phase 3) · cps/lanes/* (Phase 3)
  ns_core/clearing/* (Phase 4) · ns_ui/* (Phase 5)
  organism.py · state_api.py · OrganismPage.jsx · voice loop

## OBJECTIVE
Land AC-1..AC-7. Π is fail-closed; any ambiguity → 403 FailClosedDenial.
/canon/promote enforces quorum; slot_2 returns 423 Locked.
/ns/resume refuses canon_head mismatch.

## ENDPOINTS
POST /pi/check → AdmissibilityReceipt | 403 FailClosedDenial | 503
POST /canon/promote → PromotionReceipt | 403 | 409
POST /ns/resume → 200 {manifest,programs_restored} | 409 canon_drift

## TESTS
pytest tests/pi/ -q          # AC-2, AC-3, AC-6
bash scripts/file_header_check.sh  # AC-7

## COMMIT / TAG
headline: "NS∞ | Ring 6 constitutional scaffold — AC-1..AC-7"
Tag: ns-infinity-ring6-v1.0.0
Push: bash scripts/axiolev_push.sh --tag ns-infinity-ring6-v1.0.0

## ACCEPTANCE
All AC-1..AC-7 green. All 9 never-event vectors return 403.

## RETURN BLOCK ($INBOX/P2_ring6.return.json)
{ "return_block_version":2, "phase":2, "phase_name":"ring6",
  "acceptance": <bool>,
  "files_written": [...], "commits":[...], "tags":["ns-infinity-ring6-v1.0.0"],
  "ac_gates": { "AC_1":<bool>, "AC_2":<bool>, "AC_3":<bool>,
                "AC_4":<bool>, "AC_5":<bool>, "AC_6":<bool>, "AC_7":<bool> },
  "never_events_403": <int>, "dignity_banner": "$DIGNITY" }

## COMPRESSION FIRST.
PKT
  ok "Phase 2 packet: $PKT_P2"
  wait_for_return "P2_ring6" || { fail "Phase 2 did not close — halting"; exit 20; }
  ok "Phase 2 ACCEPTED"
else
  warn "Phase 2 SKIPPED"
fi

# =============================================================================
# PHASE 3 — Hallucination Doctrine runtime + _violet_llm
# =============================================================================
if ! skip_phase 3; then
  hdr "§Phase 3 · Hallucination Doctrine runtime + _violet_llm"

  PKT_P3="$OUTBOX/P3_doctrine_${STAMP}.md"
  cat > "$PKT_P3" <<PKT
# NS∞ PHASE 3 — Hallucination Doctrine + _violet_llm
# AXIOLEV Holdings LLC — DIGNITY PRESERVED

## STATE FIRST
Phase 2 closed. Ring 6 Canon + Π live.
Source spec: NS_Infinity_Hallucination_Doctrine.pdf (NER, force_ground, doctrine).

## BOUNDED SCOPE
Create ONLY:
  ns_core/isr/__init__.py
  ns_core/isr/ner.py                    # pure math, no LLM calls
  ns_core/isr/ner_aggregator.py         # rolling window W=128
  ns_core/isr/ner_endpoints.py          # GET /isr/ner
  ns_core/cps/lanes/__init__.py
  ns_core/cps/lanes/force_ground.py
  ns_core/cps/lanes/force_ground_runner.py
  ns_core/cps/lanes/force_ground_endpoints.py
  ns_core/cps/lanes/force_ground_dispatch.py
  ns_core/cps/spike/__init__.py
  ns_core/cps/spike/evidence_spike.py   # deterministic replay
  ns_core/cps/spike/spike_evaluator.py
  ns_core/violet/_violet_llm.py
  ns_core/violet/providers/{groq,grok,ollama,anthropic,openai,canned}.py
  ns_core/tests/isr/test_ner_math.py
  ns_core/tests/isr/test_ner_window.py
  ns_core/tests/isr/test_ner_breach_receipt.py
  ns_core/tests/isr/test_ner_determinism.py
  ns_core/tests/violet/test_fallback_chain.py
  proofs/ner/ner_determinism_1000.py
  proofs/ner/ner_breach_alexandria_integrity.py
  proofs/force_ground/spike_determinism.py
  proofs/force_ground/dispatch_table_coverage.py
  proofs/force_ground/lock_mutex_safety.py
  proofs/force_ground/append_only_invariant.py
  proofs/force_ground/yubikey_quorum_gate.py
  docs/canon/HALLUCINATION_DOCTRINE.md  # DRAFT-FOR-G5
  docs/canon/_amendments/2026-04-17-hallucination-doctrine.md

MUST NOT touch:
  Dignity Kernel · Canon · PolicyBundle · ABI schema
  ns_core/clearing/* (Phase 4) · ns_ui/* (Phase 5)
  organism.py · state_api.py · OrganismPage.jsx · voice loop

## OBJECTIVE
NER math: (N + κ_o·O + κ_r·R) / max(A, A_floor)  κ_o=256, κ_r=512, A_floor=64
Bands: green ≤1.0 < yellow ≤2.5 < orange ≤5.0 < red
force_ground dispatch: ε≤0.01 GROUND_OK | 0.01<ε≤0.25 PRUNE | else CANON_GAP
Mutex lock: $TM/locks/force_ground.lock
Auto-invoke: NER red sustained ≥8 cycles OR adjudicator deadlock ≥3
Abort: slot_1 + slot_2 quorum → 423 until slot_2 hardware
_violet_llm: Groq→Grok→Ollama→Anthropic→OpenAI→canned; emits spans
for NER to observe (NO NER→LLM coupling — math is pure)

## TESTS
pytest ns_core/tests/isr/ -q               # NER
pytest ns_core/tests/violet/ -q            # fallback chain
python proofs/ner/ner_determinism_1000.py  # 1000/1000 bit-identical
python proofs/force_ground/spike_determinism.py  # 1000/1000

## COMMITS / TAGS (3 commits, 3 tags)
"NS∞ | NER observable — initial land"         → ns-infinity-ner-v1.0.0
"NS∞ | force_ground CPS lane — initial land"  → ns-infinity-force-ground-v1.0.0
"NS∞ | _violet_llm fallback chain"            → ns-infinity-violet-llm-v1.0.0
"NS∞ | HALLUCINATION_DOCTRINE.md DRAFT-FOR-G5" → ns-infinity-doctrine-hallucination-v1.0.0-draft

## ACCEPTANCE
D-1, D-2, D-3 green. Determinism 1000/1000 for both NER + spike.
_violet_llm present with 6 providers. Voice loop regression: ZERO.

## RETURN BLOCK ($INBOX/P3_doctrine.return.json)
{ "return_block_version":2, "phase":3, "phase_name":"doctrine",
  "acceptance":<bool>, "d1_ner":<bool>, "d2_force_ground":<bool>,
  "d3_doctrine_md":<bool>, "violet_llm":<bool>,
  "determinism_ner_1000":<bool>, "determinism_spike_1000":<bool>,
  "voice_loop_regressed":<bool>,
  "commits":[...], "tags":[...], "dignity_banner":"$DIGNITY" }

## COMPRESSION FIRST.
PKT
  ok "Phase 3 packet: $PKT_P3"
  wait_for_return "P3_doctrine" || { fail "Phase 3 did not close — halting"; exit 30; }
  ok "Phase 3 ACCEPTED"
else
  warn "Phase 3 SKIPPED"
fi

# =============================================================================
# PHASE 4 — Clearing Layer runtime
# =============================================================================
if ! skip_phase 4; then
  hdr "§Phase 4 · Clearing Layer runtime classes"

  PKT_P4="$OUTBOX/P4_clearing_${STAMP}.md"
  cat > "$PKT_P4" <<PKT
# NS∞ PHASE 4 — Clearing Layer Runtime (CL-1)
# AXIOLEV Holdings LLC — DIGNITY PRESERVED

## STATE FIRST
Phase 3 closed. NER + force_ground + doctrine live.
Source spec: Clearing_layer_integration.pdf §Core Mechanisms + CI-1..CI-5.
CI tokens already in repo; this phase lands the runtime-enforceable classes.

## BOUNDED SCOPE
Create ONLY:
  ns_core/clearing/__init__.py
  ns_core/clearing/disclosure_window.py      # CI-2
  ns_core/clearing/ambiguity_retention.py    # CI-4
  ns_core/clearing/withhold_protocol.py      # CI-5
  ns_core/clearing/non_compression_zones.py  # CI-3
  ns_core/clearing/non_totalization.py       # CI-1
  ns_core/clearing/endpoints.py              # GET /clearing/state
  ns_core/tests/clearing/test_disclosure_window.py
  ns_core/tests/clearing/test_ambiguity_buffer.py
  ns_core/tests/clearing/test_withhold_reject.py
  ns_core/tests/clearing/test_non_compression.py
  ns_core/tests/clearing/test_non_totalization.py

MUST NOT touch:
  Dignity Kernel · Canon · any Phase 2/3 file
  ns_ui/* (Phase 5) · organism.py · state_api.py · OrganismPage.jsx
  voice loop

## OBJECTIVE
Runtime-enforceable classes that AFFECT BEHAVIOR (not just tokens):
  - DisclosureWindow: hold-phase buffer; emits disclosure_ready event
  - AmbiguityRetention: N-best + confidence distribution storage
  - WithholdProtocol: threshold-gated abstention; returns explicit
    "insufficient clarity" with reason codes
  - NonCompressionZones: tag-based bypass of summarization
  - NonTotalization: hard-cap on "complete" claims; annotates scope

Each class must have a unit test that demonstrates behavioral effect,
not just instantiation. Integration point: Π admissibility engine (from
Phase 2) consults WithholdProtocol before returning 200 — if ambiguity
retained, returns with "abstention" field populated.

## TESTS
pytest ns_core/tests/clearing/ -q

## COMMIT / TAG
headline: "NS∞ | Clearing Layer runtime classes — CI-1..CI-5 embodied"
Tag: ns-infinity-clearing-v1.0.0

## ACCEPTANCE
CL-1 green. All 5 CI classes present with behavioral unit tests passing.
Π integration: /pi/check now returns abstention field when invoked with
low-confidence candidate.

## RETURN BLOCK ($INBOX/P4_clearing.return.json)
{ "return_block_version":2, "phase":4, "phase_name":"clearing",
  "acceptance":<bool>,
  "ci_classes": {"CI_1":<bool>,"CI_2":<bool>,"CI_3":<bool>,"CI_4":<bool>,"CI_5":<bool>},
  "pi_abstention_integration":<bool>,
  "tests_passed":<int>, "tests_failed":<int>,
  "commits":[...], "tags":["ns-infinity-clearing-v1.0.0"],
  "dignity_banner":"$DIGNITY" }

## COMPRESSION FIRST.
PKT
  ok "Phase 4 packet: $PKT_P4"
  wait_for_return "P4_clearing" || { fail "Phase 4 did not close — halting"; exit 40; }
  ok "Phase 4 ACCEPTED"

  # ---- DROP RING6_COMPLETE SIGNAL for terminal-2 brokerage auto-merge ----
  sec "§Phase 4.5 · Dropping ring6_complete signal for terminal-2"

  cd "$REPO"
  TARGET_SHA="$(git rev-parse boot-operational-closure 2>/dev/null || git rev-parse HEAD)"
  TARGET_BRANCH="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo '?')"
  SIG_TIMESTAMP="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

  SIGNAL_BODY="# NS∞ Ring 6 completion signal
# AXIOLEV HOLDINGS LLC — DIGNITY PRESERVED
TIMESTAMP=$SIG_TIMESTAMP
TARGET_SHA=$TARGET_SHA
TARGET_BRANCH=$TARGET_BRANCH
RING6_PACKETS=P2,P3,P4
UI_TILES=pending_phase_5
NOTES=ring6_doctrine_clearing_landed_ui_pending"

  LOCAL_SIG="$SIGNAL_DIR_LOCAL/ring6_complete.signal"
  echo "$SIGNAL_BODY" > "$LOCAL_SIG"
  ok "signal written: $LOCAL_SIG"

  if [ -d "$SIGNAL_DIR_ALEX" ]; then
    ALEX_SIG="$SIGNAL_DIR_ALEX/ring6_complete.signal"
    echo "$SIGNAL_BODY" > "$ALEX_SIG" 2>/dev/null && ok "signal mirrored: $ALEX_SIG" || warn "could not mirror to Alexandria"
  fi

  info "terminal-2 brokerage watcher will detect within ~15s and auto-merge"
  info "to CANCEL the merge: rm $LOCAL_SIG $ALEX_SIG (quickly)"
else
  warn "Phase 4 SKIPPED — signal not dropped"
fi

# =============================================================================
# PHASE 5 — Living Architecture constitutional UI
# =============================================================================
if ! skip_phase 5; then
  hdr "§Phase 5 · Living Architecture Constitutional UI"

  PKT_P5="$OUTBOX/P5_ui_${STAMP}.md"
  cat > "$PKT_P5" <<PKT
# NS∞ PHASE 5 — Living Architecture Constitutional UI
# AXIOLEV Holdings LLC — DIGNITY PRESERVED

## STATE FIRST
Phase 4 closed. Backend Ring 6 + Doctrine + Clearing live.
Principle: UI is a FORCING FUNCTION for truth. A tile cannot truthfully
display a state unless the backend provides it. If a tile would lie,
refuse to render.

## BOUNDED SCOPE
Create ONLY:
  ns_ui/violet_panel/__init__.tsx
  ns_ui/violet_panel/index.tsx
  ns_ui/violet_panel/components/NERTile.tsx            ← GET /isr/ner
  ns_ui/violet_panel/components/ForceGroundBanner.tsx  ← GET /cps/force_ground/history
  ns_ui/violet_panel/components/ClearingTile.tsx       ← GET /clearing/state
  ns_ui/violet_panel/components/InvariantsTile.tsx     ← /violet/invariants (9/10)
  ns_ui/violet_panel/components/ReceiptChainTile.tsx   ← /integrity/chain
  ns_ui/violet_panel/components/CanonPendingTile.tsx   ← /canon/pending_promotions
  ns_ui/violet_panel/components/AbstentionTile.tsx     ← /clearing/withheld
  ns_ui/violet_panel/hooks/useNER.ts
  ns_ui/violet_panel/hooks/useForceGround.ts
  ns_ui/violet_panel/hooks/useClearingState.ts
  ns_ui/violet_panel/hooks/useCanonPending.ts

MUST NOT touch:
  Any existing page under ns_ui/src/pages/* (OrganismPage.jsx is in-flight)
  Any backend file
  organism.py · state_api.py
  voice loop

## OBJECTIVE
Each tile exposes EXACTLY what the constitutional surface must show:
  NERTile           → live band + breach streak + last receipt CID
  ForceGroundBanner → last invocation kind + dispatch outcome + ack state
  ClearingTile      → disclosure-window hold count + abstention rate +
                      ambiguity-index + withheld reasons
  InvariantsTile    → 10 invariants with live status (9/10 expected)
  ReceiptChainTile  → head CID + chain length + integrity=ok
  CanonPendingTile  → pending G_INTENT receipts awaiting ratification
  AbstentionTile    → what the system is currently refusing to answer and why

No tile may compute state locally. No localStorage. No LLM calls from UI.
If any endpoint returns non-200, tile renders "data unavailable" — never
fabricates. This is the projection invariant made visible.

## TESTS
npm run test (React Testing Library):
  - each tile renders empty-state correctly on 503
  - no tile accepts a localStorage import
  - no tile includes useState with server-derived booleans

## COMMIT / TAG
headline: "NS∞ | VioletPanel Constitutional Surface — 7 tiles"
Tag: ns-infinity-violet-panel-v1.0.0

## ACCEPTANCE
UI gate green. All 7 tiles present, wired to real endpoints, refuse to
fabricate on endpoint failure. Build artifacts exist in ns_ui/.next
or ns_ui/dist.

## RETURN BLOCK ($INBOX/P5_ui.return.json)
{ "return_block_version":2, "phase":5, "phase_name":"ui",
  "acceptance":<bool>,
  "tiles_present":{ "NERTile":<bool>,"ForceGroundBanner":<bool>,
                    "ClearingTile":<bool>,"InvariantsTile":<bool>,
                    "ReceiptChainTile":<bool>,"CanonPendingTile":<bool>,
                    "AbstentionTile":<bool> },
  "build_succeeded":<bool>,
  "projection_invariant_preserved":<bool>,
  "organism_page_untouched":<bool>,
  "tags":["ns-infinity-violet-panel-v1.0.0"],
  "dignity_banner":"$DIGNITY" }

## COMPRESSION FIRST.
PKT
  ok "Phase 5 packet: $PKT_P5"
  wait_for_return "P5_ui" || { fail "Phase 5 did not close — halting"; exit 50; }
  ok "Phase 5 ACCEPTED"
else
  warn "Phase 5 SKIPPED"
fi

# =============================================================================
# PHASE 6 — Minimal Autopoiesis
# =============================================================================
if ! skip_phase 6; then
  hdr "§Phase 6 · Minimal Autopoiesis"

  PKT_P6="$OUTBOX/P6_autopoiesis_${STAMP}.md"
  cat > "$PKT_P6" <<PKT
# NS∞ PHASE 6 — Minimal Autopoiesis
# AXIOLEV Holdings LLC — DIGNITY PRESERVED

## STATE FIRST
Phase 5 closed. Backend + UI constitutional surfaces live.
Principle: MINIMAL real metabolism, not theatrical grand autopoiesis.
  doc → program object → runtime tracking → update-on-receipt → visible.

## BOUNDED SCOPE
Create ONLY:
  ns_core/autopoiesis/__init__.py
  ns_core/autopoiesis/document_to_program_compiler.py
  ns_core/autopoiesis/program_runtime.py
  ns_core/autopoiesis/strategic_initiative.py
  ns_core/autopoiesis/autonarration.py          # morning-briefing feed
  ns_core/autopoiesis/b_adaptive.py             # candidate policy store
  ns_core/autopoiesis/promotion_candidate.py
  ns_core/autopoiesis/self_modify.py            # gated via Π from Phase 2
  ns_core/autopoiesis/endpoints.py
  ns_core/tests/autopoiesis/test_compiler_roundtrip.py
  ns_core/tests/autopoiesis/test_program_runtime_bounded.py
  ns_core/tests/autopoiesis/test_self_modify_gated.py
  ns_core/tests/autopoiesis/test_autonarration.py

INTEGRATION GUARD — READ organism.py FIRST:
  If organism.py exports StrategicInitiative or ProgramRuntime symbols,
  IMPORT from it rather than redefining. Emit "inflight_imports" in the
  return block listing any symbols consumed from organism.py.

MUST NOT touch:
  organism.py (READ ONLY; may import from it if compatible)
  state_api.py · OrganismPage.jsx · Canon · Dignity Kernel
  voice loop

## OBJECTIVE
Seed 5 StrategicInitiative / ProgramRuntime pairs (Symphony spec):
  Symphony IP, Licensing, Product, Recruiting, GTM
Document-to-Program compiler: parses strategy PDFs → typed objects
  (entities, patents, components, phases, actions).
Autonarration: morning-briefing feed from Alexandria receipt stream.
Self-modify: B_adaptive candidates flow through Π admissibility BEFORE
  any promotion — autopoietic loop is fail-closed.

## ENDPOINTS
POST /autopoiesis/compile          → doc_id → program graph
GET  /autopoiesis/programs         → 5 StrategicInitiatives
GET  /autopoiesis/briefing         → morning autonarration
POST /autopoiesis/propose_adaptive → B_adaptive → Π → G_INTENT receipt

## TESTS
pytest ns_core/tests/autopoiesis/ -q
  - compiler_roundtrip: markdown → program graph → markdown reproduces
  - program_runtime_bounded: no recursion depth > 10, no unbounded state
  - self_modify_gated: every proposed adaptation invokes /pi/check
  - autonarration: briefing derives ONLY from ledger receipts

## COMMIT / TAG
headline: "NS∞ | Minimal Autopoiesis — compiler + runtime + self-loop"
Tag: ns-infinity-autopoiesis-v1.0.0

## ACCEPTANCE
AP green. 5 programs seeded. Self-loop gated through Π (not freehand).
Autonarration surface reads ledger only (no LLM fabrication).

## RETURN BLOCK ($INBOX/P6_autopoiesis.return.json)
{ "return_block_version":2, "phase":6, "phase_name":"autopoiesis",
  "acceptance":<bool>,
  "compiler":<bool>, "program_runtime":<bool>,
  "programs_seeded":<int>, "autonarration":<bool>, "self_loop_gated":<bool>,
  "inflight_imports":[...],  "tags":["ns-infinity-autopoiesis-v1.0.0"],
  "dignity_banner":"$DIGNITY" }

## COMPRESSION FIRST.
PKT
  ok "Phase 6 packet: $PKT_P6"
  wait_for_return "P6_autopoiesis" || { fail "Phase 6 did not close — halting"; exit 60; }
  ok "Phase 6 ACCEPTED"
else
  warn "Phase 6 SKIPPED"
fi

# =============================================================================
# PHASE 7 — Final Truthful Certification
# =============================================================================
if ! skip_phase 7; then
  hdr "§Phase 7 · Final Truthful Certification"

  PKT_P7="$OUTBOX/P7_final_cert_${STAMP}.md"
  cat > "$PKT_P7" <<PKT
# NS∞ PHASE 7 — Final Truthful Certification
# AXIOLEV Holdings LLC — DIGNITY PRESERVED

## STATE FIRST
Phases 1–6 closed. Base organism live, Ring 6 + Doctrine + Clearing + UI +
Autopoiesis landed. Brokerage feature/brokerage-v1 may have auto-merged
(terminal-2 signal-driven — verify via brokerage-v1-merged tag).

PRINCIPLE: stop letting closure scripts be the source of truth.
  ONE state probe.
  ONE deep verifier.
  ONE end-to-end proof.
  ONE final report.

## BOUNDED SCOPE
You MAY:
  - bash $V2_PROBE                                (v2 state probe)
  - bash NS_RIGHT_DEEP_VERIFY.sh                  (existing deep verifier)
  - curl localhost endpoints (read-only)
  - read Alexandria receipts
  - write final report to /Volumes/NSExternal/ALEXANDRIA/state_checks/
  - write tag: ns-infinity-founder-ready-plus-v1.0.0 (only if all acceptance green)

You MUST NOT:
  - write any new source code
  - modify any prior commit
  - push without operator confirmation

## OBJECTIVE
Produce THE authoritative final report. Diff live state against
Founder-Ready+ acceptance matrix from all 7 phases. Emit one JSON +
one markdown. Tag HEAD only if every cell is green.

## ACCEPTANCE MATRIX (must all be true)
Live baseline:
  - services.up >= 11
  - hic_veto_confirmed
  - pdp_deny_confirmed
  - omega_advisory_confirmed
  - voice_loop.{respond,inbound,polly_matthew,twilio_sid}

Ring 6 (AC-1..AC-7):
  - canon/axioms/ax_core.json (14 axioms)
  - pi/ engine + /pi/check live
  - /canon/promote live, fail-closed on quorum
  - /ns/resume live, fail-closed on canon_drift
  - tests/pi/never_events/ corpus passes
  - resume_ns.sh + scripts/axiolev_push.sh present
  - AXIOLEV-FILE-HEADER on all new .py

Doctrine (D-1..D-3):
  - ns_core/isr/ner.py + /isr/ner live
  - cps/lanes/force_ground.py + /cps/force_ground/invoke live
  - docs/canon/HALLUCINATION_DOCTRINE.md committed
  - NER determinism 1000/1000
  - force_ground spike determinism 1000/1000

Clearing (CL-1):
  - 5 CI classes with behavioral tests
  - Π integration — /pi/check abstention field live

UI:
  - violet_panel/ with 7 tiles
  - Build artifacts in ns_ui/.next or ns_ui/dist
  - Projection invariant preserved (no tile computes truth)

Autopoiesis:
  - compiler + ProgramRuntime + self-loop present
  - 5 StrategicInitiatives seeded
  - Self-loop gated via Π
  - Autonarration surface reads ledger only

Brokerage parallel track (terminal-2):
  - feature/brokerage-v1 merged OR still in build (OK either way)
  - If merged: brokerage-v1-merged tag present
  - If merged: brokerage post-merge smoke tests passed

In-flight preserved:
  - organism.py / state_api.py / OrganismPage.jsx still exist,
    content unchanged from pre-dispatch snapshot

Voice loop regression:
  - ZERO changes to /voice/respond, /voice/inbound, Polly.Matthew,
    Twilio SID AC9d6c185542b20bf7d1145bc0f2e96028
  - voice-loop-v1 tag still reachable

Hardware gates (REPORTED, not blocked on):
  - YK slot_2 pending
  - Ring 5 gates 1–5 pending

## OUTPUTS (exactly 3 files)
  $ALEX/state_checks/FOUNDER_READY_PLUS_${STAMP}.md
  $ALEX/state_checks/FOUNDER_READY_PLUS_${STAMP}.json
  $TM/final_completion/verdict_${STAMP}.txt   (one line: "✅ GREEN" or "🟡 PARTIAL" or "❌ BLOCKED")

## TAG (conditional)
IF every acceptance cell above is true:
  git tag -a ns-infinity-founder-ready-plus-v1.0.0 \
    -m "Founder-Ready+ sealed $STAMP. All 7 phases green. Hardware gates open: slot_2, Ring 5. \$DIGNITY"
  bash scripts/axiolev_push.sh --tag ns-infinity-founder-ready-plus-v1.0.0
ELSE:
  Do NOT tag. Emit verdict=🟡 PARTIAL or ❌ BLOCKED with exact residual list.

## RETURN BLOCK ($INBOX/P7_final_cert.return.json)
{ "return_block_version":2, "phase":7, "phase_name":"final_cert",
  "acceptance":<bool>,
  "verdict":"<GREEN|PARTIAL|BLOCKED>",
  "matrix":{
    "live_baseline":<bool>, "ring6":<bool>, "doctrine":<bool>,
    "clearing":<bool>, "ui":<bool>, "autopoiesis":<bool>,
    "brokerage_track":<bool>, "inflight_preserved":<bool>,
    "voice_loop_no_regression":<bool>
  },
  "hardware_gates_open":["YK_slot_2","Ring_5_gate_1","Ring_5_gate_2",
                          "Ring_5_gate_3","Ring_5_gate_4","Ring_5_gate_5"],
  "residual_gaps":[...],
  "final_report_md":"<path>",
  "final_report_json":"<path>",
  "final_tag":"<tag or null>",
  "dignity_banner":"$DIGNITY" }

## COMPRESSION FIRST.
PKT
  ok "Phase 7 packet: $PKT_P7"
  wait_for_return "P7_final_cert" || { fail "Phase 7 did not close — halting"; exit 70; }
  ok "Phase 7 ACCEPTED — reading verdict"

  VERDICT="$(python3 -c "import json; print(json.load(open('$INBOX/P7_final_cert.return.json')).get('verdict','UNKNOWN'))" 2>/dev/null || echo UNKNOWN)"
  FINAL_TAG="$(python3 -c "import json; print(json.load(open('$INBOX/P7_final_cert.return.json')).get('final_tag') or '')" 2>/dev/null || echo "")"

  case "$VERDICT" in
    "GREEN"|"✅ GREEN")
      ok "FOUNDER-READY+ ACHIEVED"
      [ -n "$FINAL_TAG" ] && ok "final tag: $FINAL_TAG"
      ;;
    *)
      warn "verdict: $VERDICT — residual gaps remain; see P7 return block"
      ;;
  esac
else
  warn "Phase 7 SKIPPED — no final verdict"
fi

# =============================================================================
# FINAL SUMMARY
# =============================================================================
hdr "§FINAL SUMMARY"

# Collect tallies
SUMMARY_JSON="$FINAL_DIR/summary_${STAMP}.json"
{
  echo "{"
  echo "  \"stamp\": \"$STAMP\","
  echo "  \"repo\": \"$REPO\","
  echo "  \"phases\": {"
  first=1
  for p in 1 2 3 4 5 6 7; do
    case "$p" in
      1) key="P1_live_reprove" ;;
      2) key="P2_ring6" ;;
      3) key="P3_doctrine" ;;
      4) key="P4_clearing" ;;
      5) key="P5_ui" ;;
      6) key="P6_autopoiesis" ;;
      7) key="P7_final_cert" ;;
    esac
    rb="$INBOX/${key}.return.json"
    if [ -f "$rb" ]; then
      acc="$(python3 -c "import json; print(json.load(open('$rb')).get('acceptance','?'))" 2>/dev/null || echo "?")"
    elif skip_phase "$p"; then
      acc="skipped"
    else
      acc="not_run"
    fi
    [ "$first" = "1" ] && first=0 || echo ","
    printf "    \"phase_%s\": \"%s\"" "$p" "$acc"
  done
  echo ""
  echo "  },"
  echo "  \"brokerage_return\": \"$INBOX/02_brokerage_full.return.json\","
  echo "  \"final_verdict\": \"${VERDICT:-not_reached}\","
  echo "  \"final_tag\": \"${FINAL_TAG:-}\","
  echo "  \"hardware_gates_open\": [\"YK_slot_2\",\"Ring_5_gates_1..5\"],"
  echo "  \"dignity_banner\": \"$DIGNITY\""
  echo "}"
} > "$SUMMARY_JSON"

ok "summary: $SUMMARY_JSON"
cat "$SUMMARY_JSON"

echo ""
echo "$M$BOLD════════════════════════════════════════════════════════════════════════$NC"
echo "$M$BOLD $DIGNITY $NC"
echo "$M$BOLD════════════════════════════════════════════════════════════════════════$NC"
