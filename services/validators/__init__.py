"""Validator adapter framework — AXIOLEV Holdings LLC © 2026."""
from .contracts import (
    ValidationResult,
    ValidatorAdapter,
    Verdict,
    I3_ADMIN_CAP,
    emit_lineage_receipt,
    cap_confidence,
    make_claim_id,
)
from .lean_math import LeanMathAdapter
from .dft_physics_stub import DFTPhysicsAdapter
from .fda_biomed import FDABiomedAdapter
from .registry import dispatch, register, registered_domains

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
    "register",
    "registered_domains",
    "make_claim_id",
    # legacy
    "LeanAdapter",
    "DFTAdapter",
    "FDAClassAdapter",
    "REGISTRY",
]
