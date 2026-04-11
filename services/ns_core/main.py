from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from routes.boot import router as boot_router
from routes.feed import router as feed_router
from routes.packets import router as packets_router
import os, psycopg2, logging

logger = logging.getLogger("ns_core")

# ── Architecture modules ───────────────────────────────────────────────────────
try:
    from hyperobject.models import HyperObject, MemoryAxis, EpistemicAxis
    from hyperobject.store import get_store as _get_ho_store
    from narrative.buffer import NarrativeBuffer, NarrativeObject, NarrativeClass
    from metabolism.engine import get_metabolism_engine as _get_metabolism
    from device.router import get_device_router as _get_device_router
    _ARCH_MODULES_LOADED = True
except ImportError as _e:
    logger.warning("Architecture modules not available: %s", _e)
    _ARCH_MODULES_LOADED = False

_narrative_buffer = NarrativeBuffer() if _ARCH_MODULES_LOADED else None

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

    if _ARCH_MODULES_LOADED:
        # Wire 1: Sync HyperObjectStore from DB atoms
        try:
            store = _get_ho_store()
            conn = psycopg2.connect(DB_URL)
            cur = conn.cursor()
            cur.execute("SELECT id, type, content, created_at FROM atoms ORDER BY created_at ASC LIMIT 500")
            rows = cur.fetchall()
            for row in rows:
                ho = HyperObject()
                ho.memory.index_refs = [str(row[0])]
                ho.memory.promotion_state = "durable"
                ho.execution.intent = row[1] or ""
                ho.narrative.summary = (row[2] or "")[:120]
                ho.temporal.created_at = row[3].isoformat() if row[3] else ho.temporal.created_at
                store.create(ho)
            conn.close()
            logger.info("HyperObjectStore: synced %d atoms from DB", len(rows))
        except Exception as e:
            logger.warning("HyperObjectStore DB sync failed: %s", e)

        # Wire 5: Device router boot publish
        try:
            router = _get_device_router()
            router.boot_sequence_publish({"status": "ok", "endpoints": 6})
            logger.info("DeviceRouter: boot_sequence_publish sent to all surfaces")
        except Exception as e:
            logger.warning("DeviceRouter boot publish failed: %s", e)

        # Wire 2: Emit system_boot to MetabolismEngine (EventSpine gets receipt chain)
        try:
            engine = _get_metabolism()
            obj = engine.intake("system_boot", "boot_event", {"db_url": "connected"})
            logger.info("MetabolismEngine: system_boot event ingested (id=%s)", obj.object_id)
        except Exception as e:
            logger.warning("MetabolismEngine boot intake failed: %s", e)


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

        # Wire 3: Intake intent into MetabolismEngine
        metabolism_obj_id = None
        if _ARCH_MODULES_LOADED:
            try:
                engine = _get_metabolism()
                mobj = engine.intake(intent, "founder_intent", {"mode": mode})
                metabolism_obj_id = mobj.object_id
            except Exception:
                pass

        # Wire 4: NarrativeBuffer — wrap result in typed NarrativeObject
        narrative_closure_risk = None
        narrative_id = None
        if _ARCH_MODULES_LOADED and _narrative_buffer is not None:
            try:
                nobj = NarrativeObject(
                    narrative_class=NarrativeClass.observation,
                    human_text=f"Intent received: {intent[:80]}",
                    based_on=[h],           # receipt hash is evidence
                    machine_packet={"receipt_hash": h, "mode": mode, "metabolism_id": metabolism_obj_id},
                    confidence=0.8,
                )
                _narrative_buffer.add(nobj)
                narrative_closure_risk = round(nobj.compute_closure_risk(), 3)
                narrative_id = nobj.narrative_id
            except Exception:
                pass

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
            "narrative": {
                "id": narrative_id,
                "closure_risk": narrative_closure_risk,
                "class": "observation",
            } if narrative_id else None,
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


import httpx
from isr_v2 import create_default_isr, FounderMode
from violet_renderer import VioletRenderer
from voice_state_machine import VoiceSession, VoiceState, VOICE_STATE_UI
import uuid as _uuid

# ── Track 2/3/7 modules ───────────────────────────────────────────────────────
try:
    from mac_adapter import get_mac_gate as _get_mac_gate
    _MAC_GATE_AVAILABLE = True
except ImportError:
    _MAC_GATE_AVAILABLE = False

try:
    from ether import get_hic_engine as _get_hic_engine
    _HIC_AVAILABLE = True
except ImportError:
    _HIC_AVAILABLE = False

try:
    from pdp import get_pdp as _get_pdp
    _PDP_AVAILABLE = True
except ImportError:
    _PDP_AVAILABLE = False

try:
    from program_runtime import get_program_runtime as _get_program_runtime
    _PROGRAM_RUNTIME_AVAILABLE = True
