"""Tests for Π admissibility engine — Ring 6 AC-1..AC-4."""
from pi.engine import PiEngine, PiCheckRequest

_engine = PiEngine()


def _check(candidate):
    return _engine.check(PiCheckRequest(candidate=candidate))


def test_wire_send_blocked():
    r = _check({"op": "wire.send", "amount": 100})
    assert r.admissible is False
    assert r.abstention is False
    assert "AX-10" in r.triggered_axioms
    assert any("NE-1" in ne or "wire" in ne.lower() for ne in r.triggered_never_events)


def test_dk_mutation_blocked():
    r = _check({"op": "dk.write", "content": "x"})
    assert r.admissible is False
    assert "AX-1" in r.triggered_axioms


def test_canon_overwrite_blocked():
    r = _check({"op": "canon.overwrite"})
    assert r.admissible is False


def test_shell_exec_blocked():
    r = _check({"op": "shell.exec", "cmd": "rm -rf /"})
    assert r.admissible is False
    assert r.abstention is False


def test_alexandria_rewrite_blocked():
    r = _check({"op": "alexandria.rewrite"})
    assert r.admissible is False


def test_ambiguous_canon_op_abstains():
    r = _check({"op": "canon.promote", "evidence": None})
    assert r.admissible is False
    assert r.abstention is True


def test_safe_op_admissible():
    r = _check({"op": "read.ledger", "evidence": "sha256:abc"})
    assert r.admissible is True
    assert r.abstention is False


def test_return_block_v2_shape():
    r = _check({"op": "read.healthz"})
    assert r.return_block_version == 2
    assert r.dignity_banner == "AXIOLEV HOLDINGS LLC — DIGNITY PRESERVED"
    assert r.receipt_id is not None
    assert r.timestamp is not None


def test_tcpa_blocked():
    r = _check({"op": "tcpa.call_dnc", "number": "+15551234567"})
    assert r.admissible is False
    assert "AX-12" in r.triggered_axioms


def test_fair_housing_blocked():
    r = _check({"op": "fh.deny", "subject": "protected_class"})
    assert r.admissible is False
    assert "AX-11" in r.triggered_axioms
