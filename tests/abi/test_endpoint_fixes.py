"""Live endpoint tests — P1.5 ABI freeze verification."""
import json
import pytest
import urllib.request
import urllib.error


BASE = "http://127.0.0.1:9000"
STATE_API = "http://127.0.0.1:9090"


def _post(path, body):
    data = json.dumps(body).encode()
    req = urllib.request.Request(
        BASE + path, data=data,
        headers={"Content-Type": "application/json"}, method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def _get(url):
    try:
        with urllib.request.urlopen(url, timeout=5) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, {}


def test_pdp_decide_returns_v2_deny():
    status, body = _post("/pdp/decide", {"principal": "anon", "action": "canon.promote"})
    assert body.get("return_block_version") == 2, f"expected v2, got: {body}"
    assert body.get("ok") is False, f"anon should be denied: {body}"
    assert body.get("failure_reason") == "unauthorized"
    assert body.get("dignity_banner") == "AXIOLEV HOLDINGS LLC — DIGNITY PRESERVED"


def test_omega_simulate_403_on_allow_promotion():
    status, body = _post("/api/v1/omega/simulate", {"allow_promotion": True})
    assert status == 403, f"expected 403 on allow_promotion=true, got {status}: {body}"


def test_state_api_9090_reachable():
    status, body = _get(STATE_API + "/healthz")
    assert status == 200, f"state_api:9090 /healthz returned {status}"
    assert body.get("status") == "ok"
