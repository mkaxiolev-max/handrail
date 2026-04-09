"""
test_invariants.py — five guarantee tests attacking the exact audit seams.
If any fail, the system is not enforced.
"""
import pytest
import asyncio
import hashlib
import json

@pytest.mark.asyncio
async def test_intent_execute_returns_receipt_hash(client):
    resp = await client.post("/intent/execute", json={
        "text": "what is the current system state", "mode": "command", "actor": "founder_test"})
    assert resp.status_code == 200
    data = resp.json()
    assert "receipt_hash" in data, "ENFORCEMENT BROKEN: no receipt_hash returned"
    assert len(data["receipt_hash"]) >= 32, "receipt_hash too short"

@pytest.mark.asyncio
async def test_receipt_prev_hash_advances_monotonically(client, chain):
    for i in range(3):
        await client.post("/intent/execute", json={
            "text": f"test intent {i}", "mode": "command", "actor": "invariant_test"})
    receipts = chain.get_last_n(3)
    for i in range(1, len(receipts)):
        assert receipts[i].prev_hash == receipts[i-1].hash, (
            f"CHAIN BROKEN at {i}: prev_hash={receipts[i].prev_hash} != hash={receipts[i-1].hash}")

@pytest.mark.asyncio
async def test_policy_update_without_signature_fails(canon_service):
    from canon_service import CanonSignatureError
    with pytest.raises(CanonSignatureError):
        await canon_service.commit_policy(new_policy={"allow_all":True}, signature="", actor="attacker")
    with pytest.raises(CanonSignatureError):
        await canon_service.commit_policy(new_policy={"allow_all":True}, signature="bad", actor="attacker")

@pytest.mark.asyncio
async def test_voice_session_cannot_complete_without_memory_atom(voice_repo, alexandria_repo):
    from voice_archival import close_voice_session, VoiceSessionArchiveError
    session_id = voice_repo.create_session(transcript=None)
    with pytest.raises(VoiceSessionArchiveError):
        await close_voice_session(session_id, voice_repo, alexandria_repo)
    session = voice_repo.get_voice_session(session_id)
    assert session.state == "error_no_transcript"
    assert session.memory_atom_id is None

@pytest.mark.asyncio
async def test_atoms_api_count_matches_db_count_for_large_limit(client, db):
    db_count = db.execute("SELECT COUNT(*) FROM atoms").fetchone()[0]
    resp = await client.get("/memory/atoms", params={"limit": 10000})
    assert resp.status_code == 200
    data = resp.json()
    api_count = data.get("total") or len(data.get("atoms", []))
    assert api_count == db_count, (
        f"PAGINATION DRIFT: API={api_count}, DB={db_count}. System is lying about its memory.")
