"""Validator Adapters — SMT (z3), DFT (scipy/numpy), FDA-style validation."""
from __future__ import annotations
import shutil
from dataclasses import dataclass
from typing import Any


@dataclass
class ValidationResult:
    adapter: str
    passed: bool
    detail: str
    skipped: bool = False


# --- SMT Adapter (z3) ---
def _z3_available() -> bool:
    try:
        import z3  # noqa
        return True
    except ImportError:
        return False


def smt_check_satisfiable(constraints: list[str]) -> ValidationResult:
    if not _z3_available():
        return ValidationResult("smt", False, "z3 not available", skipped=True)
    import z3
    solver = z3.Solver()
    x = z3.Int("x")
    for c in constraints:
        try:
            solver.add(eval(c, {"x": x, "z3": z3}))  # noqa: S307
        except Exception as e:
            return ValidationResult("smt", False, f"parse error: {e}")
    result = solver.check()
    return ValidationResult("smt", result == z3.sat, str(result))


def smt_check_unsat(formula: str) -> ValidationResult:
    """Check that negation is unsatisfiable (i.e., formula is a tautology)."""
    if not _z3_available():
        return ValidationResult("smt_unsat", False, "z3 not available", skipped=True)
    import z3
    x = z3.Int("x")
    solver = z3.Solver()
    try:
        solver.add(z3.Not(eval(formula, {"x": x, "z3": z3})))  # noqa: S307
    except Exception as e:
        return ValidationResult("smt_unsat", False, f"parse error: {e}")
    result = solver.check()
    return ValidationResult("smt_unsat", result == z3.unsat, str(result))


# --- DFT Adapter (pure Python) ---
def dft_check_periodicity(signal: list[float], expected_period: int) -> ValidationResult:
    n = len(signal)
    if n < expected_period * 2:
        return ValidationResult("dft", False, "signal too short")
    # Simple periodicity check without FFT
    errors = sum(abs(signal[i] - signal[i % expected_period]) for i in range(n))
    avg_err = errors / n
    passed = avg_err < 0.1
    return ValidationResult("dft", passed, f"avg_err={avg_err:.4f}")


# --- FDA-style Adapter ---
def fda_validate_protocol(protocol: dict) -> ValidationResult:
    required = ["name", "version", "inputs", "outputs", "validation_steps"]
    missing = [k for k in required if k not in protocol]
    passed = not missing
    detail = "ok" if passed else f"missing: {missing}"
    return ValidationResult("fda", passed, detail)
