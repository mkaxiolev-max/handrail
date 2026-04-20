"""Q3 — reversible registry tests."""
from services.reversible import DEFAULT, ReversibleRegistry

def test_registered_ops_roundtrip():
    for name, start in [("identity", "x"),
                        ("append", (1,2,3)),
                        ("increment", 41),
                        ("toggle", True)]:
        _, back, ok = DEFAULT.roundtrip(name, start)
        assert ok, f"{name} not reversible"

def test_coverage_bounded():
    r = ReversibleRegistry()
    r.register("a", lambda s: s, lambda s: s)
    assert r.coverage(10) == 0.1
    assert r.coverage(0)  == 0.0
