"""Behavioral tests for Clearing classes CI-1..CI-5.

Each class must have a before/after pair where the same candidate gets
different /pi/check results with the class wired vs bypassed.
"""
from clearing.non_totalization import NonTotalization
from clearing.disclosure_window import DisclosureWindow
from clearing.irreducibility import Irreducibility
from clearing.multi_disclosure import MultiDisclosure
from clearing.silence_abstention import SilenceAbstention
from pi.engine import PiEngine, PiCheckRequest

_engine = PiEngine()


def _check(candidate):
    return _engine.check(PiCheckRequest(candidate=candidate))


# CI-1 NonTotalization

def test_non_totalization_abstains_high_entropy():
    nt = NonTotalization(theta=0.1)
    assert nt.evaluates({"op": "read"}, residual_entropy=0.5) is True


def test_non_totalization_passes_low_entropy():
    nt = NonTotalization(theta=0.1)
    assert nt.evaluates({"op": "read"}, residual_entropy=0.05) is False


def test_pi_abstains_with_high_entropy():
    r = _check({"op": "canon.decide", "evidence": "sha:abc", "residual_entropy": 0.9})
    assert r.abstention is True, f"expected abstention, got: {r}"


def test_pi_admissible_with_low_entropy():
    r = _check({"op": "read.healthz", "evidence": "sha:abc", "residual_entropy": 0.0})
    assert r.admissible is True


# CI-2 DisclosureWindow

def test_disclosure_window_open():
    dw = DisclosureWindow()
    assert dw.is_disclosable() is True


def test_disclosure_window_closed_in_past():
    from datetime import datetime, timezone, timedelta
    past = datetime.now(timezone.utc) - timedelta(hours=1)
    dw = DisclosureWindow(close_at=past)
    assert dw.is_disclosable() is False


def test_disclosure_window_not_yet_open():
    from datetime import datetime, timezone, timedelta
    future = datetime.now(timezone.utc) + timedelta(hours=1)
    dw = DisclosureWindow(open_at=future)
    assert dw.evaluate({}) is True  # must abstain


# CI-3 Irreducibility

def test_irreducibility_passes_enough_receipts():
    irr = Irreducibility(min_receipts=3)
    assert irr.evaluate({"receipts": ["r1", "r2", "r3"]}) is False


def test_irreducibility_abstains_too_few_receipts():
    irr = Irreducibility(min_receipts=3)
    assert irr.evaluate({"receipts": ["r1"]}) is True


def test_irreducibility_abstains_on_compress():
    irr = Irreducibility()
    assert irr.evaluate({"compress": True}) is True


# CI-4 MultiDisclosure

def test_multi_disclosure_surfaces_both_framings():
    md = MultiDisclosure()
    framings = [
        {"id": "f1", "receipt_consistent": True},
        {"id": "f2", "receipt_consistent": True},
    ]
    result = md.evaluate({}, framings)
    assert result["multi_framing"] is True
    assert len(result["framings"]) == 2
    assert result["abstain"] is False


def test_multi_disclosure_single_framing():
    md = MultiDisclosure()
    framings = [{"id": "f1", "receipt_consistent": True}]
    result = md.evaluate({}, framings)
    assert result["multi_framing"] is False


# CI-5 SilenceAbstention

def test_silence_abstention_explicit():
    sa = SilenceAbstention()
    result = sa.evaluate({"silence": True, "op": "anything"})
    assert result is not None
    assert result["abstain"] is True


def test_silence_abstention_no_op():
    sa = SilenceAbstention()
    result = sa.evaluate({"op": ""})
    assert result is not None
    assert result["abstain"] is True


def test_silence_abstention_not_triggered():
    sa = SilenceAbstention()
    result = sa.evaluate({"op": "read.healthz", "evidence": "present"})
    assert result is None


def test_pi_abstention_field_live_via_silence():
    r = _check({"silence": True, "op": "read.healthz"})
    assert r.abstention is True
    assert r.admissible is False
