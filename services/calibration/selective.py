"""Chow (1970) selective prediction with learned abstention threshold. © 2026 AXIOLEV Holdings LLC

Abstain when max_confidence < τ. τ is chosen to minimise cost at target coverage c.
"""
from __future__ import annotations

import math
from typing import Dict, Optional, Tuple

import numpy as np


def chow_optimal_threshold(
    probs: np.ndarray,
    labels: np.ndarray,
    target_coverage: float = 0.8,
    c_error: float = 4.0,
    c_reject: float = 1.0,
    min_coverage: float = 0.05,
) -> Dict[str, float]:
    """Find the Chow threshold τ that minimises cost at (approximately) target_coverage.

    Cost = c_error * risk * coverage + c_reject * (1 - coverage)

    The search scans all unique confidence thresholds and picks the τ that
    minimises cost subject to coverage >= min_coverage.

    Args:
        probs:           (N,) binary probabilities or (N, C) multiclass.
        labels:          (N,) integer labels.
        target_coverage: Desired fraction of predictions to retain.
        c_error:         Cost of a wrong prediction (default 4.0).
        c_reject:        Cost of abstaining (default 1.0).
        min_coverage:    Hard lower bound on coverage.

    Returns:
        dict with keys: threshold, coverage, risk.
    """
    p = np.asarray(probs, dtype=float)
    y = np.asarray(labels, dtype=int)

    conf = p.max(axis=1) if p.ndim > 1 else p
    if p.ndim > 1:
        loss = (p.argmax(axis=1) != y).astype(float)
    else:
        loss = (y.astype(float) == 0).astype(float)

    n = len(conf)
    order = np.argsort(-conf)            # descending confidence
    conf_s = conf[order]
    loss_s = loss[order]
    cum_loss = np.cumsum(loss_s)

    best_cost = math.inf
    best: Dict[str, float] = {
        "threshold": float(conf_s[max(0, int(n * target_coverage) - 1)]),
        "coverage": target_coverage,
        "risk": 1.0,
    }

    for k in range(1, n + 1):
        coverage = k / n
        if coverage < min_coverage:
            continue
        tau = float(conf_s[k - 1])
        risk = float(cum_loss[k - 1] / k)
        cost = c_error * risk * coverage + c_reject * (1.0 - coverage)
        if cost < best_cost:
            best_cost = cost
            best = {"threshold": tau, "coverage": coverage, "risk": risk}

    return best


def selective_predict(
    probs: np.ndarray,
    threshold: float,
) -> Tuple[np.ndarray, np.ndarray]:
    """Return predictions with abstentions applied.

    Returns:
        predictions: (N,) int array; -1 = abstained.
        abstain_mask: (N,) bool array; True = abstained.
    """
    p = np.asarray(probs, dtype=float)
    conf = p.max(axis=1) if p.ndim > 1 else p
    preds = p.argmax(axis=1) if p.ndim > 1 else (conf >= 0.5).astype(int)
    abstain = conf < threshold
    preds = preds.copy().astype(int)
    preds[abstain] = -1
    return preds, abstain


def selective_risk(
    probs: np.ndarray,
    labels: np.ndarray,
    threshold: float,
) -> Dict[str, float]:
    """Selective risk metrics at a given threshold τ.

    Returns dict with: threshold, coverage, risk, n_covered.
    """
    p = np.asarray(probs, dtype=float)
    y = np.asarray(labels, dtype=int)

    conf = p.max(axis=1) if p.ndim > 1 else p
    covered = conf >= threshold
    coverage = float(covered.mean())

    if covered.sum() == 0:
        return {"threshold": threshold, "coverage": 0.0, "risk": 0.0, "n_covered": 0}

    if p.ndim > 1:
        correct = (p.argmax(axis=1) == y).astype(float)
    else:
        pred = (conf >= 0.5).astype(int)
        correct = (pred == y).astype(float)

    risk = float(1.0 - correct[covered].mean())
    return {
        "threshold": float(threshold),
        "coverage": coverage,
        "risk": risk,
        "n_covered": int(covered.sum()),
    }
