"""Tests for calibration telemetry pipeline and INS-06 modules."""
import pytest
import numpy as np
from services.calibration import (
    RunningBrier, BinnedECE, AURC, ChowThreshold, BrierSkillScore,
    emit_decision, compute_metrics, classify_band,
)
from services.calibration.metrics import (
    brier_score, brier_decomposition, ece, aurc as aurc_metric, risk_coverage_curve,
)
from services.calibration.sft import sft_temperature_loop
from services.calibration.selective import chow_optimal_threshold, selective_predict, selective_risk

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

# --- metrics module ---

def test_metrics_brier_score_binary():
    assert brier_score(np.ones(100), np.ones(100, dtype=int)) == pytest.approx(0.0)
    assert brier_score(np.full(100, 0.5), np.zeros(100, dtype=int)) == pytest.approx(0.25)

def test_metrics_brier_decomposition_identity():
    rng = np.random.default_rng(7)
    p = rng.uniform(0, 1, 800)
    y = (rng.uniform(0, 1, 800) < p).astype(int)
    d = brier_decomposition(p, y, n_bins=15)
    assert abs(d["reliability"] - d["resolution"] + d["uncertainty"] - d["brier"]) < 0.05

def test_metrics_ece_well_calibrated():
    rng = np.random.default_rng(8)
    p = rng.uniform(0, 1, 2000)
    y = (rng.uniform(0, 1, 2000) < p).astype(int)
    assert ece(p, y, n_bins=15) < 0.06

def test_metrics_aurc_monotone_ascending():
    rng = np.random.default_rng(9)
    conf = rng.uniform(0, 1, 300)
    y = (rng.uniform(0, 1, 300) < conf).astype(int)
    curve = risk_coverage_curve(conf, y)
    coverages = [c["coverage"] for c in curve]
    assert coverages == sorted(coverages)

# --- sft module ---

def test_sft_T_decreases_from_overestimate():
    rng = np.random.default_rng(10)
    z = rng.normal(0, 1, 500)
    y = (z > 0).astype(int)
    temps = list(sft_temperature_loop(z, y, n_epochs=30, init_T=3.0, use_torch=False))
    assert temps[-1] < temps[0]

def test_sft_yields_n_epochs():
    rng = np.random.default_rng(11)
    z = rng.normal(0, 1, 100)
    y = (z > 0).astype(int)
    temps = list(sft_temperature_loop(z, y, n_epochs=20, init_T=2.0, use_torch=False))
    assert len(temps) == 20

# --- selective module ---

def test_selective_predict_abstain():
    p = np.array([0.9, 0.4, 0.3, 0.8])
    preds, abstain = selective_predict(p, threshold=0.5)
    assert abstain[1] and abstain[2]
    assert not abstain[0] and not abstain[3]

def test_selective_risk_high_threshold():
    p = np.array([0.9, 0.95, 0.85])
    y = np.array([1, 1, 1])
    r = selective_risk(p, y, threshold=0.8)
    assert r["risk"] == pytest.approx(0.0)
    assert r["coverage"] == pytest.approx(1.0)

def test_chow_optimal_coverage():
    rng = np.random.default_rng(12)
    conf = rng.uniform(0.5, 1.0, 200)
    y = (rng.uniform(0, 1, 200) < conf).astype(int)
    result = chow_optimal_threshold(conf, y, target_coverage=0.7)
    assert 0.0 <= result["threshold"] <= 1.0
    assert result["coverage"] >= 0.05
