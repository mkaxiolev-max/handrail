"""Aletheion v2.0 — Pre-action gate. Final check before Handrail CPS."""
from __future__ import annotations
from typing import Any


def pre_action_check(action: Any, signal: Any, logos: Any) -> str:
    """
    Returns ADMIT if action is clear to execute, DENY otherwise.
    signal: duck-typed with .dignity_sensitivity, .narrative_collapse_risk
    logos:  duck-typed with .deception_risk, .coercion_risk, .domination_risk,
                            .truth_coherence, .dignity_preservation
    """
    deception   = getattr(logos, "deception_risk",    0.0)
    coercion    = getattr(logos, "coercion_risk",     0.0)
    domination  = getattr(logos, "domination_risk",   0.0)
    dignity_sig = getattr(signal, "dignity_sensitivity",      0.0)
    narrative   = getattr(signal, "narrative_collapse_risk",  0.0)

    risk = deception + coercion + domination + dignity_sig + narrative

    # Hard gate: irreversible action with any risk
    irreversible = getattr(action, "irreversible", False)
    if irreversible and risk > 0.0:
        return "DENY"

    if risk >= 1.5:
        return "DENY"

    return "ADMIT"