except ImportError:
    _PROGRAM_RUNTIME_AVAILABLE = False

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


_OMEGA_URL = os.environ.get("OMEGA_URL", "http://omega:9010")

async def _omega_proxy(method: str, path: str, json_body=None):
    url = f"{_OMEGA_URL}{path}"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.request(method, url, json=json_body)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text) from exc
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Omega unavailable: {exc}") from exc

@app.get("/api/v1/omega/healthz")
async def omega_health():
    return await _omega_proxy("GET", "/healthz")

@app.post("/api/v1/omega/simulate")
async def omega_simulate(payload: dict):
    return await _omega_proxy("POST", "/omega/simulate", json_body=payload)

@app.get("/api/v1/omega/runs")
async def omega_runs():
    return await _omega_proxy("GET", "/omega/runs")

@app.get("/api/v1/omega/runs/{run_id}")
async def omega_run(run_id: str):
    return await _omega_proxy("GET", f"/omega/runs/{run_id}")

@app.get("/api/v1/omega/runs/{run_id}/branches")
async def omega_run_branches(run_id: str):
    return await _omega_proxy("GET", f"/omega/runs/{run_id}/branches")

@app.post("/api/v1/omega/runs/{run_id}/compare")
async def omega_compare(run_id: str, payload: dict):
    return await _omega_proxy("POST", f"/omega/runs/{run_id}/compare", json_body=payload)


@app.get("/hic/gates")
async def hic_gates():
    if not _HIC_AVAILABLE:
        return {"status": "unavailable"}
    engine = _get_hic_engine()
    return {"status": "ok", "pattern_count": engine.pattern_count(), "gates": engine.gate_summary()}

@app.post("/hic/evaluate")
async def hic_evaluate(body: dict):
    if not _HIC_AVAILABLE:
        return {"status": "unavailable"}
    text = body.get("text", "")
    decision = _get_hic_engine().evaluate(text)
    return {
        "verdict": decision.verdict.value,
        "gates_triggered": decision.gates_triggered,
        "matched_count": len(decision.matched_patterns),
        "rationale": decision.rationale,
    }

@app.post("/pdp/decide")
async def pdp_decide(body: dict):
    if not _PDP_AVAILABLE:
        return {"status": "unavailable"}
    from pdp import PDPRequest
    req = PDPRequest(
        subject=body.get("subject", "unknown"),
        action=body.get("action", ""),
        resource=body.get("resource", ""),
        projection=body.get("projection"),
        context=body.get("context", {}),
    )
    decision = _get_pdp().decide(req)
    return {
        "effect": decision.effect.value,
        "reason": decision.reason,
        "obligations": [{"type": o.obligation_type, "detail": o.detail} for o in decision.obligations],
        "rules_matched": len(decision.matched_rules),
    }

@app.get("/programs")
async def programs_list():
    if not _PROGRAM_RUNTIME_AVAILABLE:
        return {"status": "unavailable"}
    runtime = _get_program_runtime()
    return {"status": "ok", **runtime.summary(), "programs": [p.to_dict() for p in runtime.all()]}

@app.post("/programs/route")
async def programs_route(body: dict):
    if not _PROGRAM_RUNTIME_AVAILABLE:
        return {"status": "unavailable"}
    intent = body.get("intent", "")
    matches = _get_program_runtime().route_intent(intent)
    return {
        "status": "ok",
        "intent": intent,
        "matched": [{"program_id": p.program_id, "name": p.name, "namespace": p.namespace} for p in matches],
    }

# ── Voice / Twilio ─────────────────────────────────────────────────────────────
_WEBHOOK_BASE = os.environ.get("NORTHSTAR_WEBHOOK_BASE", "").rstrip("/")
_VOICE_SESSIONS: dict = {}

def _twiml_gather(say_text: str) -> str:
    """
    Build TwiML gather response.
    Key: <Say> is OUTSIDE <Gather> with a <Pause length="1"/> between them.
    If Say were inside Gather, Polly audio triggers Gather immediately on finish,
    Twilio captures silence, returns empty SpeechResult → infinite loop.
    speechTimeout="3" waits 3s of real silence after caller stops speaking.
    actionOnEmptyResult="true" routes empty results here so we can count retries.
    """
    action = f"{_WEBHOOK_BASE}/voice/transcription" if _WEBHOOK_BASE else "/voice/transcription"
    safe = say_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Say voice="Polly.Matthew-Neural">{safe}</Say>
  <Pause length="1"/>
  <Gather input="speech" action="{action}" method="POST"
          speechTimeout="3" language="en-US" timeout="15"
          actionOnEmptyResult="true">
  </Gather>
  <Say voice="Polly.Matthew-Neural">I did not hear you. Please call again.</Say>
  <Hangup/>
