"""T-074 — obligation path with compensating action resolves cleanly.

Flow:
  1. First attempt: no proof → AssuranceViolation raised, obligation returned.
  2. Caller performs the compensating action (marks obligation RESOLVED).
  3. Retry with the resolved obligation as artifact → VERIFIED receipt → success.
"""
import pytest
from services.assurance import (
    ComputationContract,
    ObligationArtifact,
    ObligationStatus,
    RiskTier,
    Verdict,
    AssuranceViolation,
    assured,
)


CONTRACT = ComputationContract(
    inputs_schema={"owner": "axiolev"},
    outputs_schema={"state": "str"},
    preconditions=[],
    postconditions=[],
    side_effects=["soft_state_update"],
    risk_tier=RiskTier.R1,
)


def test_obligation_path_with_compensating_action_resolves_cleanly():
    # --- Step 1: initial attempt, no artifacts → obligation emitted → blocked ---
    @assured(CONTRACT)  # no artifacts_fn
    def do_transition():
        return {"state": "updated"}

    caught_obligation = None
    with pytest.raises(AssuranceViolation) as exc_info:
        do_transition()

    err = exc_info.value
    assert "obligation_pending" in str(err)
    caught_obligation = err.obligation
    assert caught_obligation is not None
    assert caught_obligation.status == ObligationStatus.PENDING

    # --- Step 2: caller performs compensating action ---
    resolved = ObligationArtifact(
        owner=caught_obligation.owner,
        deadline=caught_obligation.deadline,
        compensating_action=caught_obligation.compensating_action,
        status=ObligationStatus.RESOLVED,
    )

    # --- Step 3: retry with resolved obligation → VERIFIED receipt → allowed ---
    @assured(CONTRACT, artifacts_fn=lambda _: [resolved])
    def do_transition_retry():
        return {"state": "updated"}

    result = do_transition_retry()
    assert result == {"state": "updated"}
