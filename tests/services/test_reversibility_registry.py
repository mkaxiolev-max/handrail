"""C03 — MISSING-002: Reversibility Registry tests. I4."""
import pytest
from services.reversibility_registry.registry import ReversibilityRegistry


def test_registry_registers_ops():
    r = ReversibilityRegistry()
    r.register("op1", lambda: None)
    assert r.can_rollback("op1")


def test_registry_rollback_calls_fn():
    called = []
    r = ReversibilityRegistry()
    r.register("op1", lambda: called.append(1))
    r.rollback("op1")
    assert called == [1]


def test_registry_rollback_removes_op():
    r = ReversibilityRegistry()
    r.register("op1", lambda: None)
    r.rollback("op1")
    assert not r.can_rollback("op1")


def test_registry_unknown_rollback_raises():
    r = ReversibilityRegistry()
    with pytest.raises(KeyError):
        r.rollback("ghost")


def test_registry_coverage_is_100():
    r = ReversibilityRegistry()
    r.register("a", lambda: None)
    r.register("b", lambda: None)
    assert r.coverage_pct() == 100.0


def test_registry_tracks_multiple_ops():
    r = ReversibilityRegistry()
    for i in range(10):
        r.register(f"op{i}", lambda: None)
    assert r.size() == 10


def test_registry_list_ops():
    r = ReversibilityRegistry()
    r.register("x", lambda: None)
    r.register("y", lambda: None)
    assert set(r.registered_ops()) == {"x", "y"}
