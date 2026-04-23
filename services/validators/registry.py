"""Validator adapter registry — AXIOLEV Holdings LLC © 2026.

Single source of truth for domain → adapter dispatch.
Protocol conformance is verified at module load time via isinstance()
against the @runtime_checkable ValidatorAdapter protocol.
"""
from __future__ import annotations

import uuid
from typing import Any, Dict

from .contracts import ValidationResult, ValidatorAdapter, emit_lineage_receipt
from .lean_math import LeanMathAdapter
from .dft_physics_stub import DFTPhysicsAdapter
from .fda_biomed import FDABiomedAdapter

_ADAPTERS: Dict[str, ValidatorAdapter] = {
    "math":       LeanMathAdapter(),
    "physics":    DFTPhysicsAdapter(),
    "biomedical": FDABiomedAdapter(),
}

# Aliases for backward compatibility with pre-framework REGISTRY keys
_ALIASES: Dict[str, str] = {
    "materials": "physics",
    "clinical":  "biomedical",
}

# Protocol conformance gate — fail fast at import time
for _domain, _adapter in _ADAPTERS.items():
    assert isinstance(_adapter, ValidatorAdapter), (
        f"Adapter for domain {_domain!r} does not satisfy ValidatorAdapter protocol"
    )


def dispatch(domain: str, claim: str, context: Dict[str, Any]) -> ValidationResult:
    """Route *claim* to the adapter registered for *domain*.

    Returns an UNSUPPORTED ValidationResult (still Lineage-anchored) for
    unknown domains rather than raising, so callers get a usable receipt.
    """
    resolved = _ALIASES.get(domain, domain)
    adapter = _ADAPTERS.get(resolved)
    if adapter is None:
        cid = context.get("claim_id", uuid.uuid4().hex[:12])
        checks = {"reason": f"no adapter for domain '{domain}'"}
        receipt_id, lhash = emit_lineage_receipt(
            claim_id=cid, domain=domain, adapter="registry",
            verdict="UNSUPPORTED", confidence=0.0, checks=checks,
        )
        return ValidationResult(
            claim_id=cid, domain=domain, adapter="registry",
            verdict="UNSUPPORTED", confidence=0.0,
            rationale=f"No adapter registered for domain '{domain}'",
            checks=checks,
            flags=[f"unknown_domain:{domain}"],
            audit_trail=[{"step": "dispatch_fail", "domain": domain,
                          "known": sorted(_ADAPTERS)}],
            receipt_id=receipt_id, lineage_hash=lhash,
        )
    return adapter.validate(claim, context)


def registered_domains() -> list[str]:
    return sorted(_ADAPTERS.keys())


def register(adapter: ValidatorAdapter, *, override: bool = False) -> None:
    """Register *adapter* in the dispatch table.

    Raises:
        TypeError:  If *adapter* does not satisfy the ValidatorAdapter protocol.
        ValueError: If domain already registered and *override* is False.
    """
    if not isinstance(adapter, ValidatorAdapter):
        raise TypeError(
            f"Object {adapter!r} does not satisfy the ValidatorAdapter protocol"
        )
    if adapter.domain in _ADAPTERS and not override:
        raise ValueError(
            f"Adapter for domain {adapter.domain!r} already registered. "
            "Pass override=True to replace."
        )
    _ADAPTERS[adapter.domain] = adapter
