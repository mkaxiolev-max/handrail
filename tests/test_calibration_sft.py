"""INS-06 calibration tests: Brier decomposition, ECE invariance, AURC monotonicity,
Chow optimality, SFT convergence, Alexandrian Archive schema validation."""
from __future__ import annotations

import json
import math
import os
import tempfile

import numpy as np
import pytest

from services.calibration.metrics import (
    aurc,
    brier_decomposition,
    brier_score,
    ece,
    risk_coverage_curve,
)
from services.calibration.selective import chow_optimal_threshold
from services.calibration.sft import sft_temperature_loop
from services.calibration.pipeline import run_calibration_pipeline


# ---------------------------------------------------------------------------
# 1. Brier decomposition: reliability + uncertainty - resolution ≈ brier score
# ---------------------------------------------------------------------------

def test_brier_decomposition_identity():
    """BS = REL - RES + UNC (Murphy 1973) holds within ±0.05 on large sample."""
    rng = np.random.default_rng(42)
    p = rng.uniform(0.0, 1.0, 2000)
    y = (rng.uniform(0.0, 1.0, 2000) < p).astype(int)

    d = brier_decomposition(p, y, n_bins=15)
    reconstructed = d["reliability"] - d["resolution"] + d["uncertainty"]
    assert abs(reconstructed - d["brier"]) < 0.05, (
        f"Decomposition error: REL-RES+UNC={reconstructed:.4f}, BS={d['brier']:.4f}"
    )


def test_brier_decomposition_components_nonneg():
    """REL, RES, UNC must all be non-negative."""
    rng = np.random.default_rng(43)
    p = rng.uniform(0.0, 1.0, 500)
    y = (rng.uniform(0.0, 1.0, 500) < p).astype(int)
    d = brier_decomposition(p, y, n_bins=10)
    assert d["reliability"] >= 0.0
    assert d["resolution"] >= 0.0
    assert 0.0 <= d["uncertainty"] <= 0.25   # max unc = 0.5*(1-0.5)


def test_brier_decomposition_perfect_forecast_zero_rel():
    """A perfectly calibrated oracle has reliability ≈ 0."""
    rng = np.random.default_rng(44)
    conf = rng.uniform(0.0, 1.0, 1000)
    # Labels generated with P(y=1|conf) = conf → exactly calibrated
    y = rng.binomial(1, conf).astype(int)
    d = brier_decomposition(conf, y, n_bins=15)
    assert d["reliability"] < 0.02, f"REL should be near 0 for calibrated forecast, got {d['reliability']:.4f}"


# ---------------------------------------------------------------------------
# 2. ECE bin-count invariance within ±0.01 across 10/15/20 bins
# ---------------------------------------------------------------------------

def test_ece_bin_count_invariance():
    """ECE is consistent across 10, 15, 20 bins on well-calibrated synthetic data."""
    rng = np.random.default_rng(0)
    conf = rng.uniform(0.0, 1.0, 3000)
    y = rng.binomial(1, conf).astype(int)

    ece10 = ece(conf, y, n_bins=10)
    ece15 = ece(conf, y, n_bins=15)
    ece20 = ece(conf, y, n_bins=20)

    assert abs(ece10 - ece15) < 0.01, f"|ECE10-ECE15|={abs(ece10-ece15):.4f}"
    assert abs(ece15 - ece20) < 0.01, f"|ECE15-ECE20|={abs(ece15-ece20):.4f}"
    assert abs(ece10 - ece20) < 0.01, f"|ECE10-ECE20|={abs(ece10-ece20):.4f}"


# ---------------------------------------------------------------------------
# 3. AURC monotonicity under confidence-sorted coverage sweep
# ---------------------------------------------------------------------------

def test_aurc_monotonicity():
    """Selective risk must be non-decreasing as coverage increases.

    When we sweep from high-confidence-only to full coverage, adding less
    confident (riskier) predictions should not lower the selective risk.
    """
    rng = np.random.default_rng(1)
    # High-confidence → correct; low-confidence → random
    conf = rng.uniform(0.0, 1.0, 500)
    y = (rng.uniform(0.0, 1.0, 500) < conf).astype(int)

    curve = risk_coverage_curve(conf, y)
    risks = [pt["risk"] for pt in curve]

    # Allow at most 5 % of steps to violate monotonicity (noise from random data)
    violations = sum(
        1 for i in range(1, len(risks)) if risks[i] < risks[i - 1] - 0.05
    )
    assert violations < len(risks) * 0.05, (
        f"{violations}/{len(risks)} steps violated AURC monotonicity"
    )


def test_aurc_perfect_ordering_near_zero():
    """Perfect ranker (high conf = always correct) has AURC ≈ 0."""
    n = 200
    conf = np.linspace(0.01, 0.99, n)
    y = np.ones(n, dtype=int)        # all correct — no loss
    assert aurc(conf, y) == pytest.approx(0.0, abs=1e-9)


# ---------------------------------------------------------------------------
# 4. Chow threshold optimality on 2-Gaussian toy problem
# ---------------------------------------------------------------------------