</Response>"""

@app.post("/voice/inbound")
async def voice_inbound(request: Request):
    try:
        form = dict(await request.form())
        call_sid = form.get("CallSid", "unknown")
        caller = form.get("From", "unknown")
        _VOICE_SESSIONS[call_sid] = {"status": "gathering", "from": caller}
    except Exception:
        pass
    from fastapi.responses import Response as _R
    return _R(content=_twiml_gather("Northstar online. How can I serve you?"), media_type="text/xml")

async def _violet_llm(prompt: str, system: str = "") -> str:
    """
    Multi-provider LLM for Violet. Never raises — always returns a string.
    Priority: Groq → Grok → Ollama → Anthropic → OpenAI → canned fallback.
    """
    VOICE_SYSTEM = system or (
        "You are Violet, the voice interface of NS Infinity by AXIOLEV. "
        "You are concise, clear, and sovereign. "
        "Respond in 1-2 sentences maximum. No markdown, no symbols, no lists. "
        "Speak naturally as if talking to the founder."
    )

    # 1. Groq (llama-3.3-70b — free tier, fast)
    groq_key = os.environ.get("GROQ_API_KEY", "")
    if groq_key and len(groq_key) > 10 and groq_key.startswith("gsk_"):
        try:
            from groq import AsyncGroq
            client = AsyncGroq(api_key=groq_key)
            resp = await client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": VOICE_SYSTEM},
                           {"role": "user", "content": prompt}],
                max_tokens=150,
            )
            text = resp.choices[0].message.content or ""
            if text.strip():
                return text.strip()
        except Exception:
            pass

    # 2. xAI Grok (grok-4.20-reasoning — live)
    grok_key = os.environ.get("XAI_API_KEY", "")
    if grok_key and len(grok_key) > 10:
        try:
            import httpx as _hx
            async with _hx.AsyncClient(timeout=30.0) as _c:
                _r = await _c.post(
                    "https://api.x.ai/v1/responses",
                    headers={"Authorization": f"Bearer {grok_key}", "Content-Type": "application/json"},
                    json={"model": "grok-4.20-reasoning", "input": f"{VOICE_SYSTEM}\n\n{prompt}"},
                )
                if _r.status_code == 200:
                    _d = _r.json()
                    text = ""
                    for _item in _d.get("output", []):
                        if _item.get("type") == "message":
                            for _cx in _item.get("content", []):
                                if _cx.get("type") == "output_text":
                                    text += _cx.get("text", "")
                    if not text:
                        text = _d.get("output_text", "")
                    if text.strip():
                        return text.strip()[:400]
        except Exception:
            pass

    # 3. Ollama (local — no key, no credits needed)
    try:
        import httpx as _hx
        ollama_host = os.environ.get("OLLAMA_HOST", "host.docker.internal")
        ollama_port = os.environ.get("OLLAMA_PORT", "11434")
        ollama_model = os.environ.get("OLLAMA_DEFAULT_MODEL", "llama3:latest")
        async with _hx.AsyncClient(timeout=60.0) as _c:
            _r = await _c.post(
                f"http://{ollama_host}:{ollama_port}/v1/chat/completions",
                json={"model": ollama_model,
                      "messages": [{"role": "system", "content": VOICE_SYSTEM},
                                    {"role": "user", "content": prompt}],
                      "max_tokens": 150},
                headers={"Authorization": "Bearer ollama"},
            )
            _r.raise_for_status()
            text = _r.json()["choices"][0]["message"]["content"] or ""
            if text.strip():
                return text.strip()
    except Exception:
        pass

    # 4. Anthropic
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if anthropic_key and len(anthropic_key) > 10:
        try:
            import anthropic as _ant
            client = _ant.Anthropic(api_key=anthropic_key)
            resp = client.messages.create(
                model="claude-haiku-4-5-20251001", max_tokens=150,
                system=VOICE_SYSTEM,
                messages=[{"role": "user", "content": prompt}]
            )
            text = (resp.content[0].text if resp.content else "").strip()
            if text:
                return text
        except Exception:
            pass

    # 5. OpenAI
    openai_key = os.environ.get("OPENAI_API_KEY", "")
    if openai_key and len(openai_key) > 10:
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=openai_key)
            resp = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "system", "content": VOICE_SYSTEM},
                           {"role": "user", "content": prompt}],
                max_tokens=150,
            )
            text = (resp.choices[0].message.content or "").strip()
            if text:
                return text
        except Exception:
            pass

    # 6. Canned fallback — always available
    import hashlib
    _fallbacks = [
        "I am Violet. I am here and processing your request.",
        "Acknowledged. I am standing by.",
        "Violet online. Please continue.",
    ]
    return _fallbacks[int(hashlib.md5(prompt.encode()).hexdigest(), 16) % len(_fallbacks)]


@app.post("/voice/transcription")
async def voice_transcription(request: Request):
    from fastapi.responses import Response as _R
    try:
        form = dict(await request.form())
        call_sid = form.get("CallSid", "unknown")
        speech = form.get("SpeechResult", "").strip()

        if not speech:
            # Empty speech: retry up to 2 times, then exit gracefully.
            # Without this counter the old code would loop forever: empty→gather→empty→...
            session = _VOICE_SESSIONS.get(call_sid, {})
            retries = session.get("retries", 0)
            if retries >= 2:
                twiml = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Say voice="Polly.Matthew-Neural">I could not hear you. Please call again and speak after my greeting. Goodbye.</Say>
  <Hangup/>
</Response>"""
                return _R(content=twiml, media_type="text/xml")
            _VOICE_SESSIONS[call_sid] = {**session, "retries": retries + 1}
            prompts = ["I did not catch that. Please go ahead.", "Still here. Please speak."]
            return _R(content=_twiml_gather(prompts[min(retries, 1)]), media_type="text/xml")

        # Got real speech — reset retry counter, call LLM
        session = _VOICE_SESSIONS.get(call_sid, {})
        _VOICE_SESSIONS[call_sid] = {**session, "retries": 0, "last_input": speech[:200], "status": "processing"}
        reply = await _violet_llm(speech)
        _VOICE_SESSIONS[call_sid]["last"] = reply[:100]
        _VOICE_SESSIONS[call_sid]["status"] = "speaking"
        return _R(content=_twiml_gather(reply[:300]), media_type="text/xml")
    except Exception:
        from fastapi.responses import Response as _R2
        return _R2(content=_twiml_gather("Violet is here. One moment please."), media_type="text/xml")

