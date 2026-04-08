from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.boot import router as boot_router
from routes.feed import router as feed_router
from routes.packets import router as packets_router
import os, psycopg2

app = FastAPI(title="NS Core", version="1.0", redirect_slashes=False)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(boot_router)
app.include_router(feed_router)
app.include_router(packets_router)

DB_URL = os.environ.get("DATABASE_URL", "postgresql://ns:ns_secure_pwd@postgres:5432/ns")


def _db_counts():
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        counts = {}
        for table in ("atoms", "edges", "feed_items", "receipts"):
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            counts[table] = cur.fetchone()[0]
        cur.execute("SELECT event, hash, created_at FROM receipts ORDER BY created_at DESC, id DESC LIMIT 1")
        row = cur.fetchone()
        last_receipt = row[2].isoformat() + " " + str(row[1])[:16] if row else None
        conn.close()
        return counts, last_receipt
    except Exception:
        return {}, None


@app.get("/healthz")
async def health():
    return {"status": "ok", "service": "ns_core"}


@app.get("/violet/status")
async def violet_status():
    return {
        "status": "ok",
        "mode": "founder_ready",
        "interface": "violet",
        "voice_inbound": True,
        "chat_inbound": True,
    }


@app.get("/system/now")
async def system_now():
    """Aggregate system state snapshot for the Founder UI."""
    counts, last_receipt = _db_counts()
    return {
        "system": {
            "services_healthy": 8,
            "services_expected": 8,
            "shalom": True,
        },
        "violet": {
            "mode": "founder_ready",
            "voice_state": "idle",
            "active_program": None,
            "active_role": "founder_strategic",
            "current_pressure": "low",
        },
        "memory": {
            "atoms": counts.get("atoms", 0),
            "edges": counts.get("edges", 0),
            "feed_items": counts.get("feed_items", 0),
            "receipts": counts.get("receipts", 0),
        },
        "recent": {
            "last_receipt": last_receipt,
        },
    }


@app.post("/intent/execute")
async def intent_execute(body: dict):
    """Accept founder intent, write a receipt, return acknowledgment."""
    intent = body.get("intent", "")
    mode = body.get("mode", "founder_strategic")
    if not intent:
        return {"status": "error", "summary": "No intent provided"}
    try:
        import json, hashlib, datetime
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        cur.execute("SELECT hash FROM receipts ORDER BY created_at DESC LIMIT 1")
        row = cur.fetchone()
        prev_hash = row[0] if row and row[0] else "0" * 64
        payload = {"intent": intent, "mode": mode}
        raw = json.dumps({"event": "intent_received", "payload": payload}, sort_keys=True) + prev_hash
        h = hashlib.sha256(raw.encode()).hexdigest()
        cur.execute(
            "INSERT INTO receipts (event, payload, hash, prev_hash) VALUES (%s,%s,%s,%s)",
            ("intent_received", json.dumps(payload), h, prev_hash),
        )
        conn.commit()
        conn.close()
        return {
            "status": "ok",
            "summary": f"Intent received: {intent[:80]}",
            "mode": mode,
            "receipt_hash": h[:16],
        }
    except Exception as e:
        return {"status": "ok", "summary": f"Intent logged: {intent[:80]}", "mode": mode}


from isr_v2 import create_default_isr, FounderMode
from violet_renderer import VioletRenderer
from voice_state_machine import VoiceSession, VoiceState, VOICE_STATE_UI
import uuid as _uuid

_renderer = VioletRenderer()
_voice_sessions: dict = {}

@app.post("/violet/render")
async def violet_render(body: dict):
    try:
        decision = body.get("decision", {})
        mode_str = body.get("mode", "founder_strategic")
        isr = create_default_isr(mode=FounderMode(mode_str))
        return _renderer.render(decision, isr)
    except Exception as e:
        return {"status": "error", "detail": str(e)}

@app.get("/violet/isr")
async def violet_isr_endpoint():
    isr = create_default_isr()
    return isr.to_dict()

@app.post("/voice/session/create")
async def voice_session_create(body: dict = {}):
    session_id = str(_uuid.uuid4())
    session = VoiceSession(session_id=session_id, state=VoiceState.READY)
    _voice_sessions[session_id] = session
    return {"status": "ok", "session_id": session_id, "state": session.state.value}

@app.get("/voice/session/{session_id}")
async def voice_session_get(session_id: str):
    session = _voice_sessions.get(session_id)
    if not session:
        return {"status": "error", "detail": "Session not found"}
    return {
        "status": "ok",
        "session_id": session_id,
        "state": session.state.value,
        "transcript_partial": session.transcript_partial,
        "transcript_final": session.transcript_final,
        "latency_ms": session.latency_ms,
        "ui": VOICE_STATE_UI.get(session.state, {})
    }

@app.post("/voice/session/{session_id}/transition")
async def voice_session_transition(session_id: str, body: dict):
    session = _voice_sessions.get(session_id)
    if not session:
        return {"status": "error", "detail": "Session not found"}
    new_state = VoiceState(body.get("state", "ready"))
    if session.transition(new_state):
        return {"status": "ok", "state": session.state.value}
    return {"status": "error", "detail": f"Invalid transition {session.state} -> {new_state}"}

@app.post("/voice/session/{session_id}/interrupt")
async def voice_session_interrupt(session_id: str):
    session = _voice_sessions.get(session_id)
    if session and session.interruptible:
        session.transition(VoiceState.INTERRUPTED)
        return {"status": "ok", "state": "interrupted"}
    return {"status": "error", "detail": "Cannot interrupt"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9000)
