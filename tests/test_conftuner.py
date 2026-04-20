"""Q6 — ConfTuner tests."""
from services.conftuner import ConfSample, tokenized_brier, ece, trainer_hook

def _samples():
    return [
        ConfSample("a","a",0.9),
        ConfSample("b","b",0.8),
        ConfSample("c","x",0.2),   # correctly low-conf on wrong answer
        ConfSample("d","d",0.95),
    ]

def test_brier_low_for_good_calib():
    assert tokenized_brier(_samples()) < 0.1

def test_brier_high_for_bad_calib():
    bad = [ConfSample("a","x",0.99), ConfSample("b","y",0.99)]
    assert tokenized_brier(bad) > 0.9

def test_ece_bounded():
    e = ece(_samples())
    assert 0.0 <= e <= 1.0

def test_trainer_hook_shape():
    p = trainer_hook(_samples())
    assert {"loss_tokenized_brier","ece","n"}.issubset(p.keys())
