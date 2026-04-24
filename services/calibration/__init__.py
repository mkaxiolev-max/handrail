"""AXIOLEV calibration telemetry service. © 2026 AXIOLEV Holdings LLC"""
from .pipeline import (
    CalibrationDecision, RunningBrier, BinnedECE, ACE,
    ReliabilityDiagram, AURC, ChowThreshold, BrierSkillScore,
    emit_decision, compute_metrics, export_prometheus, classify_band,
    run_calibration_pipeline,
)
from .metrics import (
    brier_score, brier_decomposition, ece, aurc as aurc_metric, risk_coverage_curve,
)
from .sft import sft_temperature_loop
from .selective import chow_optimal_threshold, selective_predict, selective_risk

__version__ = "2.2.0"
__all__ = [
    # pipeline (runtime telemetry)
    "CalibrationDecision", "RunningBrier", "BinnedECE", "ACE",
    "ReliabilityDiagram", "AURC", "ChowThreshold", "BrierSkillScore",
    "emit_decision", "compute_metrics", "export_prometheus", "classify_band",
    "run_calibration_pipeline",
    # metrics (batch functions)
    "brier_score", "brier_decomposition", "ece", "aurc_metric", "risk_coverage_curve",
    # sft
    "sft_temperature_loop",
    # selective
    "chow_optimal_threshold", "selective_predict", "selective_risk",
]
