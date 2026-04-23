"""State Manifold transition registry — 100% classification coverage.

Every state transition across the NS∞ State Manifold is enumerated and
classified as Reversible, Bounded-Irreversible, or Irreversible.

Sources:
  voice     — services/ns_core/voice_state_machine.py :: VALID_TRANSITIONS
  program   — services/ns_core/program_runtime/runtime.py :: VALID_TRANSITIONS
  narrative — services/ns_core/narrative/buffer.py :: NarrativeObject.advance_state
  tier      — services/continuum/src/tier.py :: TierLatch
  continuum — services/continuum/src/store.py :: AppendOnlyStore
  receipt   — services/ns/nss/core/receipts.py :: ReceiptChain.emit
  calibration — services/calibration/pipeline.py :: CalibrationDecision bands
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class Kind(str, Enum):
    REVERSIBLE = "reversible"
    BOUNDED_IRREVERSIBLE = "bounded_irreversible"
    IRREVERSIBLE = "irreversible"


@dataclass(frozen=True)
class StateTransition:
    op_id: str
    domain: str
    from_state: str
    to_state: str
    kind: Kind
    justification: str
    compensating_action: Optional[str] = None
    bounded_budget: Optional[str] = None

    def __post_init__(self) -> None:
        if self.kind != Kind.REVERSIBLE and not self.compensating_action:
            raise ValueError(
                f"Non-reversible transition {self.op_id!r} requires compensating_action"
            )


def _t(
    op_id: str,
    domain: str,
    from_state: str,
    to_state: str,
    kind: Kind,
    justification: str,
    compensating_action: Optional[str] = None,
    bounded_budget: Optional[str] = None,
) -> StateTransition:
    return StateTransition(
        op_id=op_id,
        domain=domain,
        from_state=from_state,
        to_state=to_state,
        kind=kind,
        justification=justification,
        compensating_action=compensating_action,
        bounded_budget=bounded_budget,
    )


R = Kind.REVERSIBLE
B = Kind.BOUNDED_IRREVERSIBLE
I = Kind.IRREVERSIBLE


_ALL: list[StateTransition] = [

    # ── Voice State Machine (23 transitions) ──────────────────────────────────
    _t("voice.idle→ready", "voice", "idle", "ready", R,
       "Session initialised; READY→IDLE is restored via ERROR→IDLE or explicit reset."),
    _t("voice.ready→listening", "voice", "ready", "listening", R,
       "Microphone activated; INTERRUPTED→READY reverses to an equivalent ready state."),
    _t("voice.ready→muted", "voice", "ready", "muted", R,
       "Mute toggle; MUTED→READY exactly reverses."),
    _t("voice.listening→transcribing", "voice", "listening", "transcribing", B,
       "Audio segment captured and submitted to ASR pipeline; the segment buffer is consumed.",
       compensating_action=(
           "voice.session_reset — discard partial transcript and return to IDLE; "
           "write compensating receipt to Lineage Fabric"
       ),
       bounded_budget="1 audio segment per transcription invocation"),
    _t("voice.listening→muted", "voice", "listening", "muted", R,
       "Mute during active listen; MUTED→READY reverses."),
    _t("voice.transcribing→thinking", "voice", "transcribing", "thinking", B,
       "ASR token stream committed; transcript object persisted to session record.",
       compensating_action=(
           "voice.session_reset — discard transcript, return to IDLE; "
           "write compensating receipt to Lineage Fabric"
       ),
       bounded_budget="1 transcript object per ASR call"),
    _t("voice.transcribing→interrupted", "voice", "transcribing", "interrupted", R,
       "Transcription aborted; INTERRUPTED→LISTENING reverses."),
    _t("voice.thinking→responding", "voice", "thinking", "responding", B,
       "LLM tokens generated and streamed; inference compute is consumed.",
       compensating_action=(
           "voice.session_reset — discard response tokens, return to READY; "
           "write compensating receipt to Lineage Fabric"
       ),
       bounded_budget="1 model call per thinking cycle"),
    _t("voice.thinking→executing", "voice", "thinking", "executing", B,
       "CPS operation dispatched to Handrail; execution slot is consumed.",
       compensating_action=(
           "cps.compensate — run registered undo op if available; "
           "else write failure_event to Lineage Fabric and return to READY"
       ),
       bounded_budget="1 CPS execution slot per dispatch"),
    _t("voice.thinking→error", "voice", "thinking", "error", B,
       "Error state recorded in Lineage Fabric receipt chain; error event slot consumed.",
       compensating_action=(
           "voice.error_receipt_acknowledge — write acknowledgment receipt, "
           "clear error and transition to READY"
       ),
       bounded_budget="1 error event emission per thinking cycle"),
    _t("voice.responding→ready", "voice", "responding", "ready", R,
       "Natural completion; session cycles back to READY for the next utterance."),
    _t("voice.responding→interrupted", "voice", "responding", "interrupted", R,
       "Response interrupted mid-stream; INTERRUPTED→READY reverses."),
    _t("voice.responding→awaiting_confirmation", "voice", "responding", "awaiting_confirmation", B,
       "Confirmation request emitted to the user; confirmation slot is consumed.",
       compensating_action=(
           "voice.confirmation_timeout — timeout path returns to READY with no action taken; "
           "write timeout receipt to Lineage Fabric"
       ),
       bounded_budget="1 confirmation request per responding cycle"),
    _t("voice.executing→responding", "voice", "executing", "responding", B,
       "Execution result committed to session and Lineage Fabric; result slot consumed.",
       compensating_action=(
           "voice.session_reset — discard execution result, log compensating receipt"
       ),
       bounded_budget="1 execution result object per execution"),
    _t("voice.executing→error", "voice", "executing", "error", B,
       "Execution error logged permanently in failure_events.jsonl.",
       compensating_action=(
           "voice.error_receipt_acknowledge — write acknowledgment receipt, "
           "clear error and transition to READY"
       ),
       bounded_budget="1 error event emission per execution"),
    _t("voice.awaiting_confirmation→executing", "voice", "awaiting_confirmation", "executing", I,
       "User confirmation granted; action is constitutionally authorised. "
       "A confirmed intent cannot be un-confirmed.",
       compensating_action=(
           "cps.compensate — run registered undo op if domain supports it; "
           "governance review required for any reversal"
       )),
    _t("voice.awaiting_confirmation→ready", "voice", "awaiting_confirmation", "ready", R,
       "Confirmation declined; no action taken; session resets to READY."),
    _t("voice.awaiting_confirmation→interrupted", "voice", "awaiting_confirmation", "interrupted", R,
       "Confirmation interrupted; INTERRUPTED→READY reverses."),
    _t("voice.interrupted→listening", "voice", "interrupted", "listening", R,
       "Resume listening after interrupt."),
    _t("voice.interrupted→ready", "voice", "interrupted", "ready", R,
       "Full session reset after interrupt."),
    _t("voice.muted→ready", "voice", "muted", "ready", R,
       "Unmute; READY→MUTED can re-mute."),
    _t("voice.error→ready", "voice", "error", "ready", R,
       "Error cleared; session continues from READY."),
    _t("voice.error→idle", "voice", "error", "idle", R,
       "Full reset to initial IDLE state."),

    # ── Program Runtime (15 transitions) ──────────────────────────────────────
    _t("program.dormant→activated", "program", "dormant", "activated", B,
       "Activation receipt written to Lineage Fabric; resource allocation begins.",
       compensating_action=(
           "program.deactivate_receipt — write deactivation receipt, return to DORMANT "
           "if no downstream receipts have been emitted"
       ),
       bounded_budget="1 program activation per instance"),
    _t("program.activated→briefing", "program", "activated", "briefing", B,
       "Briefing session opened; activation slot consumed.",
       compensating_action=(
           "program.briefing_abort — write abort receipt, return to ACTIVATED"
       ),
       bounded_budget="1 briefing slot per activation"),
    _t("program.activated→paused", "program", "activated", "paused", R,
       "Program paused; PAUSED→ACTIVATED exactly reverses."),
    _t("program.activated→archived", "program", "activated", "archived", I,
       "Permanent termination from ACTIVATED; data sealed in Lineage Fabric ledger.",
       compensating_action=(
           "governance.archive_review — governance program records the archive rationale "
           "as a canon entry; no state reversal is possible"
       )),
    _t("program.briefing→executing", "program", "briefing", "executing", B,
       "Execution authorisation granted; execution receipt emitted to Lineage Fabric.",
       compensating_action=(
           "program.execution_abort — write abort receipt, halt CPS chain"
       ),
       bounded_budget="1 execution run per briefing"),
    _t("program.briefing→paused", "program", "briefing", "paused", R,
       "Briefing paused; PAUSED→ACTIVATED can resume."),
    _t("program.briefing→archived", "program", "briefing", "archived", I,
       "Permanent termination from BRIEFING; sealed in Lineage Fabric ledger.",
       compensating_action=(
           "governance.archive_review — governance program records the archive rationale; "
           "no state reversal is possible"
       )),
    _t("program.executing→review", "program", "executing", "review", B,
       "Execution output committed for review; review receipt emitted to Lineage Fabric.",
       compensating_action=(
           "program.review_abort — write abort receipt, return to EXECUTING for continuation"
       ),
       bounded_budget="1 review slot per execution"),
    _t("program.executing→paused", "program", "executing", "paused", R,
       "Execution paused mid-run; PAUSED→ACTIVATED to resume."),
    _t("program.review→executing", "program", "review", "executing", R,
       "Review returned execution for further processing."),
    _t("program.review→completed", "program", "review", "completed", I,
       "Program completion is permanent; outcomes sealed in Lineage Fabric. Cannot reopen.",
       compensating_action=(
           "knowledge.promote_to_canon — completion outcomes must be promoted to the "
           "canonical knowledge base before the completed record becomes authoritative"
       )),
    _t("program.review→archived", "program", "review", "archived", I,
       "Permanent termination from REVIEW; sealed in Lineage Fabric ledger.",
       compensating_action=(
           "governance.archive_review — governance program records the archive rationale; "
           "no state reversal is possible"
       )),
    _t("program.paused→activated", "program", "paused", "activated", R,
       "Resume from pause; ACTIVATED→PAUSED can re-pause."),
    _t("program.paused→archived", "program", "paused", "archived", I,
       "Permanent termination from PAUSED; sealed in Lineage Fabric ledger.",
       compensating_action=(
           "governance.archive_review — governance program records the archive rationale; "
           "no state reversal is possible"
       )),
    _t("program.completed→archived", "program", "completed", "archived", I,
       "Completed programs are archived permanently. Both COMPLETED and ARCHIVED are terminal.",
       compensating_action=(
           "knowledge.promote_to_canon — all completed outputs must be promoted to canon "
           "before archival is considered complete"
       )),

    # ── Narrative State Machine (4 transitions) ───────────────────────────────
    _t("narrative.drafted→buffered", "narrative", "drafted", "buffered", R,
       "Narrative buffered for challenge review; retraction to DRAFTED is permitted."),
    _t("narrative.buffered→challenged", "narrative", "buffered", "challenged", B,
       "Challenge event logged to Lineage Fabric; challenge token consumed.",
       compensating_action=(
           "narrative.challenge_withdraw — write withdrawal receipt to Lineage Fabric, "
           "return narrative to BUFFERED"
       ),
       bounded_budget="1 challenge token per narrative object"),
    _t("narrative.challenged→stabilized", "narrative", "challenged", "stabilized", I,
       "Constitutional seal: stabilised narratives become part of the canonical knowledge base. "
       "Permanent by constitutional design.",
       compensating_action=(
           "narrative.supersede — create a superseding narrative via knowledge.promote_to_canon; "
           "the original stabilised record is sealed and immutable"
       )),
    _t("narrative.any→superseded", "narrative", "*", "superseded", I,
       "Supersession records that a canonical successor exists. "
       "The lineage link is permanent and immutable.",
       compensating_action=(
           "narrative.supersession_review — governance review can annotate an erroneous "
           "supersession, but the supersession record itself is immutable"
       )),

    # ── TierLatch / Continuum (3 transitions) ─────────────────────────────────
    _t("tier.0→2", "tier", "0", "2", B,
       "Global isolation triggered; ratchet state cannot self-reverse without quorum.",
       compensating_action=(
           "governance.tier_review — 2-of-3 governance quorum authorises tier reduction "
           "after threat resolution; reduction receipt written to Lineage Fabric"
       ),
       bounded_budget="1 isolation event; reversal requires 2-of-3 governance quorum"),
    _t("tier.2→3", "tier", "2", "3", I,
       "Terminal lock. Tier 3 is constitutionally irreversible — the system is frozen for safety.",
       compensating_action=(
           "sys.shutdown_graceful — controlled shutdown sequence executes; "
           "no state reversal is constitutionally possible"
       )),
    _t("tier.isolate_domain", "tier", "active", "isolated", B,
       "Domain isolation event logged; isolated_domains set grows monotonically.",
       compensating_action=(
           "governance.domain_restore — governance quorum authorises domain restoration; "
           "restoration receipt written to Lineage Fabric"
       ),
       bounded_budget="1 domain isolation event per domain_id"),

    # ── Continuum Append-Only Store (1 transition) ────────────────────────────
    _t("continuum.stream_append", "continuum", "stream_n", "stream_n+1", I,
       "Cryptographic append-only stream; SHA256-chained entries cannot be deleted or modified.",
       compensating_action=(
           "continuum.correction_append — append a correction event to the same stream "
           "that references the erroneous entry by sequence number"
       )),

    # ── Receipt Chain / Lineage Fabric (1 transition) ─────────────────────────
    _t("receipt.emit", "receipt", "chain_n", "chain_n+1", I,
       "Receipt emission is constitutionally irreversible; receipts ARE the Lineage Fabric.",
       compensating_action=(
           "receipt.emit_correction — emit a new receipt with event_type='correction' "
           "referencing the erroneous receipt_id; the original receipt is unchanged"
       )),

    # ── Calibration Band (6 transitions) ──────────────────────────────────────
    _t("calibration.block→review", "calibration", "BLOCK", "REVIEW", R,
       "Confidence score improved above 35%; band reclassification is bidirectional."),
    _t("calibration.review→pass", "calibration", "REVIEW", "PASS", R,
       "Confidence score improved above 65%; band reclassification is bidirectional."),
    _t("calibration.pass→high_assurance", "calibration", "PASS", "HIGH_ASSURANCE", R,
       "Confidence score improved above 80%; band reclassification is bidirectional."),
    _t("calibration.high_assurance→pass", "calibration", "HIGH_ASSURANCE", "PASS", R,
       "Confidence score degraded below 80%; band reclassification is bidirectional."),
    _t("calibration.pass→review", "calibration", "PASS", "REVIEW", R,
       "Confidence score degraded below 65%; band reclassification is bidirectional."),
    _t("calibration.review→block", "calibration", "REVIEW", "BLOCK", R,
       "Confidence score degraded below 35%; band reclassification is bidirectional."),
]

# ── Public registry ───────────────────────────────────────────────────────────

REGISTRY: dict[str, StateTransition] = {t.op_id: t for t in _ALL}

REVERSIBLE: dict[str, StateTransition] = {
    k: v for k, v in REGISTRY.items() if v.kind == Kind.REVERSIBLE
}
BOUNDED_IRREVERSIBLE: dict[str, StateTransition] = {
    k: v for k, v in REGISTRY.items() if v.kind == Kind.BOUNDED_IRREVERSIBLE
}
IRREVERSIBLE: dict[str, StateTransition] = {
    k: v for k, v in REGISTRY.items() if v.kind == Kind.IRREVERSIBLE
}
NON_REVERSIBLE: dict[str, StateTransition] = {**BOUNDED_IRREVERSIBLE, **IRREVERSIBLE}

# 100% coverage gate — build fails if any op_id appears more than once.
assert len(REGISTRY) == len(_ALL), (
    f"Duplicate op_id detected: {len(_ALL)} entries but only {len(REGISTRY)} unique IDs"
)

# Alias required by coverage report and external consumers.
MANIFEST = REGISTRY


def coverage_gate() -> dict[str, int]:
    """Verify 100% classification+proof coverage over all State Manifold transitions.

    Returns:
        dict with keys: total_ops, reversible, irreversible_with_proof,
        irreversible_without_proof.  irreversible_without_proof is always 0;
        any deviation raises RuntimeError (hard build-fail gate).

    Raises:
        RuntimeError: if any non-reversible op lacks a KenosisProof.
    """
    from .kenosis import CONSTITUTIONAL_PROOFS  # lazy import avoids circular dep

    missing = set(NON_REVERSIBLE) - set(CONSTITUTIONAL_PROOFS)
    if missing:
        raise RuntimeError(
            f"Coverage gate FAIL — non-reversible ops without KenosisProof: "
            f"{sorted(missing)}"
        )

    return {
        "total_ops": len(REGISTRY),
        "reversible": len(REVERSIBLE),
        "irreversible_with_proof": len(NON_REVERSIBLE),
        "irreversible_without_proof": 0,
    }
