"""Calibration metrics: Brier score, ECE, AURC. © 2026 AXIOLEV Holdings LLC

All functions accept numpy arrays; no heavy dependencies required.
Ontology: storage via Alexandrian Archive; lineage via Lineage Fabric.
"""
from __future__ import annotations

import math
from typing import Dict, List, Optional, Tuple

import numpy as np


def brier_score(probs: np.ndarray, labels: np.ndarray) -> float:
    """Mean Brier score.

    Binary:     probs shape (N,) in [0,1]; labels shape (N,) in {0,1}.
    Multiclass: probs shape (N,C); labels shape (N,) integer class indices.
    """
    p = np.asarray(probs, dtype=float)
    y = np.asarray(labels, dtype=int)
    if p.ndim == 1:
        return float(np.mean((p - y.astype(float)) ** 2))
    n, c = p.shape
    y_oh = np.zeros_like(p)
    y_oh[np.arange(n), y] = 1.0
    return float(np.mean(np.sum((p - y_oh) ** 2, axis=1)))


def brier_decomposition(
    probs: np.ndarray,
    labels: np.ndarray,
    n_bins: int = 15,
) -> Dict[str, float]:
    """Murphy (1973) Brier score decomposition.

    Returns:
        reliability:  calibration error (lower is better)
        resolution:   discrimination skill (higher is better)
        uncertainty:  ō(1-ō) — irreducible noise in the label process
        brier:        overall Brier score ≈ reliability - resolution + uncertainty

    The identity BS ≈ REL − RES + UNC holds exactly in the limit of many bins.
    """
    p = np.asarray(probs, dtype=float)
    y = np.asarray(labels, dtype=int)

    if p.ndim > 1:
        conf = p.max(axis=1)
        y_bin = (p.argmax(axis=1) == y).astype(float)
    else:
        conf = p
        y_bin = y.astype(float)

    base_rate = float(y_bin.mean())
    unc = base_rate * (1.0 - base_rate)

    edges = np.linspace(0.0, 1.0 + 1e-9, n_bins + 1)
    rel = 0.0
    res = 0.0
    n = len(y_bin)

    for i in range(n_bins):
        mask = (conf >= edges[i]) & (conf < edges[i + 1])
        n_k = int(mask.sum())
        if n_k == 0:
            continue
        f_k = float(conf[mask].mean())
        o_k = float(y_bin[mask].mean())
        w = n_k / n
        rel += w * (f_k - o_k) ** 2
        res += w * (o_k - base_rate) ** 2

    return {
        "brier": brier_score(p, labels),
        "reliability": float(rel),
        "resolution": float(res),
        "uncertainty": float(unc),
    }


def ece(
    probs: np.ndarray,
    labels: np.ndarray,
    n_bins: int = 15,
    equal_mass: bool = False,
) -> float:
    """Expected Calibration Error.

    equal_mass=False (default): uniform confidence bins [0,1/K), [1/K, 2/K), …
    equal_mass=True:            equal-count bins (adaptive).
    """
    p = np.asarray(probs, dtype=float)
    y = np.asarray(labels, dtype=int)

    if p.ndim > 1:
        conf = p.max(axis=1)
        correct = (p.argmax(axis=1) == y).astype(float)
    else:
        conf = p
        correct = y.astype(float)

    n = len(conf)
    order = np.argsort(conf)
    conf_s = conf[order]
    correct_s = correct[order]

    ece_val = 0.0
    if equal_mass:
        bin_size = max(1, n // n_bins)
        for i in range(n_bins):
            lo, hi = i * bin_size, min((i + 1) * bin_size, n)
            if lo >= hi:
                continue
            avg_conf = conf_s[lo:hi].mean()
            avg_acc = correct_s[lo:hi].mean()
            ece_val += ((hi - lo) / n) * abs(avg_conf - avg_acc)
    else:
        edges = np.linspace(0.0, 1.0 + 1e-9, n_bins + 1)
        for i in range(n_bins):
            mask = (conf_s >= edges[i]) & (conf_s < edges[i + 1])
            n_k = int(mask.sum())
            if n_k == 0:
                continue
            avg_conf = conf_s[mask].mean()
            avg_acc = correct_s[mask].mean()
            ece_val += (n_k / n) * abs(avg_conf - avg_acc)

    return float(ece_val)


def aurc(probs: np.ndarray, labels: np.ndarray) -> float:
    """Area Under the Risk-Coverage curve.

    Sort predictions by descending confidence; compute the average selective risk
    across all coverage levels from 1/N to N/N.
    """
    p = np.asarray(probs, dtype=float)
    y = np.asarray(labels, dtype=int)

    conf = p.max(axis=1) if p.ndim > 1 else p
    if p.ndim > 1:
        loss = (p.argmax(axis=1) != y).astype(float)
    else:
        loss = (y.astype(float) == 0).astype(float)  # error = 1 - correct

    order = np.argsort(-conf)
    loss_s = loss[order]
    cum = np.cumsum(loss_s)
    risk_at_k = cum / np.arange(1, len(loss_s) + 1)
    return float(risk_at_k.mean())


def risk_coverage_curve(probs: np.ndarray, labels: np.ndarray) -> List[Dict[str, float]]:
    """Per-coverage-step selective risk metrics sorted by ascending coverage.

    Each entry: {"coverage": float, "threshold": float, "risk": float}.
    Coverage increases as threshold decreases (more samples accepted).
    """
    p = np.asarray(probs, dtype=float)
    y = np.asarray(labels, dtype=int)

    conf = p.max(axis=1) if p.ndim > 1 else p
    if p.ndim > 1:
        loss = (p.argmax(axis=1) != y).astype(float)
    else:
        loss = (y.astype(float) == 0).astype(float)

    order = np.argsort(-conf)
    conf_s = conf[order]
    loss_s = loss[order]
    n = len(loss_s)

    result: List[Dict[str, float]] = []
    cum_loss = 0.0
    for k, (c, l) in enumerate(zip(conf_s, loss_s), 1):
        cum_loss += l
        result.append(
            {"coverage": k / n, "threshold": float(c), "risk": cum_loss / k}
        )
    return result
