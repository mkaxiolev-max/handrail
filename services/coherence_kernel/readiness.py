"""Collapse-readiness rubric: 9 sub-metrics → score_100."""
from __future__ import annotations
from pathlib import Path
from services.coherence_kernel import schemas
from services.coherence_kernel.storage import ledger


def compute_readiness(
    branch: schemas.BranchState, db_path: Path | None = None
) -> schemas.CollapseReadinessScore:
    amp = branch.evidence_amplitude

    coherence = amp.magnitude * 10.0
    diversity = amp.source_diversity * 10.0
    # interference_quality: from latest ledger pass or default to magnitude proxy
    interference_quality = amp.magnitude * 9.0
    evidence_weight = min(10.0, amp.redundancy_count * 1.5)
    contradiction_metabolism = min(10.0, len(branch.contradiction_links) * 2.5)
    decoherence_resistance = branch.decoherence_resistance * 10.0
    readout_discipline = (1.0 - branch.uncertainty) * 10.0
    receipt_integrity = min(10.0, len(branch.cps_op_chain) * 1.0 + 5.0)
    reversibility = max(0.0, 10.0 - min(10.0, branch.reversibility_cost))

    rs = schemas.CollapseReadinessScore.compute(
        coherence=round(min(10.0, coherence), 4),
        diversity=round(min(10.0, diversity), 4),
        interference_quality=round(min(10.0, interference_quality), 4),
        evidence_weight=round(min(10.0, evidence_weight), 4),
        contradiction_metabolism=round(min(10.0, contradiction_metabolism), 4),
        decoherence_resistance=round(min(10.0, decoherence_resistance), 4),
        readout_discipline=round(min(10.0, readout_discipline), 4),
        receipt_integrity=round(min(10.0, receipt_integrity), 4),
        reversibility=round(min(10.0, reversibility), 4),
    )
    kwargs = {"db_path": db_path} if db_path else {}
    ledger.append_readiness_score(rs.model_dump(mode="json"), branch.id, rs.score_100, **kwargs)
    return rs
