"""INS-02 NVIR Logic Oracle tests. © 2026 AXIOLEV Holdings LLC"""
from __future__ import annotations

import pytest

from services.nvir.oracle.logic_smt import LogicSMTOracle, _structural_logic


oracle = LogicSMTOracle()

# ── structural heuristic ──────────────────────────────────────────────────────

def test_logic_01_structural_tautology_pattern():
    v = _structural_logic("A or not A")
    assert v.valid is True
    assert "tautology" in v.method


def test_logic_02_structural_contradiction_pattern():
    v = _structural_logic("A and not A")
    assert v.valid is False
    assert "contradiction" in v.method


def test_logic_03_structural_general_logic():
    v = _structural_logic("A implies B and C or D")
    assert v.valid is True
    assert v.confidence >= 0.50


def test_logic_04_structural_empty_string():
    v = _structural_logic("")
    assert v.valid is False


def test_logic_05_structural_no_logic_tokens():
    v = _structural_logic("banana")
    assert v.valid is False


# ── Z3 layer (skipped gracefully if z3 not installed) ─────────────────────────

def _z3_available() -> bool:
    try:
        import z3  # noqa: F401
        return True
    except ImportError:
        return False


@pytest.mark.skipif(not _z3_available(), reason="z3 not installed")
def test_logic_06_z3_tautology_true_or_not_a():
    v = oracle.validate("Or(A, Not(A))")
    assert v.valid is True
    assert v.confidence == 1.0
    assert "tautology" in v.method


@pytest.mark.skipif(not _z3_available(), reason="z3 not installed")
def test_logic_07_z3_contradiction_a_and_not_a():
    v = oracle.validate("And(A, Not(A))")
    assert v.valid is False
    assert v.confidence == 1.0
    assert "unsat" in v.method


@pytest.mark.skipif(not _z3_available(), reason="z3 not installed")
def test_logic_08_z3_satisfiable_formula():
    v = oracle.validate("Or(A, B)")
    assert v.valid is True


@pytest.mark.skipif(not _z3_available(), reason="z3 not installed")
def test_logic_09_z3_implication_reflexive():
    v = oracle.validate("Implies(A, A)")
    assert v.valid is True
    assert v.confidence == 1.0  # tautology


@pytest.mark.skipif(not _z3_available(), reason="z3 not installed")
def test_logic_10_z3_integer_constraint():
    # x > 0 is satisfiable
    v = oracle.validate("x > 0")
    assert v.valid is True


# ── oracle interface ──────────────────────────────────────────────────────────

def test_logic_11_validate_returns_oracle_verdict():
    from services.nvir.oracle import OracleVerdict
    v = oracle.validate("A or not A")
    assert isinstance(v, OracleVerdict)
    assert 0.0 <= v.confidence <= 1.0
    assert isinstance(v.method, str)
    assert isinstance(v.detail, dict)


def test_logic_12_callable_interface():
    # String with logic token should return bool
    result = oracle("True")
    assert isinstance(result, bool)


def test_logic_13_smt2_format_fallback():
    """SMT-LIB2 format is tried when Python Z3 eval fails."""
    smt2 = "(assert (or true false))\n(check-sat)"
    v = oracle.validate(smt2)
    # Should not raise; may or may not parse depending on z3 availability
    assert isinstance(v.valid, bool)
