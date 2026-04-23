"""Sweep trajectory classifier for the B0..B5 UOIE hormetic sweep.

Given a 6-element trajectory [b0_score .. b5_score] and the signed
post-sweep baseline drift (b5 - b0), emits one of four phase labels:

  Super-Gnoseogenic — net knowledge gain > GAIN_THRESHOLD, drift ≤ DRIFT_EPSILON
  Generative        — net knowledge gain > 0, drift ≤ DRIFT_EPSILON
  Plastic           — recovery only (no net gain), drift ≤ DRIFT_EPSILON
  Fragile           — |post-sweep drift| > DRIFT_EPSILON — fails the phase

"Net knowledge gain" is defined as (peak_score over B0..B4) minus B0_score,
so it captures whether any pressure band improved the system's performance
relative to its clean baseline.

Thresholds are constructor-injectable for testing; defaults are canonical.

© 2026 AXIOLEV Holdings LLC
"""
from __future__ import annotations

from typing import List, Optional

# ---------------------------------------------------------------------------
# Canonical thresholds
# ---------------------------------------------------------------------------

GAIN_THRESHOLD: float = 10.0  # score-point gain separating Super-Gnoseogenic from Generative
DRIFT_EPSILON: float = 5.0    # max |post-sweep drift| before Fragile classification


# ---------------------------------------------------------------------------
# Label constants
# ---------------------------------------------------------------------------

class SweepLabel:
    SUPER_GNOSEOGENIC = "Super-Gnoseogenic"
    GENERATIVE = "Generative"
    PLASTIC = "Plastic"
    FRAGILE = "Fragile"

    _ALL = frozenset([SUPER_GNOSEOGENIC, GENERATIVE, PLASTIC, FRAGILE])

    @classmethod
    def is_valid(cls, label: str) -> bool:
        return label in cls._ALL


# ---------------------------------------------------------------------------
# Classifier
# ---------------------------------------------------------------------------

class SweepClassifier:
    """Classify a B0..B5 score trajectory into a sweep phase label.

    Parameters
    ----------
    gain_threshold:
        Minimum net score gain (peak[B0..B4] - B0) for Super-Gnoseogenic.
        Default: 10.0 score points.
    drift_epsilon:
        Maximum absolute post-sweep drift (|b5 - b0|) before Fragile.
        Default: 5.0 score points.
    """

    def __init__(
        self,
        gain_threshold: float = GAIN_THRESHOLD,
        drift_epsilon: float = DRIFT_EPSILON,
    ) -> None:
        self.gain_threshold = gain_threshold
        self.drift_epsilon = drift_epsilon

    def classify(
        self,
        trajectory: List[float],
        post_sweep_drift: Optional[float] = None,
    ) -> str:
        """Classify a sweep trajectory into a phase label.

        Parameters
        ----------
        trajectory:
            List of exactly 6 floats: [b0_score, b1_score, ..., b5_score].
        post_sweep_drift:
            Pre-computed signed drift value (b5 - b0).  If None it is
            derived from trajectory[5] - trajectory[0].

        Returns
        -------
        str
            One of: "Super-Gnoseogenic", "Generative", "Plastic", "Fragile".

        Raises
        ------
        ValueError
            If trajectory does not contain exactly 6 elements.
        """
        if len(trajectory) != 6:
            raise ValueError(
                f"trajectory must have exactly 6 elements (B0..B5); got {len(trajectory)}"
            )

        b0 = trajectory[0]
        b5 = trajectory[5]

        if post_sweep_drift is None:
            post_sweep_drift = b5 - b0

        # Peak over B0..B4 (B5 is recovery — excluded from gain calculation)
        peak = max(trajectory[:5])
        net_gain = peak - b0

        # Fragile overrides all: excessive drift fails the phase regardless of gain.
        if abs(post_sweep_drift) > self.drift_epsilon:
            return SweepLabel.FRAGILE

        if net_gain > self.gain_threshold:
            return SweepLabel.SUPER_GNOSEOGENIC

        if net_gain > 0:
            return SweepLabel.GENERATIVE

        return SweepLabel.PLASTIC
