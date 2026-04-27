"""C18 — ARMS scoring suite tests. I8."""
from services.arms_scoring.scorer import ARMSScorer, RiskDimension, ARMSReport
import pytest


def test_default_report():
    s = ARMSScorer()
    r = s.report()
    assert isinstance(r, ARMSReport)
    assert r.composite > 0


def test_green_band():
    s = ARMSScorer()
    for dim in RiskDimension:
        s.set_score(dim, 0.0)
    r = s.report()
    assert r.band == "green"


def test_red_band():
    s = ARMSScorer()
    for dim in RiskDimension:
        s.set_score(dim, 10.0)
    r = s.report()
    assert r.band == "red"


def test_mitigation_reduces_score():
    s = ARMSScorer()
    s.set_score(RiskDimension.OPERATIONAL, 8.0)
    before = s.report().composite
    s.add_mitigation(RiskDimension.OPERATIONAL)
    after = s.report().composite
    assert after < before


def test_invalid_score_raises():
    s = ARMSScorer()
    with pytest.raises(ValueError):
        s.set_score(RiskDimension.LEGAL, 11.0)


def test_mitigated_count():
    s = ARMSScorer()
    s.add_mitigation(RiskDimension.TECHNICAL)
    s.add_mitigation(RiskDimension.LEGAL)
    r = s.report()
    assert r.mitigated_count == 2
