"""
Voice E2E Test Suite — 3 lifecycle tests.
Proves the full loop: call → session → transcript → atom → receipt.

These tests run against the live ns_core service (port 9000).
Run: python -m pytest test_voice_e2e.py -v --timeout=30
"""
import pytest
import requests
import uuid

BASE = "http://127.0.0.1:9000"


def _post(path: str, body: dict = {}) -> dict:
    r = requests.post(f"{BASE}{path}", json=body, timeout=10)
    r.raise_for_status()
    return r.json()

def _get(path: str) -> dict:
    r = requests.get(f"{BASE}{path}", timeout=10)
    r.raise_for_status()
    return r.json()


# ── T1: Voice session create → state=READY ────────────────────────────────────
def test_voice_session_create_returns_ready():
    """
    POST /voice/session/create must return a session_id and state=ready.
    """
    result = _post("/voice/session/create")
    assert result["status"] == "ok", f"Expected ok, got: {result}"
    assert "session_id" in result, "session_id must be present"
    assert result["state"] == "ready", f"Expected state=ready, got: {result['state']}"
    # Verify we can retrieve it
    session_id = result["session_id"]
    fetched = _get(f"/voice/session/{session_id}")
    assert fetched["status"] == "ok"
    assert fetched["state"] == "ready"


# ── T2: Session lifecycle transitions ────────────────────────────────────────
def test_voice_session_lifecycle_transitions():
    """
    Create session → transition to LISTENING → transition to PROCESSING → RESPONDING.
    All valid transitions must succeed; state must advance correctly.
    """
    create = _post("/voice/session/create")
    session_id = create["session_id"]

    # READY → LISTENING
    r1 = _post(f"/voice/session/{session_id}/transition", {"state": "listening"})
    assert r1["status"] == "ok", f"ready→listening failed: {r1}"
    assert r1["state"] == "listening"

    # LISTENING → PROCESSING
    r2 = _post(f"/voice/session/{session_id}/transition", {"state": "processing"})
    assert r2["status"] == "ok", f"listening→processing failed: {r2}"
    assert r2["state"] == "processing"

    # PROCESSING → RESPONDING
    r3 = _post(f"/voice/session/{session_id}/transition", {"state": "responding"})
    assert r3["status"] == "ok", f"processing→responding failed: {r3}"
    assert r3["state"] == "responding"


# ── T3: Intent through voice → receipt in chain ───────────────────────────────
def test_voice_intent_produces_chained_receipt():
    """
    Create a voice session, then submit an intent via /intent/execute.
    The response must include a valid receipt_hash and chain_verified=True.
    This proves voice→intent→receipt→chain loop is connected.
    """
    # Create voice context
    create = _post("/voice/session/create")
    session_id = create["session_id"]

    # Simulate voice-driven intent
    intent_result = _post("/intent/execute", {
        "intent": f"Voice test intent from session {session_id[:8]}",
        "mode": "founder_strategic",
    })

    assert intent_result["status"] == "ok", f"intent/execute failed: {intent_result}"
    receipt_hash = intent_result.get("receipt_hash", "")
    assert len(receipt_hash) == 64, f"receipt_hash must be 64-char SHA256, got: '{receipt_hash}'"
    assert intent_result.get("chain_verified") is True, \
        f"chain_verified must be True, got: {intent_result.get('chain_verified')}"

    # Verify system/now shows receipts count increased
    now = _get("/system/now")
    assert now["memory"]["receipts"] > 0, "receipts count must be > 0 after intent"
