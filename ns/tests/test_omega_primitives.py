"""axiolev-omega-primitives-test-v2"""
from ns.omega.primitives import (
    ConfidenceEnvelope, ProjectionMode, Recoverability,
)
from ns.omega.canon_gate import canon_gate


def test_confidence_weights_locked():
    c = ConfidenceEnvelope(evidence=1.0, contradiction=0.0, novelty=1.0, stability=1.0)
    assert abs(c.score - 1.0) < 1e-6


def test_canon_gate_six_fold():
    c = ConfidenceEnvelope(evidence=0.9, contradiction=0.1, novelty=0.5, stability=0.9)
    d = canon_gate(c, 0.95, True, "hic-1", "pdp-1")
    assert d.allowed
    d2 = canon_gate(c, 0.95, True, "", "pdp-1")
    assert not d2.allowed
    c_low = ConfidenceEnvelope(evidence=0.2, contradiction=0.1, novelty=0.1, stability=0.1)
    d3 = canon_gate(c_low, 0.95, True, "hic-1", "pdp-1")
    assert not d3.allowed
    c_contra = ConfidenceEnvelope(evidence=0.9, contradiction=0.9, novelty=0.5, stability=0.9)
    d4 = canon_gate(c_contra, 0.95, True, "hic-1", "pdp-1")
    assert not d4.allowed


def test_projection_modes_six():
    assert len([m for m in ProjectionMode]) == 6


def test_recoverability_five():
    assert len([r for r in Recoverability]) == 5
