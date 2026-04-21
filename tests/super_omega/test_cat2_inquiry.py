"""Category 2 — Inquiry (Deep-Research equivalent). AXIOLEV © 2026."""
from services.omega_logos.layers.inquiry import HypothesisGraph, Claim

def test_2_1_hypothesis_graph_with_confidence():
    g = HypothesisGraph()
    g.add(Claim("a","AI capex is growing", 0.82, ["src1"]))
    g.add(Claim("b","AI capex is slowing", 0.41, ["src2"]))
    s = g.summary()
    assert s["claim_count"] == 2
    assert 0.0 <= s["avg_confidence"] <= 1.0

def test_2_2_contradiction_does_not_collapse():
    g = HypothesisGraph()
    g.add(Claim("a","X holds", 0.9))
    g.add(Claim("b","X does not hold", 0.9))
    g.detect_contradictions([("a","b")])
    assert len(g.contradictions) == 1
    # The system must SURFACE the contradiction, not collapse one side
    assert "a" in g.claims and "b" in g.claims
