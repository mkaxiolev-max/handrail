import pytest
from services.aletheia_control.scoring import omega_score, rubric_score, RUBRIC, WEIGHTS

def test_weights_sum_to_one():
    assert abs(sum(WEIGHTS.values()) - 1.0) < 1e-9

def test_omega_score_range():
    sub = {k: 0.9 for k in WEIGHTS}
    s = omega_score(sub); assert 0.0 <= s <= 1.0; assert s == pytest.approx(0.9, abs=1e-3)

def test_rubric_total_caps_at_100():
    perfect = {k: (target+0.1 if op==">=" else max(target-0.01, 0.0))
               for k,(_,target,op) in RUBRIC.items()}
    r = rubric_score(perfect); assert r["__total__"] <= 100.0; assert r["__total__"] >= 99.0
