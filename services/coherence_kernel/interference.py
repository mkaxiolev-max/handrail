"""Interference pass — 5 comparison ops, cancellation/reinforcement rules."""
from __future__ import annotations
import uuid
from services.coherence_kernel import schemas
from services.coherence_kernel.phase_alignment import phase_alignment_check, cosine
from services.coherence_kernel.atomlex_client import embed_sync
from services.coherence_kernel.storage import ledger

COMPARISON_OPS = [
    "semantic_overlap",
    "claim_polarity",
    "provenance_intersection",
    "evidence_amplitude_phase",
    "contradiction_pressure",
]

CANCELLATION_RULE = (
    "opposing polarity AND phase_alignment < -0.7 AND provenance_intersection < 0.2"
)
REINFORCEMENT_RULE = (
    "same polarity AND phase_alignment > 0.7 AND source_diversity > 0.5"
)


def _semantic_overlap(a: schemas.BranchState, b: schemas.BranchState) -> float:
    ea = embed_sync(a.claim)
    eb = embed_sync(b.claim)
    return (cosine(ea, eb) + 1.0) / 2.0  # normalise to [0,1]


def _claim_polarity(a: schemas.BranchState, b: schemas.BranchState) -> float:
    """Heuristic polarity: 1.0 if both start with same word, -1.0 if one negates."""
    ac, bc = a.claim.lower(), b.claim.lower()
    negators = ("not ", "no ", "never ", "false ", "incorrect ")
    a_neg = any(ac.startswith(n) for n in negators)
    b_neg = any(bc.startswith(n) for n in negators)
    return 1.0 if a_neg == b_neg else -1.0


def _provenance_intersection(a: schemas.BranchState, b: schemas.BranchState) -> float:
    pa, pb = set(a.evidence_amplitude.provenance_chain), set(b.evidence_amplitude.provenance_chain)
    if not pa and not pb:
        return 0.0
    return len(pa & pb) / len(pa | pb)


def _evidence_amplitude_phase(a: schemas.BranchState, b: schemas.BranchState) -> float:
    """Phase alignment from stored amplitude phases (authoritative carrier of evidence polarity)."""
    return (a.evidence_amplitude.phase + b.evidence_amplitude.phase) / 2.0


def _contradiction_pressure(a: schemas.BranchState, b: schemas.BranchState) -> float:
    """Graph distance proxy: shared contradiction links → high pressure."""
    cl_a = set(a.contradiction_links)
    cl_b = set(b.contradiction_links)
    if not cl_a and not cl_b:
        return 0.0
    return len(cl_a & cl_b) / max(len(cl_a | cl_b), 1)


def interference_pass(
    branch_a: schemas.BranchState,
    branch_b: schemas.BranchState,
) -> schemas.InterferencePass:
    sem_ovl = _semantic_overlap(branch_a, branch_b)
    polarity = _claim_polarity(branch_a, branch_b)
    prov_int = _provenance_intersection(branch_a, branch_b)
    phase_aln = _evidence_amplitude_phase(branch_a, branch_b)
    contra_p = _contradiction_pressure(branch_a, branch_b)

    # Cancellation: opposing polarity AND phase < -0.7 AND prov_int < 0.2
    cancelled = polarity < 0 and phase_aln < -0.7 and prov_int < 0.2
    # Reinforcement: same polarity AND phase > 0.7 AND source_diversity > 0.5
    reinforced = (
        polarity > 0
        and phase_aln > 0.7
        and branch_a.evidence_amplitude.source_diversity > 0.5
        and branch_b.evidence_amplitude.source_diversity > 0.5
    )

    if cancelled:
        # Quality = strength of cancellation: weight phase depth twice, low prov once
        quality = (abs(phase_aln) * 2.0 + (1.0 - prov_int)) / 3.0
        output_branches: list[str] = []
    elif reinforced:
        # Quality = strength of reinforcement: weight phase twice, high prov once
        quality = (phase_aln * 2.0 + prov_int) / 3.0
        output_branches = [branch_a.id, branch_b.id]
    else:
        quality = (sem_ovl + abs(prov_int) + abs(contra_p)) / 3.0
        output_branches = [branch_a.id] if sem_ovl > 0.5 else [branch_b.id]

    receipt_id = f"IFP-{uuid.uuid4().hex[:12]}"
    result = schemas.InterferencePass(
        input_branches=[branch_a.id, branch_b.id],
        comparison_ops=COMPARISON_OPS,
        cancellation_rule=CANCELLATION_RULE,
        reinforcement_rule=REINFORCEMENT_RULE,
        output_branches=output_branches,
        interference_quality_score=round(min(1.0, max(0.0, quality)), 6),
        receipt=receipt_id,
    )
    ledger.append_interference_pass(result.model_dump(mode="json"), receipt_id)
    return result
