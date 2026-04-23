"""T-077 — cross-layer receipt chain integrity.

Two dispatches are linked via prev_hash.  verify_receipt_chain() confirms
that receipt_2.evidence_refs contains a 'prev:<hash>' entry pointing at
receipt_1.subject_hash.  Tampering the chain breaks the integrity check.
"""
import pytest
from services.assurance import (
    ComputationContract,
    ProofArtifact,
    ProofKind,
    RiskTier,
    Verdict,
    VerificationDispatcher,
    VerificationReceipt,
    verify_receipt_chain,
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

CONTENT_A = {"layer": "handrail", "op": "cps_dispatch"}
CONTENT_B = {"layer": "ns",       "op": "receipt_emit"}


def _proof(content: dict) -> ProofArtifact:
    return ProofArtifact(
        kind=ProofKind.AUDIT,
        content=content,
        verifier="lineage_fabric",
        hash=make_proof_hash(content),
    )


def test_cross_layer_receipt_chain_integrity():
    dispatcher = VerificationDispatcher()

    # Layer 1: Handrail dispatch
    receipt_1, _ = dispatcher.dispatch(CONTRACT, [_proof(CONTENT_A)])
    assert receipt_1 is not None
    assert receipt_1.verdict == Verdict.VERIFIED

    # Layer 2: NS dispatch, linked to layer 1
    receipt_2, _ = dispatcher.dispatch(
        CONTRACT, [_proof(CONTENT_B)], prev_hash=receipt_1.subject_hash
    )
    assert receipt_2 is not None
    assert receipt_2.verdict == Verdict.VERIFIED
    assert any(ref == f"prev:{receipt_1.subject_hash}" for ref in receipt_2.evidence_refs)

    # Chain integrity check
    assert verify_receipt_chain([receipt_1, receipt_2])


def test_tampered_chain_fails_integrity_check():
    dispatcher = VerificationDispatcher()

    receipt_1, _ = dispatcher.dispatch(CONTRACT, [_proof(CONTENT_A)])
    receipt_2, _ = dispatcher.dispatch(
        CONTRACT, [_proof(CONTENT_B)], prev_hash=receipt_1.subject_hash
    )

    # Tamper: swap receipt order → chain should break
    assert not verify_receipt_chain([receipt_2, receipt_1])


def test_single_receipt_chain_is_always_valid():
    dispatcher = VerificationDispatcher()
    receipt, _ = dispatcher.dispatch(CONTRACT, [_proof(CONTENT_A)])
    assert verify_receipt_chain([receipt])
