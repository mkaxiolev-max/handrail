"""Gnoseogenic drift detection — drift caused by classification itself.

Adjacent literature: concept drift (Lu et al., IEEE TKDE 2020); semantic drift
(Stavropoulos et al.); ontological drift (Wang/Tordai).
"""
from __future__ import annotations
from collections import Counter
from typing import List
from .models import ControlClassification, ControlCircle

def circle_distribution(window: List[ControlClassification]) -> dict:
    c = Counter(x.circle for x in window)
    n = max(len(window), 1)
    return {k.value: c[k]/n for k in ControlCircle}

def drift_score(prev: List[ControlClassification], cur: List[ControlClassification]) -> float:
    """L1 distance between distributions; ≤0.05 is target."""
    p, q = circle_distribution(prev), circle_distribution(cur)
    return round(0.5 * sum(abs(p[k]-q[k]) for k in p), 4)

def is_drifting(prev, cur, threshold: float = 0.05) -> bool:
    return drift_score(prev, cur) > threshold
