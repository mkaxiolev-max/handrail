"""Q1 — witness-cosign triad tests."""
from services.witness_cosign import build_sth, verify_sth

def test_sth_has_three_cosigns():
    sth = build_sth(42, "deadbeef"*8, ts=1_000_000.0)
    assert len(sth.cosigns) == 3
    assert sth.is_quorate(3)

def test_sth_verifies():
    sth = build_sth(7, "cafebabe"*8, ts=1_000_001.0)
    v = verify_sth(sth)
    assert v["ok"] is True
    assert v["agree"] == 3

def test_tampered_sth_fails():
    sth = build_sth(7, "cafebabe"*8, ts=1_000_002.0)
    sth.cosigns["alpha"] = "0" * 64
    v = verify_sth(sth)
    assert v["ok"] is False
    assert v["agree"] == 2
