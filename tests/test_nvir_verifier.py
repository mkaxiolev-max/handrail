"""Q9 — NVIR verifier tests."""
from services.nvir.verifier import NVIRCandidate, NVIRVerifier, nvir_rate

def test_novel_valid_admitted():
    v = NVIRVerifier(known={"known-one"})
    c = NVIRCandidate("new-formula", 0.8)
    assert v.admit(c, oracle=lambda f: True)

def test_already_known_rejected():
    v = NVIRVerifier(known={"dup-formula"})
    assert not v.admit(NVIRCandidate("dup-formula", 0.9), oracle=lambda f: True)

def test_invalid_rejected():
    v = NVIRVerifier(known=set())
    assert not v.admit(NVIRCandidate("bad-one", 0.9), oracle=lambda f: False)

def test_nvir_rate_basic():
    v = NVIRVerifier(known={"formula-x"})
    cs = [NVIRCandidate("formula-x",0.9), NVIRCandidate("formula-y",0.9),
          NVIRCandidate("formula-z",0.0), NVIRCandidate("formula-qq",0.5)]
    r = nvir_rate(cs, v, oracle=lambda f: True)
    # admitted: formula-y, formula-qq → 2/4
    assert 0.4 < r <= 0.6
