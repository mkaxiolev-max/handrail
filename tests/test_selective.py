"""Q7 — AURC/Chow tests."""
from services.selective import aurc, chow_tau_abstain, risk_coverage_curve

def test_perfect_confidence_low_aurc():
    conf   = [0.99, 0.98, 0.97, 0.96]
    corr   = [1,    1,    1,    1   ]
    assert aurc(conf, corr) < 0.01

def test_inverse_confidence_high_aurc():
    conf   = [0.9, 0.8, 0.7, 0.6]
    corr   = [0,   0,   1,   1  ]
    a = aurc(conf, corr)
    assert a > 0.3

def test_chow_abstains_below_tau():
    assert     chow_tau_abstain(0.5, 0.7)
    assert not chow_tau_abstain(0.9, 0.7)
