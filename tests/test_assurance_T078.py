# Copyright © 2026 AXIOLEV Holdings LLC. All rights reserved.
"""T-078 — expired certificate rejected.

A CertificateArtifact whose expiry timestamp is in the past is rejected by
the dispatcher's cert verifier.  An unexpired cert passes.
"""
import pytest
from datetime import datetime, timedelta, timezone

from services.assurance import (
    CertificateArtifact,
    ComputationContract,
    RiskTier,
    Verdict,
    VerificationDispatcher,
    AssuranceViolation,
    assured,
)


CONTRACT = ComputationContract(
    inputs_schema={"doc_id": "str"},
    outputs_schema={"sealed": "bool"},
    preconditions=[],
    postconditions=[],
    side_effects=["canon_seal"],
    risk_tier=RiskTier.R2,
)


def _cert(*, expired: bool) -> CertificateArtifact:
    if expired:
        expiry = (datetime.now(timezone.utc) - timedelta(hours=1)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
    else:
        expiry = (datetime.now(timezone.utc) + timedelta(days=365)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
    return CertificateArtifact(
        subject="ns.canon.seal",
        claims={"scope": "lexicon", "tier": "R2"},
        issuer="axiolev_dignity_kernel",
        signature="sig_placeholder",
        expiry=expiry,
    )


def test_expired_certificate_rejected():
    dispatcher = VerificationDispatcher()
    receipt, obligation = dispatcher.dispatch(CONTRACT, [_cert(expired=True)])

    assert receipt is not None
    assert receipt.verdict == Verdict.REJECTED
    assert any("cert_expired" in ref for ref in receipt.evidence_refs)
    assert obligation is None


def test_expired_certificate_raises_via_assured():
    @assured(CONTRACT, artifacts_fn=lambda _: [_cert(expired=True)])
    def seal_document(doc_id: str):
        return {"sealed": True}

    with pytest.raises(AssuranceViolation) as exc_info:
        seal_document("doc_abc")

    assert "receipt_rejected" in str(exc_info.value)


def test_valid_certificate_accepted():
    dispatcher = VerificationDispatcher()
    receipt, obligation = dispatcher.dispatch(CONTRACT, [_cert(expired=False)])

    assert obligation is None
    assert receipt is not None
    assert receipt.verdict == Verdict.VERIFIED
    assert any("cert:ns.canon.seal" in ref for ref in receipt.evidence_refs)


def test_valid_certificate_allows_transition_via_assured():
    @assured(CONTRACT, artifacts_fn=lambda _: [_cert(expired=False)])
    def seal_document(doc_id: str):
        return {"sealed": True, "id": doc_id}

    result = seal_document("doc_xyz")
    assert result["sealed"] is True
