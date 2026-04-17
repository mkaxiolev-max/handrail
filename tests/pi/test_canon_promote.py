"""Tests for /canon/promote endpoint."""
import json
import urllib.request
import urllib.error

BASE = "http://127.0.0.1:9000"


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


def test_promote_without_signature_rejected():
    status, body = _post("/canon/promote", {"candidate_id": "test-1"})
    assert body.get("return_block_version") == 2
    assert body.get("ok") is False
    assert body.get("failure_reason") == "unauthorized"


def test_promote_with_signature_queued():
    status, body = _post("/canon/promote", {
        "candidate_id": "test-2",
        "approver_signature": "founder-test-sig",
        "hardware_signed": False,
    })
    assert body.get("return_block_version") == 2
    assert body.get("ok") is True
    arts = body.get("artifacts", [])
    assert arts and arts[0].get("status") == "queued"


def test_promote_hardware_signed_accepted():
    status, body = _post("/canon/promote", {
        "candidate_id": "test-3",
        "approver_signature": "founder-sig",
        "hardware_signed": True,
    })
    assert body.get("ok") is True
    arts = body.get("artifacts", [])
    assert arts and arts[0].get("status") == "accepted"
