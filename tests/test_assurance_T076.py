"""T-076 — postcondition failure leads to rejection.

A callable postcondition that returns False causes @assured to raise
AssuranceViolation AFTER the wrapped function has executed (result is
discarded and the transition is rejected).
"""
import pytest
from services.assurance import (
    ComputationContract,
    ProofArtifact,
    ProofKind,
    RiskTier,
    AssuranceViolation,
    assured,
    make_proof_hash,
)


CONTENT = {"claim": "postcondition_test"}

HIGH_SCORE_CONTRACT = ComputationContract(
    inputs_schema={"input": "any"},
    outputs_schema={"score": "float"},
    preconditions=[],
    postconditions=[lambda result: result.get("score", 0) > 0.5],  # score must be > 0.5
    side_effects=[],
    risk_tier=RiskTier.R1,
)


def _valid_proof() -> ProofArtifact:
    return ProofArtifact(
        kind=ProofKind.EMPIRICAL,
        content=CONTENT,
        verifier="unit_test",
        hash=make_proof_hash(CONTENT),
    )


def test_contract_postcondition_failure_leads_to_rejection():
    @assured(HIGH_SCORE_CONTRACT, artifacts_fn=lambda _: [_valid_proof()])
    def score_something(x):
        return {"score": 0.1}   # intentionally below threshold

    with pytest.raises(AssuranceViolation) as exc_info:
        score_something("any_input")

    assert "postcondition_failed" in str(exc_info.value)


def test_contract_postcondition_passes_for_valid_output():
    @assured(HIGH_SCORE_CONTRACT, artifacts_fn=lambda _: [_valid_proof()])
    def score_something(x):
        return {"score": 0.9}

    result = score_something("any_input")
    assert result["score"] == pytest.approx(0.9)
