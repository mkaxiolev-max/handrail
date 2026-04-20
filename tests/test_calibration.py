"""Tests for calibration telemetry pipeline."""
import pytest
from services.calibration import (
    RunningBrier, BinnedECE, AURC, ChowThreshold, BrierSkillScore,
    emit_decision, compute_metrics, classify_band,
)

def test_classify_band():
    assert classify_band(20) == "BLOCK"
    assert classify_band(50) == "REVIEW"
    assert classify_band(70) == "PASS"
    assert classify_band(85) == "HIGH_ASSURANCE"

def test_running_brier_perfect():
    b = RunningBrier()
    for _ in range(100): b.update(1.0, 1)
    assert b.mean == pytest.approx(0.0)

def test_running_brier_chance():
    b = RunningBrier()
    for i in range(100): b.update(0.5, i % 2)
    assert b.mean == pytest.approx(0.25, abs=0.01)

def test_running_brier_drift():
    b = RunningBrier(lam=0.1)
    for _ in range(200): b.update(0.9, 1)
    baseline_mean = b.mean
    for _ in range(50): b.update(0.9, 0)
    assert b.ewma > baseline_mean

def test_ece_perfect_calibration():
    ece = BinnedECE(n_bins=10)
    for i in range(1000): ece.update(0.5, i % 2)
    r = ece.compute()
    assert r["ece"] < 0.05

def test_ece_miscalibration():
    ece = BinnedECE(n_bins=10)
    for _ in range(1000): ece.update(0.9, 0)
    r = ece.compute()
    assert r["ece"] > 0.8

def test_aurc_perfect():
    aurc = AURC()
    for i in range(100): aurc.update(i/100, 1)
    assert aurc.compute() == pytest.approx(0.0)

def test_chow_sane():
    aurc = AURC()
    for i in range(100):
        aurc.update(i/100, 1 if i/100 > 0.5 else 0)
    chow = ChowThreshold(min_coverage=0.3, max_reject_rate=0.5)
    r = chow.optimal(aurc)
    assert 0.0 <= r["threshold"] <= 1.0

def test_bss_positive():
    b = RunningBrier()
    for i in range(200): b.update(0.9 if i%2 else 0.1, i%2)
    assert BrierSkillScore(b, 0.5).compute() > 0

def test_emit_decision():
    rec = emit_decision("d1", "t1", 0.85, outcome=1)
    assert rec.band == "HIGH_ASSURANCE"
    assert rec.brier_instant == pytest.approx(0.0225, abs=0.001)

def test_compute_metrics_schema():
    for i in range(50): emit_decision(f"d{i}", f"t{i}", 0.7, outcome=(i%3!=0))
    m = compute_metrics()
    assert {"brier_mean","ece","mce","aurc","chow_tau","bss"}.issubset(m.keys())
