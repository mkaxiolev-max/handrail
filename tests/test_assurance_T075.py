"""T-075 — contract precondition failure leads to rejection.

A callable precondition that returns False causes @assured to raise
AssuranceViolation BEFORE the wrapped function executes.
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


CONTENT = {"claim": "precondition_test"}

POSITIVE_CONTRACT = ComputationContract(
    inputs_schema={"x": "int"},
    outputs_schema={"y": "int"},
    preconditions=[lambda inputs: inputs["args"][0] > 0],   # x must be positive
    postconditions=[],
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


def test_contract_precondition_failure_leads_to_rejection():
    call_log: list = []

    @assured(POSITIVE_CONTRACT, artifacts_fn=lambda _: [_valid_proof()])
    def add_one(x: int):
        call_log.append(x)   # must NOT be reached
        return {"y": x + 1}

    # x=0 violates precondition → AssuranceViolation raised before fn body runs
    with pytest.raises(AssuranceViolation) as exc_info:
        add_one(0)

    assert "precondition_failed" in str(exc_info.value)
    assert call_log == [], "function body must not execute when precondition fails"


def test_contract_precondition_passes_for_valid_input():
    @assured(POSITIVE_CONTRACT, artifacts_fn=lambda _: [_valid_proof()])
    def add_one(x: int):
        return {"y": x + 1}

    result = add_one(3)
    assert result == {"y": 4}
