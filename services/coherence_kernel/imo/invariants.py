"""7 hard invariants + 3 advisory invariants for collapse-gate adjudication."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Callable
from services.coherence_kernel import schemas
from services.coherence_kernel.decoherence import aggregator


@dataclass(frozen=True)
class Invariant:
    name: str
    kind: str  # "hard" | "advisory"
    description: str
    check: Callable[[schemas.BranchState, schemas.CollapseReadinessScore, schemas.DecoherenceDetector], bool]


def _h1(b: schemas.BranchState, rs: schemas.CollapseReadinessScore, dd: schemas.DecoherenceDetector) -> bool:
    return rs.score_100 >= rs.target_threshold


def _h2(b: schemas.BranchState, rs: schemas.CollapseReadinessScore, dd: schemas.DecoherenceDetector) -> bool:
    return len(b.evidence_amplitude.provenance_chain) >= 2


def _h3(b: schemas.BranchState, rs: schemas.CollapseReadinessScore, dd: schemas.DecoherenceDetector) -> bool:
    return b.evidence_amplitude.magnitude >= 0.3


def _h4(b: schemas.BranchState, rs: schemas.CollapseReadinessScore, dd: schemas.DecoherenceDetector) -> bool:
    return b.uncertainty <= 0.8


def _h5(b: schemas.BranchState, rs: schemas.CollapseReadinessScore, dd: schemas.DecoherenceDetector) -> bool:
    return not dd.breached


def _h6(b: schemas.BranchState, rs: schemas.CollapseReadinessScore, dd: schemas.DecoherenceDetector) -> bool:
    return len(b.cps_op_chain) > 0


def _h7(b: schemas.BranchState, rs: schemas.CollapseReadinessScore, dd: schemas.DecoherenceDetector) -> bool:
    return b.reversibility_cost <= 100.0


def _a1(b: schemas.BranchState, rs: schemas.CollapseReadinessScore, dd: schemas.DecoherenceDetector) -> bool:
    return rs.score_100 >= rs.omega_target


def _a2(b: schemas.BranchState, rs: schemas.CollapseReadinessScore, dd: schemas.DecoherenceDetector) -> bool:
    return b.evidence_amplitude.source_diversity >= 0.5


def _a3(b: schemas.BranchState, rs: schemas.CollapseReadinessScore, dd: schemas.DecoherenceDetector) -> bool:
    return len(b.contradiction_links) >= 1


HARD: list[Invariant] = [
    Invariant("H1_MIN_READINESS", "hard", "score_100 >= target_threshold (78.0)", _h1),
    Invariant("H2_PROVENANCE_DEPTH", "hard", "provenance_chain length >= 2", _h2),
    Invariant("H3_EVIDENCE_MAGNITUDE", "hard", "evidence magnitude >= 0.3", _h3),
    Invariant("H4_UNCERTAINTY_BOUNDED", "hard", "uncertainty <= 0.8", _h4),
    Invariant("H5_NO_DECOHERENCE_BREACH", "hard", "decoherence aggregate < threshold", _h5),
    Invariant("H6_RECEIPT_CHAIN_VALID", "hard", "cps_op_chain non-empty", _h6),
    Invariant("H7_REVERSIBILITY_DOCUMENTED", "hard", "reversibility_cost <= 100.0", _h7),
]

ADVISORY: list[Invariant] = [
    Invariant("A1_OMEGA_TARGET", "advisory", "score_100 >= omega_target (95.0)", _a1),
    Invariant("A2_SOURCE_DIVERSITY", "advisory", "source_diversity >= 0.5", _a2),
    Invariant("A3_CONTRADICTION_METABOLISM", "advisory", "at least one contradiction_link", _a3),
]

ALL: list[Invariant] = HARD + ADVISORY
