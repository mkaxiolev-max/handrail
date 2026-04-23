"""Hormetic B0..B5 UOIE sweep expansion tests.

Covers:
  - Every pressure level (B0..B5) metrics correctness
  - SweepClassifier boundary cases for all four phase labels
  - Golden-trajectory regression
  - I3 admin ceiling enforcement
  - Lineage Fabric receipt emission
  - Artifact JSON structure
  - ProfileClassifier (legacy gpx_omega.profiler — must stay green)
© 2026 AXIOLEV Holdings LLC
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import List

import pytest

from services.gpx_omega.profiler import ProfileClassifier
from services.gpx_omega.profiler import Signature as ProfileSignature
from services.hormetic import (
    I3_CEILING,
    UOIE_PACK,
    SweepClassifier,
    SweepLabel,
    run_uoie_sweep,
)
from services.hormetic.sweep import HormeticBand, _band_variance


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _perfect_model(prompt: str) -> str:
    """Always returns the expected answer token for every UOIE fixture."""
    # Strip [reset] tag so B5 clean-reset fixtures still get correct answers.
    clean = prompt.replace("[reset] ", "")
    for fx in UOIE_PACK:
        if fx.prompt == prompt or fx.prompt.replace("[reset] ", "") == clean:
            return fx.expected_answer
    return "yes"


def _failing_model(prompt: str) -> str:
    """Never matches any expected answer."""
    return "WRONG_ANSWER_XYZ"


def _band_model(scores_by_band: dict) -> object:
    """Returns a callable whose per-band correctness follows the given map.

    scores_by_band: {0: 1.0, 1: 0.75, ...} — fraction correct per band.
    Within a band the first ceil(n * frac) fixtures return the right answer.
    """
    import math

    def _callable(prompt: str) -> str:
        for fx in UOIE_PACK:
            if fx.prompt == prompt:
                band = int(fx.band)
                frac = scores_by_band.get(band, 0.0)
                band_fixtures = [f for f in UOIE_PACK if int(f.band) == band]
                idx = band_fixtures.index(fx)
                cutoff = math.ceil(len(band_fixtures) * frac)
                if idx < cutoff:
                    return fx.expected_answer
                return "wrong"
        return "wrong"

    return _callable


# ---------------------------------------------------------------------------
# 1. UOIE pack structure
# ---------------------------------------------------------------------------

def test_uoie_pack_size():
    assert len(UOIE_PACK) == 24


def test_uoie_pack_four_per_band():
    for b in range(6):
        count = sum(1 for fx in UOIE_PACK if int(fx.band) == b)
        assert count == 4, f"Expected 4 fixtures for B{b}, got {count}"


def test_uoie_pack_bands_b0_to_b5():
    bands = {int(fx.band) for fx in UOIE_PACK}
    assert bands == {0, 1, 2, 3, 4, 5}


# ---------------------------------------------------------------------------
# 2. Every band metrics (B0..B5) — perfect model
# ---------------------------------------------------------------------------

def test_all_bands_present_in_result():
    result = run_uoie_sweep(_perfect_model, run_id="t-allbands", model_name="test")
    assert set(result.band_metrics.keys()) == {0, 1, 2, 3, 4, 5}
    assert len(result.trajectory) == 6


def test_perfect_model_all_bands_at_ceiling():
    # Perfect model gets 100 % correct but I3_CEILING clamps the reported score.
    result = run_uoie_sweep(_perfect_model, run_id="t-perfect")
    for b in range(6):
        assert result.band_metrics[b].score == pytest.approx(I3_CEILING)


def test_failing_model_all_bands_zero():
    result = run_uoie_sweep(_failing_model, run_id="t-fail")
    for b in range(6):
        assert result.band_metrics[b].score == 0.0


# ---------------------------------------------------------------------------
# 3. I3 admin ceiling enforcement
# ---------------------------------------------------------------------------

def test_i3_ceiling_clamps_score():
    """A model that exceeds 95 % correct cannot report above I3_CEILING."""
    assert I3_CEILING == 95.0
    result = run_uoie_sweep(_perfect_model, run_id="t-ceiling")
    for bm in result.band_metrics.values():
        assert bm.score <= I3_CEILING


# ---------------------------------------------------------------------------
# 4. Band metric fields — adaptation_rate and recovery_time
# ---------------------------------------------------------------------------

def test_adaptation_rate_b0_is_zero():
    result = run_uoie_sweep(_perfect_model, run_id="t-ar-b0")
    assert result.band_metrics[0].adaptation_rate == 0.0


def test_adaptation_rate_b1_equals_delta():
    result = run_uoie_sweep(_perfect_model, run_id="t-ar-b1")
    b0 = result.band_metrics[0].score
    b1 = result.band_metrics[1].score
    assert result.band_metrics[1].adaptation_rate == pytest.approx(b1 - b0)


def test_recovery_time_one_when_b5_gte_b0():
    """Perfect model: B5 == B0 == 100 → recovery_time = 1."""
    result = run_uoie_sweep(_perfect_model, run_id="t-rt-ok")
    assert result.band_metrics[5].recovery_time == 1


def test_recovery_time_none_when_not_recovered():
    """B0 perfect, B5 zero → B5 < B0 → recovery_time = None (not recovered)."""
    # Use _band_model so B5=0 is enforced independently of prompt text
    # (B5 fixtures reuse B0 prompts, so a prompt-based check can't distinguish them).
    model = _band_model({0: 1.0, 1: 1.0, 2: 1.0, 3: 1.0, 4: 1.0, 5: 0.0})
    result = run_uoie_sweep(model, run_id="t-rt-none")
    assert result.band_metrics[5].recovery_time is None


# ---------------------------------------------------------------------------
# 5. Post-sweep drift
# ---------------------------------------------------------------------------

def test_post_sweep_drift_zero_for_perfect():
    result = run_uoie_sweep(_perfect_model, run_id="t-drift-zero")
    assert result.post_sweep_drift == pytest.approx(0.0)


def test_post_sweep_drift_propagated_to_all_bands():
    result = run_uoie_sweep(_perfect_model, run_id="t-drift-prop")
    expected = result.post_sweep_drift
    for bm in result.band_metrics.values():
        assert bm.post_sweep_drift == pytest.approx(expected)


# ---------------------------------------------------------------------------
# 6. Variance helper
# ---------------------------------------------------------------------------

def test_band_variance_uniform():
    """All same correct value → variance == 0."""
    assert _band_variance([1.0, 1.0, 1.0, 1.0]) == pytest.approx(0.0)


def test_band_variance_mixed():
    vals = [1.0, 0.0, 1.0, 0.0]
    expected = 0.25  # mean=0.5, sum of (x-0.5)^2 / 4 = 0.25
    assert _band_variance(vals) == pytest.approx(expected)


# ---------------------------------------------------------------------------
# 7. SweepClassifier — all four labels + boundary cases
# ---------------------------------------------------------------------------

def test_classifier_fragile_positive_drift():
    c = SweepClassifier(gain_threshold=10.0, drift_epsilon=5.0)
    # drift = +6 > epsilon → Fragile
    traj = [70.0, 72.0, 75.0, 80.0, 82.0, 76.0]  # b5-b0 = +6
    assert c.classify(traj) == SweepLabel.FRAGILE


def test_classifier_fragile_negative_drift():
    c = SweepClassifier(gain_threshold=10.0, drift_epsilon=5.0)
    # drift = -6 < -epsilon → Fragile
    traj = [80.0, 75.0, 72.0, 68.0, 65.0, 74.0]  # b5-b0 = -6
    assert c.classify(traj) == SweepLabel.FRAGILE


def test_classifier_super_gnoseogenic():
    c = SweepClassifier(gain_threshold=10.0, drift_epsilon=5.0)
    # peak = 85 (B4), b0 = 70 → gain = 15 > 10, drift = b5-b0 = 2 < 5
    traj = [70.0, 74.0, 78.0, 82.0, 85.0, 72.0]
    assert c.classify(traj) == SweepLabel.SUPER_GNOSEOGENIC


def test_classifier_generative():
    c = SweepClassifier(gain_threshold=10.0, drift_epsilon=5.0)
    # peak = 75 (B2), b0 = 70 → gain = 5 (> 0 but <= 10), drift = 1
    traj = [70.0, 73.0, 75.0, 72.0, 71.0, 71.0]
    assert c.classify(traj) == SweepLabel.GENERATIVE


def test_classifier_plastic():
    c = SweepClassifier(gain_threshold=10.0, drift_epsilon=5.0)
    # peak = b0 → gain = 0, drift = 0 → Plastic
    traj = [80.0, 79.0, 78.0, 77.0, 76.0, 80.0]
    assert c.classify(traj) == SweepLabel.PLASTIC


def test_classifier_boundary_gain_exactly_threshold_is_super_gnoseogenic():
    """gain == threshold is NOT > threshold → Generative (not Super-Gnoseogenic)."""
    c = SweepClassifier(gain_threshold=10.0, drift_epsilon=5.0)
    traj = [70.0, 73.0, 76.0, 79.0, 80.0, 72.0]  # peak=80, gain=10, drift=2
    # gain == 10 is not > 10, so Generative
    assert c.classify(traj) == SweepLabel.GENERATIVE


def test_classifier_boundary_drift_at_epsilon_is_not_fragile():
    """drift == epsilon exactly is NOT > epsilon → not Fragile."""
    c = SweepClassifier(gain_threshold=10.0, drift_epsilon=5.0)
    # b5 - b0 = exactly 5.0 → should not be Fragile
    traj = [70.0, 71.0, 72.0, 73.0, 74.0, 75.0]  # drift = 5.0
    label = c.classify(traj)
    assert label != SweepLabel.FRAGILE


def test_classifier_wrong_trajectory_length():
    c = SweepClassifier()
    with pytest.raises(ValueError, match="exactly 6"):
        c.classify([70.0, 80.0, 90.0])


def test_classifier_explicit_drift_overrides_trajectory():
    c = SweepClassifier(gain_threshold=10.0, drift_epsilon=5.0)
    # trajectory drift would be 0, but we pass drift=10 → Fragile
    traj = [70.0, 72.0, 74.0, 76.0, 78.0, 70.0]
    assert c.classify(traj, post_sweep_drift=10.0) == SweepLabel.FRAGILE


# ---------------------------------------------------------------------------
# 8. Artifact emission
# ---------------------------------------------------------------------------

def test_artifact_written_to_disk():
    with tempfile.TemporaryDirectory() as tmp:
        result = run_uoie_sweep(
            _perfect_model,
            run_id="t-artifact",
            artifacts_dir=Path(tmp),
        )
        artifact = Path(tmp) / "hormetic_sweep_t-artifact.json"
        assert artifact.exists()
        payload = json.loads(artifact.read_text())
        assert payload["run_id"] == "t-artifact"
        assert len(payload["trajectory"]) == 6
        assert "band_metrics" in payload
        assert payload["i3_ceiling"] == 95.0


# ---------------------------------------------------------------------------
# 9. Golden-trajectory regression
# ---------------------------------------------------------------------------

GOLDEN_TRAJECTORY = [70.0, 73.0, 79.0, 84.0, 88.0, 71.0]
# peak=88 (B4), b0=70, gain=18>10, b5=71, drift=+1 < 5 → Super-Gnoseogenic

def test_golden_trajectory_label():
    c = SweepClassifier()
    assert c.classify(GOLDEN_TRAJECTORY) == SweepLabel.SUPER_GNOSEOGENIC


def test_golden_trajectory_net_gain():
    b0, b5 = GOLDEN_TRAJECTORY[0], GOLDEN_TRAJECTORY[5]
    peak = max(GOLDEN_TRAJECTORY[:5])
    assert peak - b0 == pytest.approx(18.0)
    assert b5 - b0 == pytest.approx(1.0)


def test_golden_trajectory_fragile_when_drift_blown():
    c = SweepClassifier(drift_epsilon=0.5)  # tighter epsilon
    assert c.classify(GOLDEN_TRAJECTORY) == SweepLabel.FRAGILE


# ---------------------------------------------------------------------------
# 10. Lineage Fabric receipt emission
# ---------------------------------------------------------------------------

class _FakeLineage:
    def __init__(self):
        self.events: list = []

    def append_lineage_event(self, event: dict) -> None:
        self.events.append(event)


def test_lineage_band_events_emitted():
    lineage = _FakeLineage()
    run_uoie_sweep(_perfect_model, run_id="t-lineage", lineage=lineage)
    band_events = [e for e in lineage.events if e["type"] == "hormetic_sweep_band"]
    assert len(band_events) == 6
    assert {e["band"] for e in band_events} == {0, 1, 2, 3, 4, 5}


def test_lineage_complete_event_emitted():
    lineage = _FakeLineage()
    run_uoie_sweep(_perfect_model, run_id="t-lineage-complete", lineage=lineage)
    complete = [e for e in lineage.events if e["type"] == "hormetic_sweep_complete"]
    assert len(complete) == 1
    assert complete[0]["run_id"] == "t-lineage-complete"
    assert len(complete[0]["trajectory"]) == 6


def test_lineage_not_required():
    result = run_uoie_sweep(_perfect_model, run_id="t-no-lineage", lineage=None)
    assert result.run_id == "t-no-lineage"


# ---------------------------------------------------------------------------
# 11. Legacy ProfileClassifier (services.gpx_omega.profiler) — must stay green
# ---------------------------------------------------------------------------

def test_legacy_super_gnoseogenic_profile():
    c = ProfileClassifier()
    assert c.classify({0: 60, 1: 65, 2: 72, 3: 82, 4: 90, 5: 80}) == ProfileSignature.SUPER_GNOSEOGENIC


def test_legacy_brittle_profile():
    c = ProfileClassifier()
    assert c.classify({0: 90, 1: 80, 2: 70, 3: 60, 4: 50, 5: 40}) == ProfileSignature.BRITTLE


def test_legacy_plastic_or_generative_profile():
    c = ProfileClassifier()
    sig = c.classify({0: 80, 1: 82, 2: 78, 3: 75, 4: 72, 5: 79})
    assert sig in (ProfileSignature.PLASTIC, ProfileSignature.GENERATIVE)
