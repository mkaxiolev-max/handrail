"""Tests for MASTER scorer v3.2 — AXIOLEV Holdings LLC © 2026.

Covers:
  - Weight-sum invariants (v3.1 and v3.2 must each sum to 1.0)
  - Per-instrument weight values for v3.2
  - Monotonicity: raising any instrument score must not lower the composite
  - Band threshold edges (exact boundary conditions)
  - I7 integration and its contribution direction
  - weighted_composite renormalization behaviour
"""
from __future__ import annotations

import sys
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.scoring.master_v32 import (
    WEIGHTS_V21,
    WEIGHTS_V30,
    WEIGHTS_V31,
    WEIGHTS_V32,
    PRIOR_SUPERMAX,
    classify_band,
    weighted_composite,
)


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def _best_live_scores() -> dict:
    """Best-live instrument scores from FINAL_MAX_CANONICAL_CERTIFICATION + I7."""
    return {
        "I1": 88.80,
        "I2": 89.74,
        "I3": 89.34,
        "I4": 97.88,
        "I5": 89.70,
        "I6": 95.97,
        "I7": 100.00,
    }


# --------------------------------------------------------------------------- #
# Weight-sum invariants
# --------------------------------------------------------------------------- #

def test_v31_weights_sum_to_one():
    total = sum(WEIGHTS_V31.values())
    assert abs(total - 1.0) < 1e-9, f"v3.1 weight sum = {total}"


def test_v32_weights_sum_to_one():
    total = sum(WEIGHTS_V32.values())
    assert abs(total - 1.0) < 1e-9, f"v3.2 weight sum = {total}"


def test_v32_has_seven_instruments():
    assert set(WEIGHTS_V32.keys()) == {"I1", "I2", "I3", "I4", "I5", "I6", "I7"}


def test_v32_individual_weights():
    assert abs(WEIGHTS_V32["I1"] - 0.1215) < 1e-9
    assert abs(WEIGHTS_V32["I2"] - 0.162) < 1e-9
    assert abs(WEIGHTS_V32["I3"] - 0.162) < 1e-9
    assert abs(WEIGHTS_V32["I4"] - 0.243) < 1e-9
    assert abs(WEIGHTS_V32["I5"] - 0.1215) < 1e-9
    assert abs(WEIGHTS_V32["I6"] - 0.090) < 1e-9
    assert abs(WEIGHTS_V32["I7"] - 0.100) < 1e-9


def test_v21_weights_sum_to_one():
    total = sum(WEIGHTS_V21.values())
    assert abs(total - 1.0) < 1e-9, f"v2.1 weight sum = {total}"


# --------------------------------------------------------------------------- #
# Monotonicity: raising any instrument must not decrease the composite
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("inst", list(WEIGHTS_V32.keys()))
def test_monotonicity_instrument(inst: str):
    """Raising an instrument score by 1 pt must strictly increase the composite."""
    s = _best_live_scores()
    before = weighted_composite(s, WEIGHTS_V32)
    s[inst] = min(100.0, s[inst] + 1.0)
    after = weighted_composite(s, WEIGHTS_V32)
    # If the instrument was already at 100 the composite cannot rise; otherwise it must.
    original = _best_live_scores()[inst]
    if original < 100.0:
        assert after > before, f"monotonicity failed for {inst}: {before} -> {after}"
    else:
        assert after >= before


def test_monotonicity_i7_from_low():
    """I7 going from 80 to 100 must raise the composite."""
    s = _best_live_scores()
    s["I7"] = 80.0
    low = weighted_composite(s, WEIGHTS_V32)
    s["I7"] = 100.0
    high = weighted_composite(s, WEIGHTS_V32)
    assert high > low


def test_monotonicity_all_instruments_jointly():
    """Raising every instrument by 1 pt must raise the composite."""
    s = _best_live_scores()
    before = weighted_composite(s, WEIGHTS_V32)
    s2 = {k: min(100.0, v + 1.0) for k, v in s.items()}
    after = weighted_composite(s2, WEIGHTS_V32)
    assert after >= before


# --------------------------------------------------------------------------- #
# Band threshold edges (exact boundary conditions)
# --------------------------------------------------------------------------- #

def test_band_exactly_at_90():
    assert classify_band(90.0) == "Approaching 90"


def test_band_just_below_90():
    assert classify_band(89.999) == "Below 90"


def test_band_just_below_93():
    assert classify_band(92.999) == "Approaching 90"


def test_band_exactly_at_93():
    assert classify_band(93.0) == "Certified 93"


def test_band_just_below_95():
    assert classify_band(94.999) == "Certified 93"


def test_band_exactly_at_95():
    assert classify_band(95.0) == "SuperMax 95"


def test_band_just_below_96():
    assert classify_band(95.999) == "SuperMax 95"


def test_band_exactly_at_96():
    assert classify_band(96.0) == "Transcendent 96"


def test_band_at_100():
    assert classify_band(100.0) == "Transcendent 96"


def test_band_at_zero():
    assert classify_band(0.0) == "Below 90"


# --------------------------------------------------------------------------- #
# I7 integration
# --------------------------------------------------------------------------- #

def test_v32_higher_than_v31_with_perfect_i7():
    """v3.2 must exceed v3.1 when I7=100 (positive I7 contribution)."""
    s = _best_live_scores()
    assert weighted_composite(s, WEIGHTS_V32) > weighted_composite(s, WEIGHTS_V31)


def test_v32_best_live_is_certified_93():
    """Best-live v3.2 composite must reach the Certified 93 band."""
    s = _best_live_scores()
    composite = weighted_composite(s, WEIGHTS_V32)
    assert composite >= 93.0, f"v3.2 = {composite}, below Certified 93 threshold"


def test_v32_exceeds_prior_supermax():
    """Best-live v3.2 must exceed the prior SUPERMAX benchmark (92.42)."""
    s = _best_live_scores()
    assert weighted_composite(s, WEIGHTS_V32) > PRIOR_SUPERMAX


def test_prior_supermax_value():
    assert PRIOR_SUPERMAX == 92.42


# --------------------------------------------------------------------------- #
# weighted_composite renormalization
# --------------------------------------------------------------------------- #

def test_renorm_missing_instrument():
    """If an instrument is absent from scores, weights renormalize correctly."""
    # Two instruments each at 90, weight dict covers three instruments
    scores = {"I1": 90.0, "I2": 90.0}
    w = {"I1": 0.5, "I2": 0.5, "I3": 0.5}   # I3 missing; raw sum would be 1.5
    result = weighted_composite(scores, w)
    # shared keys: I1, I2; shared weight sum = 1.0; result = (90*0.5 + 90*0.5)/1.0 = 90
    assert abs(result - 90.0) < 0.01


def test_renorm_perfect_scores_give_100():
    scores = {k: 100.0 for k in WEIGHTS_V32}
    assert abs(weighted_composite(scores, WEIGHTS_V32) - 100.0) < 0.01


def test_renorm_zero_scores_give_zero():
    scores = {k: 0.0 for k in WEIGHTS_V32}
    assert abs(weighted_composite(scores, WEIGHTS_V32) - 0.0) < 0.01
