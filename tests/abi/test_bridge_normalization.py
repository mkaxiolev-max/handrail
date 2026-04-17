"""Tests for bridge normalization — ns_bridge always emits ReturnBlock.v2."""
from bridge.normalize import wrap_response, normalize_bridge_response


def test_passthrough_v2_unchanged():
    v2 = {
        "return_block_version": 2, "ok": True, "rc": 0, "operation": "x",
        "failure_reason": None, "artifacts": [], "checks": [], "state_change": None,
        "warnings": [], "receipt_id": "abc", "timestamp": "t",
        "dignity_banner": "AXIOLEV HOLDINGS LLC — DIGNITY PRESERVED",
    }
    result = wrap_response(v2, "test")
    assert result is v2


def test_non_v2_gets_wrapped():
    upstream = {"effect": "DENY", "reason": "test"}
    rb = wrap_response(upstream, "pdp.legacy")
    assert rb["return_block_version"] == 2
    assert rb["artifacts"] == [upstream]
    assert rb["dignity_banner"] == "AXIOLEV HOLDINGS LLC — DIGNITY PRESERVED"


def test_none_upstream_wrapped():
    rb = wrap_response(None, "empty.upstream")
    assert rb["return_block_version"] == 2
    assert rb["artifacts"] == []


def test_exception_yields_fail_block():
    rb = normalize_bridge_response(None, "failing.op", exc=ValueError("boom"))
    assert rb["return_block_version"] == 2
    assert rb["ok"] is False
    assert rb["rc"] == 1
    assert "boom" in rb["failure_reason"]


def test_no_exception_wraps_upstream():
    data = {"foo": "bar"}
    rb = normalize_bridge_response(data, "good.op")
    assert rb["return_block_version"] == 2
    assert rb["ok"] is True
    assert data in rb["artifacts"]
