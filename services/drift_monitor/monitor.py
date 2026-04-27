"""Drift Monitor — PSI, ADWIN, Page-Hinkley drift detection."""
from __future__ import annotations
import math
from dataclasses import dataclass, field
from typing import Sequence


@dataclass
class DriftAlert:
    detector: str
    detected: bool
    magnitude: float
    sample_count: int


# --- PSI (Population Stability Index) ---
def psi(expected: Sequence[float], actual: Sequence[float], buckets: int = 10) -> float:
    """Compute PSI. < 0.1 stable, 0.1–0.2 minor drift, > 0.2 significant drift."""
    if len(expected) < buckets or len(actual) < buckets:
        return 0.0
    min_v = min(min(expected), min(actual))
    max_v = max(max(expected), max(actual)) + 1e-9
    bucket_size = (max_v - min_v) / buckets
    exp_counts = [0] * buckets
    act_counts = [0] * buckets
    for v in expected:
        idx = min(int((v - min_v) / bucket_size), buckets - 1)
        exp_counts[idx] += 1
    for v in actual:
        idx = min(int((v - min_v) / bucket_size), buckets - 1)
        act_counts[idx] += 1
    result = 0.0
    n_exp, n_act = len(expected), len(actual)
    for e, a in zip(exp_counts, act_counts):
        ep = max(e / n_exp, 1e-9)
        ap = max(a / n_act, 1e-9)
        result += (ap - ep) * math.log(ap / ep)
    return round(result, 6)


# --- ADWIN (simplified sliding window) ---
class ADWIN:
    def __init__(self, delta: float = 0.002):
        self._delta = delta
        self._window: list[float] = []
        self._total_drift_detected = 0

    def add_element(self, value: float) -> bool:
        self._window.append(value)
        if len(self._window) < 20:
            return False
        n = len(self._window)
        half = n // 2
        mean_a = sum(self._window[:half]) / half
        mean_b = sum(self._window[half:]) / (n - half)
        drift = abs(mean_a - mean_b) > self._delta * 10
        if drift:
            self._total_drift_detected += 1
            self._window = self._window[half:]
        return drift

    def drift_count(self) -> int:
        return self._total_drift_detected


# --- Page-Hinkley ---
class PageHinkley:
    def __init__(self, threshold: float = 50.0, alpha: float = 0.9999):
        self._threshold = threshold
        self._alpha = alpha
        self._sum = 0.0
        self._min_sum = float("inf")
        self._n = 0
        self._mean = 0.0

    def add_element(self, value: float) -> bool:
        self._n += 1
        self._mean = self._mean + (value - self._mean) / self._n
        self._sum += value - self._mean - self._alpha
        self._min_sum = min(self._min_sum, self._sum)
        return (self._sum - self._min_sum) > self._threshold


class DriftMonitor:
    def __init__(self):
        self._adwin = ADWIN()
        self._ph = PageHinkley()
        self._samples: list[float] = []
        self._alerts: list[DriftAlert] = []

    def add_sample(self, value: float) -> list[DriftAlert]:
        self._samples.append(value)
        alerts = []
        if self._adwin.add_element(value):
            a = DriftAlert("adwin", True, abs(value - sum(self._samples) / len(self._samples)),
                           len(self._samples))
            self._alerts.append(a)
            alerts.append(a)
        if self._ph.add_element(value):
            a = DriftAlert("page_hinkley", True, abs(value), len(self._samples))
            self._alerts.append(a)
            alerts.append(a)
        return alerts

    def compute_psi(self, reference: list[float]) -> float:
        return psi(reference, self._samples)

    def alert_count(self) -> int:
        return len(self._alerts)
