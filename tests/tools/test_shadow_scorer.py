"""C10 — MISSING-024: Shadow-Score 18-metric discipline tests. I8."""
import pytest
from tools.shadow_score.shadow_scorer import ShadowScorer, METRIC_NAMES, ShadowMetric


def test_18_metrics_defined():
    assert len(METRIC_NAMES) == 18


def test_record_valid_metric():
    s = ShadowScorer()
    s.record("test_pass_rate", 0.95)
    assert "test_pass_rate" in s.get_all()


def test_record_invalid_metric_raises():
    s = ShadowScorer()
    with pytest.raises(ValueError):
        s.record("nonexistent_metric_xyz", 0.5)


def test_composite_requires_records():
    s = ShadowScorer()
    assert s.composite() == 0.0


def test_composite_all_metrics():
    s = ShadowScorer()
    for name in METRIC_NAMES:
        s.record(name, 0.8)
    assert 0.0 < s.composite() <= 1.0


def test_coverage_pct():
    s = ShadowScorer()
    for name in METRIC_NAMES[:9]:
        s.record(name, 0.5)
    assert s.coverage_pct() == pytest.approx(50.0)


def test_missing_metrics_tracked():
    s = ShadowScorer()
    s.record("test_pass_rate", 1.0)
    missing = s.missing_metrics()
    assert "test_pass_rate" not in missing
    assert len(missing) == 17


def test_lower_is_better_inverts_score():
    m = ShadowMetric("error_rate", 0.8, lower_is_better=True)
    assert m.normalized == pytest.approx(0.2)


def test_higher_is_better_keeps_score():
    m = ShadowMetric("test_pass_rate", 0.9, lower_is_better=False)
    assert m.normalized == pytest.approx(0.9)