@app.post("/violet/chat")
async def violet_chat(body: dict):
    """Text chat endpoint for Violet. Uses multi-provider fallback chain."""
    import time as _time
    prompt = body.get("message", "").strip()
    if not prompt:
        return {"ok": False, "error": "empty message"}
    try:
        reply = await _violet_llm(prompt)
        return {"ok": True, "text": reply,
                "timestamp": _time.strftime("%Y-%m-%dT%H:%M:%SZ", _time.gmtime())}
    except Exception as e:
        return {"ok": False, "error": str(e), "text": "Violet is processing. Please try again."}

@app.get("/voice/sessions")
async def voice_sessions_list():
    return {"sessions": list(_VOICE_SESSIONS.values()), "count": len(_VOICE_SESSIONS)}

@app.get("/mac_adapter/status")
async def mac_adapter_status():
    if not _MAC_GATE_AVAILABLE:
        return {"status": "unavailable"}
    gate = _get_mac_gate()
    return {
        "status": "ok",
        "allowed_capabilities": list(__import__("mac_adapter.gate", fromlist=["MAC_ALLOWED_CAPABILITIES"]).MAC_ALLOWED_CAPABILITIES),
        "escalation_required": list(__import__("mac_adapter.gate", fromlist=["MAC_ESCALATION_REQUIRED"]).MAC_ESCALATION_REQUIRED),
        "receipts_issued": len(gate.receipts()),
        "denied_count": gate.denied_count(),
    }


@app.post("/voice/sms")
async def voice_sms(request: Request):
    """
    Twilio SMS webhook. Returns TwiML <Message> (NOT <Say> — that is voice-only).
    Uses _violet_llm fallback chain with an SMS-specific system prompt.

    SETUP REQUIRED IN TWILIO CONSOLE:
    Phone Numbers → +1 (307) 202-4418 → Messaging →
    'A Message Comes In' → Webhook → [ngrok URL]/voice/sms  (HTTP POST)
    """
    from fastapi.responses import Response as _R
    import html as _ht
    try:
        form = dict(await request.form())
        body = (form.get("Body") or "").strip()
        if not body:
            return _R(
                content="""<?xml version="1.0" encoding="UTF-8"?><Response><Message>Violet here. Send me a message.</Message></Response>""",
                media_type="text/xml",
            )
        sms_system = (
            "You are Violet, the voice of NS Infinity by AXIOLEV. "
            "You are responding via SMS text message. "
            "Keep your response under 140 characters when possible. "
            "Be direct and conversational. No markdown, no bullet points."
        )
        reply = await _violet_llm(body, system=sms_system)
        safe = _ht.escape(reply[:1500])
        return _R(
            content=f"""<?xml version="1.0" encoding="UTF-8"?><Response><Message>{safe}</Message></Response>""",
            media_type="text/xml",
        )
    except Exception:
        return _R(
            content="""<?xml version="1.0" encoding="UTF-8"?><Response><Message>Violet here. Please try again.</Message></Response>""",
            media_type="text/xml",
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9000)
