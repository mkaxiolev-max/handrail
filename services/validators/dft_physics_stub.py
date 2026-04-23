"""DFT (Density Functional Theory) physics stub adapter — AXIOLEV Holdings LLC © 2026.

Validates materials-physics claims against DFT plausibility bounds and
caller-reported convergence flags. No live DFT engine is invoked;
claims requiring ab-initio calculation return UNCERTAIN.

Context keys recognised:
  quantity   — str: "band_gap_ev", "formation_energy_eV", "lattice_constant_A",
                    "bulk_modulus_GPa", "cohesive_energy_eV", "magnetic_moment_muB"
  value      — float: the reported quantity value
  functional — str: DFT functional label, e.g. "PBE", "HSE06" (informational)
  converged  — bool | None: caller-attested SCF convergence

I3 constraint: confidence ceiling I3_ADMIN_CAP (0.95).
"""
from __future__ import annotations
import uuid
from typing import Any, Dict

from .contracts import ValidationResult, Verdict, emit_lineage_receipt, cap_confidence

# Physically plausible ranges for common DFT output quantities
_BOUNDS: Dict[str, tuple[float, float]] = {
    "band_gap_ev":         (0.0,   30.0),   # eV — metal (0) to wide-gap insulator
    "formation_energy_eV": (-20.0, 10.0),   # eV/atom
    "lattice_constant_A":  (1.5,   20.0),   # Angstroms
    "bulk_modulus_GPa":    (0.1,   700.0),  # GPa
    "cohesive_energy_eV":  (0.0,   12.0),   # eV/atom
    "magnetic_moment_muB": (0.0,   10.0),   # μ_B / atom
}


def _check_quantity(key: str, value: float) -> Dict[str, Any]:
    if key not in _BOUNDS:
        return {"known": False, "in_range": None, "bounds": None, "value": value}
    lo, hi = _BOUNDS[key]
    return {
        "known": True,
        "in_range": lo <= value <= hi,
        "bounds": [lo, hi],
        "value": value,
    }


class DFTPhysicsAdapter:
    domain = "physics"

    def validate(self, claim: str, context: Dict[str, Any]) -> ValidationResult:
        claim_id = context.get("claim_id", uuid.uuid4().hex[:12])
        checks: Dict[str, Any] = {"stub": True, "engine": "none"}

        quantity_key = context.get("quantity")
        quantity_val = context.get("value")
        functional   = context.get("functional", "unspecified")
        convergence  = context.get("converged", None)

        checks["functional"]           = functional
        checks["convergence_reported"] = convergence

        quantity_check: Dict[str, Any] = {}
        if quantity_key is not None and quantity_val is not None:
            quantity_check = _check_quantity(quantity_key, float(quantity_val))
        checks["quantity_bounds"] = quantity_check

        if quantity_check.get("known") and quantity_check.get("in_range") is False:
            verdict: Verdict = "FAIL"
            confidence = cap_confidence(0.80)
            rationale = (
                f"{quantity_key}={quantity_val} outside plausible DFT range "
                f"{quantity_check['bounds']} — likely input error or unit mismatch"
            )
        elif convergence is False:
            verdict = "FAIL"
            confidence = cap_confidence(0.72)
            rationale = "Caller-reported SCF convergence failure — result unreliable"
        elif quantity_check.get("in_range") and convergence:
            verdict = "PASS"
            confidence = cap_confidence(0.70)   # stub ceiling — no live calculation
            rationale = (
                f"{quantity_key}={quantity_val} within DFT bounds, convergence confirmed "
                f"(stub — no live {functional} calculation performed)"
            )
        else:
            verdict = "UNCERTAIN"
            confidence = cap_confidence(0.35)
            rationale = "Insufficient context for DFT validation — stub adapter, no live engine"

        receipt_id, lineage_hash = emit_lineage_receipt(
            claim_id=claim_id, domain=self.domain, adapter="dft_physics_stub",
            verdict=verdict, confidence=confidence, checks=checks,
        )
        return ValidationResult(
            claim_id=claim_id, domain=self.domain, adapter="dft_physics_stub",
            verdict=verdict, confidence=confidence, rationale=rationale,
            checks=checks, receipt_id=receipt_id, lineage_hash=lineage_hash,
        )
