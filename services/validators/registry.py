"""Validator adapter registry — AXIOLEV Holdings LLC © 2026.

Single source of truth for domain → adapter dispatch.
"""
from __future__ import annotations
import uuid
from typing import Any, Dict

from .contracts import ValidationResult, emit_lineage_receipt
from .lean_math import LeanMathAdapter
from .dft_physics_stub import DFTPhysicsAdapter
from .fda_biomed import FDABiomedAdapter

_ADAPTERS: Dict[str, Any] = {
    "math":       LeanMathAdapter(),
    "physics":    DFTPhysicsAdapter(),
    "biomedical": FDABiomedAdapter(),
}

# Aliases for backward compatibility with pre-framework REGISTRY keys
_ALIASES: Dict[str, str] = {
    "materials": "physics",
    "clinical":  "biomedical",
}


def dispatch(domain: str, claim: str, context: Dict[str, Any]) -> ValidationResult:
    resolved = _ALIASES.get(domain, domain)
    adapter = _ADAPTERS.get(resolved)
    if adapter is None:
        cid = context.get("claim_id", uuid.uuid4().hex[:12])
        no_adapter_checks = {"reason": f"no adapter for domain '{domain}'"}
        receipt_id, lhash = emit_lineage_receipt(
            claim_id=cid, domain=domain, adapter="registry",
            verdict="UNSUPPORTED", confidence=0.0, checks=no_adapter_checks,
        )
        return ValidationResult(
            claim_id=cid, domain=domain, adapter="registry",
            verdict="UNSUPPORTED", confidence=0.0,
            rationale=f"No adapter registered for domain '{domain}'",
            checks=no_adapter_checks,
            receipt_id=receipt_id, lineage_hash=lhash,
        )
    return adapter.validate(claim, context)


def registered_domains() -> list[str]:
    return sorted(_ADAPTERS.keys())
