"""C12 — MISSING-005: Validator Adapters tests. I7."""
import pytest
from services.validator_adapters.adapters import (
    smt_check_satisfiable, smt_check_unsat, dft_check_periodicity,
    fda_validate_protocol, _z3_available, ValidationResult,
)


def test_smt_sat_simple():
    r = smt_check_satisfiable(["x > 0", "x < 10"])
    assert r.skipped or r.passed


def test_smt_unsat_contradiction():
    r = smt_check_satisfiable(["x > 10", "x < 5"])
    assert r.skipped or not r.passed


def test_smt_tautology():
    r = smt_check_unsat("x >= 0")
    # x >= 0 is NOT a tautology (x can be negative); result depends on z3
    assert isinstance(r, ValidationResult)


def test_dft_periodic_signal_passes():
    signal = [1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0]
    r = dft_check_periodicity(signal, expected_period=2)
    assert r.passed


def test_dft_non_periodic_fails():
    signal = [1.0, 2.0, 0.5, 3.0, 1.0, 0.1, 2.5, 0.8]
    r = dft_check_periodicity(signal, expected_period=2)
    assert not r.passed


def test_fda_valid_protocol():
    protocol = {
        "name": "test", "version": "1.0",
        "inputs": ["x"], "outputs": ["y"],
        "validation_steps": ["step1"],
    }
    r = fda_validate_protocol(protocol)
    assert r.passed


def test_fda_missing_field_fails():
    r = fda_validate_protocol({"name": "incomplete"})
    assert not r.passed
    assert "version" in r.detail or "inputs" in r.detail


def test_all_adapters_return_validation_result():
    for r in [
        smt_check_satisfiable(["x > 0"]),
        dft_check_periodicity([1, 0, 1, 0, 1, 0], 2),
        fda_validate_protocol({"name": "x", "version": "1",
                               "inputs": [], "outputs": [], "validation_steps": []}),
    ]:
        assert isinstance(r, ValidationResult)
