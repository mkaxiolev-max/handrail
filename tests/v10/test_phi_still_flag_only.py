"""v10 explicit invariant guard — Phi NEVER in gate weights."""
import pytest
from services.ns.nss.lenses.scoring import WEIGHTS

def test_phi_curvature_is_not_a_gate():
    assert "phi_curvature" not in WEIGHTS, "VIOLATION: phi_curvature must never be a gate"
    assert "phi" not in WEIGHTS,           "VIOLATION: phi must never be a gate"

def test_weights_sum_to_one():
    assert abs(sum(WEIGHTS.values()) - 1.0) < 1e-9

def test_weights_are_ten():
    assert len(WEIGHTS) == 10, f"Expected 10 gates, got {len(WEIGHTS)}: {list(WEIGHTS)}"
