"""Omega-score formula + 100-pt rubric."""
from __future__ import annotations
from typing import Dict

WEIGHTS = {
    "control_ratio_score":        0.25,
    "influence_conversion_score": 0.20,
    "concern_leakage_score":      0.20,
    "feedback_integrity_score":   0.15,
    "deletion_efficiency_score":  0.10,
    "drift_resistance_score":     0.10,
}

RUBRIC = {
    "classification_accuracy":       (14, 0.97, ">="),
    "control_ratio":                 (14, 0.85, ">="),
    "concern_leakage_suppression":   (14, 0.05, "<="),
    "false_control_suppression":     (12, 0.02, "<="),
    "feedback_integrity":            (12, 0.95, ">="),
    "influence_conversion":          (10, 0.60, ">="),
    "alexandria_receipt_integrity":  ( 8, 1.00, ">="),
    "handrail_binding":              ( 6, 1.00, ">="),
    "ether_admissibility":           ( 5, 0.95, ">="),
    "gnoseogenic_drift_resistance":  ( 5, 0.05, "<="),
}

def omega_score(sub: Dict[str, float]) -> float:
    return round(sum(WEIGHTS[k]*sub.get(k,0.0) for k in WEIGHTS), 4)

def rubric_score(measurements: Dict[str, float]) -> Dict[str, float]:
    earned = {}; total = 0
    for k,(pts,target,op) in RUBRIC.items():
        v = measurements.get(k, 0.0)
        passed = v >= target if op==">=" else v <= target
        earned[k] = pts if passed else round(pts * (v/target if op==">=" else target/max(v,1e-9)), 2)
        total += earned[k]
    earned["__total__"] = round(min(total, 100.0), 2)
    return earned
