"""Q20 — final composite sanity check."""
import json, pathlib

def test_master_improved():
    p = pathlib.Path("certification/NS_MASTER_v2_1_CEILING.json")
    assert p.exists(), "composite artifact missing"
    d = json.loads(p.read_text())
    assert d["master"] >= 90.0, f"master {d['master']} below ceiling floor"
    assert d["tier"] in ("Omega-Approaching","Certified Advanced","Ultra-Omega")

def test_weights_sum_to_one():
    import pathlib, json
    d = json.loads(pathlib.Path("certification/NS_MASTER_v2_1_CEILING.json").read_text())
    s = sum(d["weights"].values())
    assert abs(s - 1.0) < 1e-9
