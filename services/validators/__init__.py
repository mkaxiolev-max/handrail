"""Validator adapter framework — AXIOLEV Holdings LLC © 2026."""
from .contracts import (
    ValidationResult,
    ValidatorAdapter,
    Verdict,
    I3_ADMIN_CAP,
    emit_lineage_receipt,
    cap_confidence,
)
from .lean_math import LeanMathAdapter
from .dft_physics_stub import DFTPhysicsAdapter
from .fda_biomed import FDABiomedAdapter
from .registry import dispatch, registered_domains

# Legacy compatibility aliases
LeanAdapter      = LeanMathAdapter
DFTAdapter       = DFTPhysicsAdapter
FDAClassAdapter  = FDABiomedAdapter
REGISTRY = {"math": LeanMathAdapter(), "materials": DFTPhysicsAdapter(), "clinical": FDABiomedAdapter()}

__all__ = [
    "ValidationResult",
    "ValidatorAdapter",
    "Verdict",
    "I3_ADMIN_CAP",
    "emit_lineage_receipt",
    "cap_confidence",
    "LeanMathAdapter",
    "DFTPhysicsAdapter",
    "FDABiomedAdapter",
    "dispatch",
    "registered_domains",
    # legacy
    "LeanAdapter",
    "DFTAdapter",
    "FDAClassAdapter",
    "REGISTRY",
]
