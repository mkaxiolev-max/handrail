"""Spike detection primitives — pure functions."""
from __future__ import annotations

from typing import List


def detect_spike(rates: List[float], multiplier: float = 2.0) -> bool:
    """True if latest rate is multiplier× the rolling mean of prior rates."""
    if len(rates) < 2:
        return False
    prior = rates[:-1]
    mean = sum(prior) / len(prior)
    if mean == 0:
        return rates[-1] > 0
    return rates[-1] >= mean * multiplier


class SpikeDetector:
    def __init__(self, window: int = 10, multiplier: float = 2.0):
        self._window = window
        self._multiplier = multiplier
        self._history: List[float] = []

    def record(self, rate: float) -> bool:
        self._history.append(rate)
        if len(self._history) > self._window:
            self._history = self._history[-self._window:]
        return detect_spike(self._history, self._multiplier)
