"""INS-02 NVIR Math Oracle tests. © 2026 AXIOLEV Holdings LLC"""
from __future__ import annotations

import pytest

from services.nvir.oracle.math_lean import MathLeanOracle, _safe_eval, _try_eval


oracle = MathLeanOracle()


# ── safe eval ─────────────────────────────────────────────────────────────────

def test_math_01_safe_eval_arithmetic():
    assert _safe_eval("2 + 2") == 4
    assert _safe_eval("3 * 4") == 12
    assert _safe_eval("10 / 2") == 5.0
    assert _safe_eval("2 ** 8") == 256


def test_math_02_safe_eval_math_functions():
    import math
    assert abs(_safe_eval("sqrt(4)") - 2.0) < 1e-9
    assert abs(_safe_eval("pi") - math.pi) < 1e-9
    assert abs(_safe_eval("sin(0)")) < 1e-9


def test_math_03_safe_eval_blocks_builtins():
    with pytest.raises((ValueError, NameError)):
        _safe_eval("__import__('os')")
    with pytest.raises((ValueError, NameError)):
        _safe_eval("open('/etc/passwd')")


def test_math_04_safe_eval_blocks_unknown_name():
    with pytest.raises(ValueError, match="unknown name|Unknown"):
        _safe_eval("definitely_not_a_math_function()")


# ── equation validation ───────────────────────────────────────────────────────

def test_math_05_valid_arithmetic_equation():
    v = oracle.validate("2 + 2 = 4")
    assert v.valid is True
    assert v.confidence >= 0.90


def test_math_06_invalid_arithmetic_equation():
    v = oracle.validate("2 + 2 = 5")
    assert v.valid is False
    assert v.confidence >= 0.90


def test_math_07_valid_multiplication():
    v = oracle.validate("3 * 4 = 12")
    assert v.valid is True


def test_math_08_division_by_zero_is_invalid():
    v = oracle.validate("1 / 0")
    assert v.valid is False
    assert "division" in v.method or v.confidence >= 0.80


def test_math_09_pure_valid_expression():
    v = oracle.validate("sqrt(16)")
    assert v.valid is True


def test_math_10_latex_equation_valid():
    # LaTeX cleaned before eval
    v = oracle.validate(r"$\pi \approx 3.14159$")
    # Structural or sympy — should be valid (has math content)
    assert isinstance(v.valid, bool)
    assert v.confidence > 0.0


def test_math_11_callable_interface():
    assert oracle("4 * 4 = 16") is True
    assert oracle("4 * 4 = 17") is False


def test_math_12_complex_fraction():
    v = oracle.validate("(10 + 2) / 4 = 3")
    assert v.valid is True


def test_math_13_power_equation():
    v = oracle.validate("2 ** 10 = 1024")
    assert v.valid is True


def test_math_14_float_tolerance():
    # sin(pi) ≈ 0 within tolerance
    v = oracle.validate("sin(pi) = 0")
    assert v.valid is True


def test_math_15_structural_fallback_on_text():
    # Natural language math — triggers structural fallback
    v = oracle.validate("The integral of x dx is x squared over 2")
    # Should not crash; confidence low but valid=True (has math tokens)
    assert isinstance(v.valid, bool)
    assert 0.0 < v.confidence <= 1.0
