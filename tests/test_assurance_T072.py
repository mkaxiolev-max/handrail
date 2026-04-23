"""T-072 — reject justification without verification-or-obligation.

A ProofArtifact with a tampered (wrong) hash fails the dispatcher's hash
check.  Because a justification artifact WAS submitted, the dispatcher does
not fall back to creating an obligation — it returns a REJECTED receipt.
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
    inputs_schema={},
    outputs_schema={},
    preconditions=[],
    postconditions=[],
    side_effects=[],
    risk_tier=RiskTier.R1,
)

CONTENT = {"theorem": "liveness", "steps": 42}


def _tampered_proof() -> ProofArtifact:
    """Valid content but hash set to a wrong value."""
    return ProofArtifact(
        kind=ProofKind.FORMAL,
        content=CONTENT,
        verifier="lean4_validator",
        hash="sha256:" + "0" * 64,   # intentionally wrong
    )


def test_reject_justification_without_verification_or_obligation():
    dispatcher = VerificationDispatcher()
    receipt, obligation = dispatcher.dispatch(CONTRACT, [_tampered_proof()])

    # Justification present but failed → REJECTED, no obligation fallback
    assert receipt is not None
    assert receipt.verdict == Verdict.REJECTED
    assert any("proof_hash_mismatch" in ref for ref in receipt.evidence_refs)
    assert obligation is None


def test_assured_rejects_tampered_proof():
    @assured(CONTRACT, artifacts_fn=lambda _: [_tampered_proof()])
    def my_transition():
        return {}

    with pytest.raises(AssuranceViolation) as exc_info:
        my_transition()

    assert "receipt_rejected" in str(exc_info.value)
