"""Tests for /ns/resume endpoint."""
import json
import urllib.request

BASE = "http://127.0.0.1:9000"


def _post(path, body):
    data = json.dumps(body).encode()
    req = urllib.request.Request(
        BASE + path, data=data,
        headers={"Content-Type": "application/json"}, method="POST",
    )
    with urllib.request.urlopen(req, timeout=5) as r:
        return r.status, json.loads(r.read())


def test_ns_resume_returns_v2():
    status, body = _post("/ns/resume", {"context": "ring6_test"})
    assert status == 200
    assert body.get("return_block_version") == 2
    assert body.get("ok") is True
    assert body.get("dignity_banner") == "AXIOLEV HOLDINGS LLC — DIGNITY PRESERVED"


def test_ns_resume_pi_check_live():
    """Quick smoke test: /pi/check also reachable after ring6 routes registered."""
    data = json.dumps({"candidate": {"op": "wire.send"}}).encode()
    req = urllib.request.Request(
        BASE + "/pi/check", data=data,
        headers={"Content-Type": "application/json"}, method="POST",
    )
    with urllib.request.urlopen(req, timeout=5) as r:
        body = json.loads(r.read())
    assert body.get("admissible") is False
    assert "AX-10" in body.get("triggered_axioms", [])