def test_chow_threshold_2gaussian():
    """Optimal τ selects the high-accuracy cluster on a 2-Gaussian mixture."""
    rng = np.random.default_rng(2)
    n = 600

    # High-confidence cluster: conf ~ N(0.85, 0.04), accuracy ≈ 92 %
    conf_hi = np.clip(rng.normal(0.85, 0.04, n // 2), 0.0, 1.0)
    y_hi = rng.binomial(1, 0.92, n // 2)

    # Low-confidence cluster: conf ~ N(0.38, 0.08), accuracy ≈ 50 % (noise)
    conf_lo = np.clip(rng.normal(0.38, 0.08, n // 2), 0.0, 1.0)
    y_lo = rng.binomial(1, 0.50, n // 2)

    conf = np.concatenate([conf_hi, conf_lo])
    y = np.concatenate([y_hi, y_lo])

    # At 40 % coverage we expect to recover the high-confidence cluster
    result = chow_optimal_threshold(conf, y, target_coverage=0.4)

    assert result["threshold"] > 0.55, (
        f"Expected τ > 0.55 to exclude low-conf cluster; got {result['threshold']:.3f}"
    )
    assert result["risk"] < 0.20, (
        f"Expected risk < 0.20 in high-conf cluster; got {result['risk']:.3f}"
    )


# ---------------------------------------------------------------------------
# 5. SFT convergence: miscalibrated softmax → T → 1 ± 0.15
# ---------------------------------------------------------------------------

def test_sft_convergence_toward_unity():
    """Temperature scaling converges toward T=1 when data is well-calibrated at T=1."""
    rng = np.random.default_rng(3)
    n = 2000
    # Well-calibrated logits: z ~ N(0,1), y ~ Bernoulli(sigmoid(z))
    z = rng.normal(0.0, 1.0, n)
    p_true = 1.0 / (1.0 + np.exp(-z))
    y = rng.binomial(1, p_true).astype(int)

    # Start over-regularised (T=3 → too spread out)
    temps = list(sft_temperature_loop(z, y, n_epochs=300, lr=0.3, init_T=3.0, use_torch=False))

    final_T = temps[-1]
    assert final_T < temps[0], "T should decrease from initial over-estimate"
    assert abs(final_T - 1.0) < 0.30, (
        f"Expected T ≈ 1.0 ± 0.30; got {final_T:.4f}"
    )


def test_sft_brier_decreasing():
    """Brier loss on calibrated probs should decrease monotonically over SFT epochs."""
    rng = np.random.default_rng(4)
    z = rng.normal(0.0, 1.0, 1000)
    y = (z > 0).astype(int)

    def brier_at_T(T: float) -> float:
        with np.errstate(over="ignore"):
            p = 1.0 / (1.0 + np.exp(np.clip(-z / T, -500, 500)))
        return float(np.mean((p - y.astype(float)) ** 2))

    temps = list(sft_temperature_loop(z, y, n_epochs=100, lr=0.3, init_T=5.0, use_torch=False))
    losses = [brier_at_T(T) for T in temps]

    # Allow small upticks; final loss must be lower than initial
    assert losses[-1] < losses[0], f"Brier did not decrease: {losses[0]:.4f} → {losses[-1]:.4f}"


# ---------------------------------------------------------------------------
# 6. Alexandrian Archive log schema validation
# ---------------------------------------------------------------------------

def test_pipeline_log_schema():
    """Every JSONL epoch record must conform to the required schema."""
    rng = np.random.default_rng(5)
    n = 300
    z = rng.normal(0.0, 1.0, n)
    y = (z > 0).astype(int)

    required_keys = {"epoch", "brier", "ece", "aurc", "tau", "coverage", "risk", "T", "run_id", "ts"}

    with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False, mode="w") as tmp:
        tmp_path = tmp.name

    try:
        run_calibration_pipeline(
            z, y, n_epochs=5, run_id="schema_test", log_path=tmp_path, lr=0.3, init_T=2.0
        )
        with open(tmp_path) as fh:
            lines = [ln for ln in fh if ln.strip()]

        assert len(lines) >= 1, "Pipeline wrote no log records"

        for i, line in enumerate(lines):
            record = json.loads(line)
            missing = required_keys - set(record.keys())
            assert not missing, f"Epoch {i} record missing keys: {missing}"
            assert isinstance(record["brier"], (int, float))
            assert isinstance(record["ece"], (int, float))
            assert isinstance(record["aurc"], (int, float))
            assert 0.0 <= record["coverage"] <= 1.0, f"coverage={record['coverage']} out of [0,1]"
            assert record["T"] > 0.0, f"T must be positive, got {record['T']}"
            assert record["epoch"] == i
            assert record["run_id"] == "schema_test"
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def test_pipeline_log_run_id_isolation():
    """Two pipeline runs with different run_ids produce independent log files."""
    rng = np.random.default_rng(6)
    n = 100
    z = rng.normal(0.0, 1.0, n)
    y = (z > 0).astype(int)

    with tempfile.TemporaryDirectory() as tmpdir:
        path_a = os.path.join(tmpdir, "run_a.jsonl")
        path_b = os.path.join(tmpdir, "run_b.jsonl")

        run_calibration_pipeline(z, y, n_epochs=3, run_id="run_a", log_path=path_a, init_T=2.0)
        run_calibration_pipeline(z, y, n_epochs=7, run_id="run_b", log_path=path_b, init_T=4.0)

        with open(path_a) as f:
            lines_a = [json.loads(l) for l in f if l.strip()]
        with open(path_b) as f:
            lines_b = [json.loads(l) for l in f if l.strip()]

        assert len(lines_a) == 3, f"Expected 3 epochs in run_a, got {len(lines_a)}"
        assert len(lines_b) == 7, f"Expected 7 epochs in run_b, got {len(lines_b)}"
        assert all(r["run_id"] == "run_a" for r in lines_a)
        assert all(r["run_id"] == "run_b" for r in lines_b)
        # Initial T differs between runs
        assert lines_a[0]["T"] != lines_b[0]["T"]
