"""Q5 — Hamiltonian-gate runtime assertion tests."""
from services.hamiltonian_gate import GATE

def _ok_ctx():
    return {"route":"dignity","receipt_hash":"h","ne_checked":True,
            "actor":"founder","delete":False}

def test_ok_context_passes():
    r = GATE.evaluate(_ok_ctx())
    assert r.ok
    assert r.violations == []

def test_missing_receipt_violates():
    c = _ok_ctx(); c["receipt_hash"] = ""
    r = GATE.evaluate(c)
    assert not r.ok
    assert "receipt_emitted" in r.violations

def test_bypass_detected():
    c = _ok_ctx(); c["route"] = "shortcut"
    r = GATE.evaluate(c)
    assert not r.ok
    assert "no_bypass" in r.violations

def test_coverage_meaningful():
    assert GATE.coverage(5) == 1.0
    assert GATE.coverage(10) == 0.5
