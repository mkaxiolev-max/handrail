"""Tests for ReturnBlock.v2 ABI freeze."""
from abi.return_block import ReturnBlock


def test_ok_block_has_v2():
    rb = ReturnBlock.ok_block("test.op")
    assert rb.return_block_version == 2
    assert rb.ok is True
    assert rb.rc == 0
    assert rb.dignity_banner == "AXIOLEV HOLDINGS LLC — DIGNITY PRESERVED"
    assert rb.receipt_id is not None
    assert rb.timestamp is not None


def test_fail_block_has_v2():
    rb = ReturnBlock.fail_block("something_failed", rc=1, operation="test.fail")
    assert rb.return_block_version == 2
    assert rb.ok is False
    assert rb.rc == 1
    assert rb.failure_reason == "something_failed"
    assert rb.dignity_banner == "AXIOLEV HOLDINGS LLC — DIGNITY PRESERVED"


def test_serialization_roundtrip():
    rb = ReturnBlock.ok_block("serial.test", artifacts=[{"key": "val"}])
    data = rb.model_dump()
    assert data["return_block_version"] == 2
    rb2 = ReturnBlock(**data)
    assert rb2.artifacts == [{"key": "val"}]


def test_deny_envelope():
    rb = ReturnBlock.fail_block("unauthorized", rc=1, operation="pdp.decide")
    d = rb.model_dump()
    assert d["ok"] is False
    assert d["failure_reason"] == "unauthorized"
    assert d["return_block_version"] == 2
