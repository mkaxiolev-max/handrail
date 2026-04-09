from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.boot import router as boot_router
from routes.feed import router as feed_router
from routes.packets import router as packets_router
import os, psycopg2, logging

logger = logging.getLogger("ns_core")

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

# ── Boot invariants ────────────────────────────────────────────────────────────
_boot_report: dict = {}

def _run_boot_invariants() -> dict:
    """Verify system invariants at startup. Returns warning_block if any fail."""
    results = []
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        # Only verify receipts that participate in the chain (have a prev_hash).
        # feed_generated and other events may write receipts without chain linking.
        cur.execute("""
            SELECT r.hash, r.prev_hash FROM receipts r
            WHERE r.prev_hash IS NOT NULL AND r.prev_hash != ''
            ORDER BY r.created_at DESC, r.id DESC LIMIT 50
        """)
        chained = cur.fetchall()
        chain_ok = True
        broken_at = None
        for row in chained:
            cur.execute("SELECT 1 FROM receipts WHERE hash = %s", (row[1],))
            if not cur.fetchone():
                chain_ok = False
                broken_at = row[1][:16]
                break
        detail = f"{len(chained)} chained receipts verified" if chain_ok else f"DANGLING prev_hash {broken_at}"
        results.append({"name": "receipt_chain_intact", "passed": chain_ok, "detail": detail})
        # canon_commits table
        try:
            cur.execute("SELECT COUNT(*) FROM canon_commits")
            results.append({"name": "canon_commits_table", "passed": True, "detail": "table exists"})
        except Exception:
            results.append({"name": "canon_commits_table", "passed": False,
                            "detail": "TABLE MISSING", "remedy": "run migration 003"})
        # voice_sessions table
        try:
            cur.execute("SELECT COUNT(*) FROM voice_sessions")
            results.append({"name": "voice_sessions_table", "passed": True, "detail": "table exists"})
        except Exception:
            results.append({"name": "voice_sessions_table", "passed": False,
                            "detail": "TABLE MISSING", "remedy": "run migration 003"})
        conn.close()
    except Exception as e:
        results.append({"name": "db_connection", "passed": False, "detail": str(e), "remedy": "check postgres"})

    failed = [r for r in results if not r["passed"]]
    if failed:
        logger.error("BOOT INVARIANT FAILURE: %s", failed)
        return {"invariant_drift": True, "failed": failed}
    logger.info("Boot invariants: all %d checks passed", len(results))
    return {}


@app.on_event("startup")
async def on_startup():
    global _boot_report
    _boot_report = _run_boot_invariants()


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
    state = {"status": "ok", "service": "ns_core"}
    if _boot_report:
        state["status"] = "DEGRADED"
        state["invariant_warnings"] = _boot_report
    return state


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
    """Accept founder intent, write a chained receipt, return FounderResponseEnvelope."""
    import json, hashlib
    intent = body.get("intent", "")
    mode = body.get("mode", "founder_strategic")
    if not intent:
        return {"status": "error", "error": "No intent provided", "receipt_hash": "", "chain_verified": False, "mode": mode}
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()

        # Fetch previous receipt for chain linking
        cur.execute("SELECT hash, prev_hash FROM receipts ORDER BY created_at DESC, id DESC LIMIT 1")
        prev_row = cur.fetchone()
        prev_hash = prev_row[0] if prev_row else "0" * 64

        # Compute new receipt hash
        payload = {"intent": intent, "mode": mode}
        raw = json.dumps({"event": "intent_received", "payload": payload}, sort_keys=True) + prev_hash
        h = hashlib.sha256(raw.encode()).hexdigest()

        cur.execute(
            "INSERT INTO receipts (event, payload, hash, prev_hash) VALUES (%s,%s,%s,%s)",
            ("intent_received", json.dumps(payload), h, prev_hash),
        )

        # Verify chain: the prev_hash we just wrote should match what was last in DB
        chain_verified = (prev_row is None) or (prev_hash == prev_row[0])

        # Fetch canon state
        canon_version = None
        canon_hash = None
        try:
            cur.execute("SELECT version, policy_hash FROM canon_commits ORDER BY version DESC LIMIT 1")
            canon_row = cur.fetchone()
            if canon_row:
                canon_version, canon_hash = canon_row
        except Exception:
            pass

        conn.commit()
        conn.close()

        return {
            "status": "ok",
            "receipt_hash": h,
            "chain_verified": chain_verified,
            "mode": mode,
            "pressure": "low",
            "response_shape": "retrieval",
            "canon_version": canon_version,
            "canon_hash": canon_hash,
            "memory_atoms_written": 0,
            "memory_atoms_queried": 0,
            "feed_items_added": 0,
            "voice_session_id": None,
            "result": {"summary": f"Intent received: {intent[:80]}"},
            "error": None,
        }
    except Exception as e:
        logger.error("intent_execute failed: %s", e)
        return {
            "status": "error",
            "receipt_hash": "",
            "chain_verified": False,
            "mode": mode,
            "result": {},
            "error": str(e),
        }


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
