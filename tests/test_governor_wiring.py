import pytest
from services.governor.wiring.schema import AxiolevReceipt
from services.governor.wiring.invariant import ScoreMonotoneInvariant

def test_receipt_hash_deterministic():
    r1=AxiolevReceipt("e1","parent","PASS",80.0,timestamp=1000.0)
    r2=AxiolevReceipt("e1","parent","PASS",80.0,timestamp=1000.0)
    assert r1.hash()==r2.hash()

def test_receipt_ledger_schema():
    e=AxiolevReceipt("e1","p","HIGH_ASSURANCE",88.0,delta=2.0).to_ledger_entry()
    assert "axiolev.zone" in e and "axiolev.receipt_hash" in e

def test_invariant_allows():
    assert ScoreMonotoneInvariant().evaluate(80.0)[0] is True

def test_invariant_blocks_low():
    ok,reason=ScoreMonotoneInvariant().evaluate(30.0)
    assert ok is False and "minimum" in reason

def test_invariant_blocks_halt():
    ok,reason=ScoreMonotoneInvariant().evaluate(50.0,baseline=70.0)
    assert ok is False and "halt" in reason.lower()

def test_invariant_allows_small_drop():
    assert ScoreMonotoneInvariant().evaluate(85.0,baseline=88.0)[0] is True
