"""T-073 — accept verified receipt end-to-end.

A well-formed ProofArtifact with a correct hash passes all dispatcher checks
and produces a VERIFIED VerificationReceipt.  @assured allows the transition.
"""
import pytest
from services.assurance import (
    ComputationContract,
    ProofArtifact,
    ProofKind,
    RiskTier,
    Verdict,
    VerificationDispatcher,
    AssuranceViolation,
    assured,
    make_proof_hash,
)


CONTRACT = ComputationContract(
    inputs_schema={"record_id": "str"},
    outputs_schema={"committed": "bool"},
    preconditions=[],
    postconditions=[],
    side_effects=["ledger_append"],
    risk_tier=RiskTier.R2,
)

CONTENT = {"theorem": "safety_invariant", "steps": 7, "model": "TLA+"}


def _valid_proof() -> ProofArtifact:
    return ProofArtifact(
        kind=ProofKind.FORMAL,
        content=CONTENT,
        verifier="tla_apalache",
        hash=make_proof_hash(CONTENT),
    )


def test_accept_verified_receipt_end_to_end():
    dispatcher = VerificationDispatcher()
    receipt, obligation = dispatcher.dispatch(CONTRACT, [_valid_proof()])

    assert obligation is None
    assert receipt is not None
    assert receipt.verdict == Verdict.VERIFIED
    assert len(receipt.evidence_refs) == 1
    assert receipt.evidence_refs[0].startswith("proof:formal:")
    assert receipt.subject_hash.startswith("sha256:")
    assert receipt.timestamp.endswith("Z")


def test_assured_allows_verified_transition():
    @assured(CONTRACT, artifacts_fn=lambda _: [_valid_proof()])
    def commit_record(record_id: str):
        return {"committed": True, "id": record_id}

    result = commit_record("rec_001")
    assert result == {"committed": True, "id": "rec_001"}
