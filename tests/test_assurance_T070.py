"""T-070 — reject transition without receipt.

A state transition wrapped with @assured that provides no artifacts causes
the dispatcher to emit a PENDING ObligationArtifact.  @assured treats an
obligation as a BLOCK (not a receipt) and raises AssuranceViolation.
"""
import pytest
from services.assurance import (
    ComputationContract,
    RiskTier,
    ObligationStatus,
    AssuranceViolation,
    assured,
)


CONTRACT = ComputationContract(
    inputs_schema={"x": "int"},
    outputs_schema={"y": "int"},
    preconditions=[],
    postconditions=[],
    side_effects=[],
    risk_tier=RiskTier.R1,
)


def test_reject_transition_without_receipt():
    @assured(CONTRACT)   # no artifacts_fn → empty bundle → obligation emitted
    def my_transition(x):
        return {"y": x + 1}

    with pytest.raises(AssuranceViolation) as exc_info:
        my_transition(5)

    err = exc_info.value
    assert "obligation_pending" in str(err)
    # Caller receives the obligation so they can fulfill it and retry
    assert err.obligation is not None
    assert err.obligation.status == ObligationStatus.PENDING
    assert err.obligation.compensating_action == "provide_justification_artifact"
