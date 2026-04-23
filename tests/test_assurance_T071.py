"""T-071 — reject receipt without justification.

A VerificationReceipt submitted as an artifact without any backing
ProofArtifact / CertificateArtifact / BoundedClaim is rejected by the
dispatcher (I11-b: Receipt without justification).
"""
import pytest
from services.assurance import (
    ComputationContract,
    RiskTier,
    Verdict,
    VerificationReceipt,
    VerificationDispatcher,
    AssuranceViolation,
    assured,
)


CONTRACT = ComputationContract(
    inputs_schema={},
    outputs_schema={},
    preconditions=[],
    postconditions=[],
    side_effects=[],
    risk_tier=RiskTier.R0,
)


def _fake_receipt() -> VerificationReceipt:
    return VerificationReceipt(
        subject_hash="sha256:" + "a" * 64,
        verdict=Verdict.VERIFIED,
        evidence_refs=["self_attested"],
        timestamp="2026-04-23T00:00:00Z",
    )


def test_reject_receipt_without_justification():
    # Dispatcher-level: bare receipt in bundle, no backing justification
    dispatcher = VerificationDispatcher()
    receipt, obligation = dispatcher.dispatch(CONTRACT, [_fake_receipt()])

    assert receipt is not None
    assert receipt.verdict == Verdict.REJECTED
    assert any("no_justification" in ref for ref in receipt.evidence_refs)
    assert obligation is None


def test_assured_rejects_receipt_without_justification():
    # End-to-end: @assured receives a receipt-only bundle → raises
    @assured(CONTRACT, artifacts_fn=lambda _: [_fake_receipt()])
    def my_transition():
        return {}

    with pytest.raises(AssuranceViolation) as exc_info:
        my_transition()

    assert "receipt_rejected" in str(exc_info.value)
