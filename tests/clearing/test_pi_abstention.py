"""Tests for /pi/check abstention=true via Clearing Layer."""
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
        return json.loads(r.read())


def test_pi_check_abstention_on_ambiguous():
    body = _post("/pi/check", {"candidate": {"op": "ambiguous_decision", "evidence": None}})
    assert body.get("abstention") is True, f"expected abstention=true: {body}"


def test_pi_check_abstention_on_high_entropy():
    body = _post("/pi/check", {"candidate": {
        "op": "canon.decide",
        "evidence": "present",
        "residual_entropy": 0.9,
    }})
    assert body.get("abstention") is True


def test_pi_check_admissible_safe_op():
    body = _post("/pi/check", {"candidate": {"op": "read.healthz"}})
    assert body.get("admissible") is True
    assert body.get("abstention") is False
