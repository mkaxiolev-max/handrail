# Copyright © 2026 Axiolev. All rights reserved.
"""
NORTHSTAR API Server — Constitutional AI Operating System
NS∞ / AXIOLEV Holdings — Conciliar Architecture v1.0

Pillars:
  1. Intelligence Layer  (Arbiter, quad-LLM, SafeSpeak)
  2. Memory Layer        (Receipts, Alexandria, Canon)
  3. Interface Layer     (VOICE — Computer lane)
  4. Action Layer        (Trade actuator, market ingest)
  5. Governance Layer    (Auth, roles, conciliar, founder veto)

Endpoints: /auth /chat /receipts /approvals /visuals /canon
           /voice /actions /health /ws /console /
"""

import os
import requests
from requests import exceptions as req_exc
import sys
import json
import asyncio
import secrets
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, List

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, Depends
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from nss.core.storage import bootstrap, health as storage_health, get_ether
from nss.core.receipts import ReceiptChain
from nss.core.arbiter import Arbiter
from nss.core.auth import (
    get_auth, require_auth, require_founder, require_permission,
    AuthContext, PERMISSIONS
)
from nss.core.events import (
    get_bus, get_chat, get_approvals, get_visuals, get_canon_store,
    WSConnection
)
from nss.interfaces.voice_lane import (
    get_or_create_session, close_session, active_sessions,
    check_voice_configured, build_arbiter_context,
    safe_speak_filter, load_persisted_sessions,
    NORTHSTAR_WEBHOOK_BASE, TWILIO_PHONE_NUMBER,
    TIER_F, TIER_E,
)
from nss.interfaces.twilio_voice import (
    twiml_answer as _twiml_answer,
    twiml_respond as _twiml_respond,
    twiml_hangup as _twiml_hangup,
    twiml_conference_join,
    get_or_create_conference,
    active_conferences,
    _conferences,
)

def twiml_answer_for(session) -> str:
    base = os.environ.get("NORTHSTAR_WEBHOOK_BASE", "")
    return _twiml_answer(gather_action=f"{base}/voice/transcription")

def twiml_respond_for(text: str, session) -> str:
    base = os.environ.get("NORTHSTAR_WEBHOOK_BASE", "")
    return _twiml_respond(message=text, gather_action=f"{base}/voice/transcription")

def twiml_hangup_for(msg: str = "NORTHSTAR standing by.") -> str:
    return _twiml_hangup(farewell=msg) if hasattr(_twiml_hangup, '__call__') else _twiml_respond(msg, None)

def twiml_confirm_for(session, speech: str) -> str:
    """Simple TwiML confirm flow."""
    base = os.environ.get("NORTHSTAR_WEBHOOK_BASE", "")
    return _twiml_respond(
        message=f"I heard: {speech[:100]}. Say YES to confirm or NO to cancel.",
        gather_action=f"{base}/voice/transcription"
    )
from nss.actuators.alpaca_trading import AlpacaActuator
from nss.jobs.ether_ingest import overnight_ether_loop
from nss.api.dashboard import get_dashboard_html
from nss.api.console import CONSOLE_HTML
from nss.core.sfe import (
    get_sfe, SocraticFieldEngine, QuestionType, VersionImpact,
    ConflictResolution, ConfidenceTier, ConflictType
)
from nss.core.canon_docs import ingest_canon_docs, summarize_ingest
from nss.core.pressure import get_stabilization_engine, get_spf_zone, SPFZone
from nss.mcp.router import get_mcp_router
from nss.jobs.ingest_watcher import get_ingest_engine, get_crawler, get_drop_watcher
from nss.actuators.san_terrain import get_terrain_engine
from nss.jobs.uspto_ingest import get_uspto_ingest, BandwidthBudget
from nss.jobs.san_uspto import (
    get_san_engine, get_active_run, get_last_progress,
    TerrainConfig, TerrainMode
)


class ExecRequest(BaseModel):
    cmd: str

def create_app() -> FastAPI:
    app = FastAPI(title="NORTHSTAR", version="2.0.0", docs_url="/docs", redoc_url=None, openapi_url="/openapi.json")

    app.add_middleware(CORSMiddleware, allow_origins=["*"],
                       allow_methods=["*"], allow_headers=["*"])

    @app.on_event("startup")
    async def startup():
        asyncio.create_task(overnight_ether_loop())

    # ── Bootstrap ─────────────────────────────────────────────────────────────
    print("")
    print("=" * 62)
    print("⚡ NORTHSTAR OS — NS∞ / AXIOLEV Holdings")
    print("   Ω Advisory Sovereignty Law: ACTIVE")
    print("   Conciliar Architecture v1.0: ACTIVE")
    print("=" * 62)

    bootstrap()
    receipt_chain = ReceiptChain()
    arbiter       = Arbiter()
    alpaca        = AlpacaActuator()
    auth          = get_auth()
    bus           = get_bus()
    chat_store    = get_chat()
    approval_store= get_approvals()
    visual_store  = get_visuals()
    canon_store   = get_canon_store()
    voice_health  = check_voice_configured()
    sfe = get_sfe(receipt_chain=receipt_chain)

    # ── Canon Document Ingest ──────────────────────────────────────────────────
    # Load NS Primitives first (foundational — must precede all domain modules)
    # Idempotent — skips docs already stored at current hash
    try:
        import pathlib
        _base_dir = pathlib.Path(__file__).parent.parent.parent  # NSS root
        _canon_results = ingest_canon_docs(_base_dir, receipt_chain=receipt_chain)
        print(f"  ✓ {summarize_ingest(_canon_results)}")
    except Exception as _e:
        print(f"  ⚠  Canon doc ingest error: {_e}")

    # ── Stabilization Engine ──────────────────────────────────────────────────
    stab = get_stabilization_engine(receipt_chain=receipt_chain)
    print("  ✓ Stabilization engine online (SPF | CCT | SCS)")

    # ── Ether Ingest Engine ────────────────────────────────────────────────────
    ingest = get_ingest_engine(receipt_chain=receipt_chain)
    _stats = ingest.get_stats()
    print(f"  \u2713 Ether ingest: {_stats['total_docs']} docs in Alexandria")

    # ── SAN Terrain Engine ─────────────────────────────────────────────────────
    terrain = get_terrain_engine(receipt_chain=receipt_chain)
    _tstats = terrain.stats()
    print(f"  \u2713 SAN terrain: {_tstats['patents']} patents | {_tstats['claims']} claims | {_tstats['snapshots']} snapshots")

    # ── SAN USPTO Terrain Engine ───────────────────────────────────────────────
    san = get_san_engine(receipt_chain=receipt_chain)
    _san_stats = san.store.get_stats()
    print(f"  ✓ SAN terrain: {_san_stats['patents']} patents | {_san_stats['snapshots']} snapshots")

    # ── MCP Tool Router ──────────────────────────────────────────────────────
    mcp = get_mcp_router(receipt_chain=receipt_chain)
    print(f"  ✓ MCP router online ({len(mcp.list_tools())} tools governed)")

    @app.on_event("startup")
    async def start_background_tasks():
        watcher = get_drop_watcher(receipt_chain=receipt_chain)
        asyncio.create_task(watcher.run())

    # ── Alexandria Boot Proof ──────────────────────────────────────────────────
    _ALEXANDRIA_SNAPSHOTS_DIR = Path("/tmp/alexandria_snapshots")
    _ALEXANDRIA_SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    _ALEXANDRIA_LEDGER = Path("/tmp/ns_alexandria_boot.jsonl")
    # SSD persistence paths
    _SSD_ALEXANDRIA = Path("/Volumes/NSExternal/ALEXANDRIA")
    _SSD_SNAPSHOTS_DIR = _SSD_ALEXANDRIA / "snapshots"
    _SSD_LEDGER_DIR = _SSD_ALEXANDRIA / "ledger"
    _SSD_MOUNTED = _SSD_ALEXANDRIA.exists()
    if _SSD_MOUNTED:
        _SSD_SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)
        _SSD_LEDGER_DIR.mkdir(parents=True, exist_ok=True)
        (_SSD_ALEXANDRIA / "ether").mkdir(parents=True, exist_ok=True)
    _boot_entry = json.dumps({"event": "NS_BOOT", "ts": datetime.utcnow().isoformat() + "Z",
                               "version": "2.0.0"})
    with _ALEXANDRIA_LEDGER.open("a") as _f:
        _f.write(_boot_entry + "\n")
    if _SSD_MOUNTED:
        with (_SSD_LEDGER_DIR / "ns_receipt_chain.jsonl").open("a") as _f:
            _f.write(_boot_entry + "\n")
    try:
        import hashlib as _hlib
        _snap_data = {"tag": "boot", "ts": datetime.utcnow().isoformat() + "Z", "entry": _boot_entry}
        _snap_hash = _hlib.sha256(json.dumps(_snap_data, sort_keys=True).encode()).hexdigest()
        _snap_file = _ALEXANDRIA_SNAPSHOTS_DIR / f"snapshot_boot_{_snap_hash[:8]}.json"
        with _snap_file.open("w") as _f:
            json.dump({**_snap_data, "snapshot_hash": _snap_hash}, _f)
        print(f"  ✓ Alexandria boot proof: snapshot {_snap_hash[:8]} written (local)")
        if _SSD_MOUNTED:
            _ssd_snap_file = _SSD_SNAPSHOTS_DIR / f"snapshot_boot_{_snap_hash[:8]}.json"
            with _ssd_snap_file.open("w") as _f:
                json.dump({**_snap_data, "snapshot_hash": _snap_hash, "ssd": True}, _f)
            print(f"  ✓ Alexandria boot proof: snapshot {_snap_hash[:8]} mirrored to SSD")
    except Exception as _ae:
        print(f"  ⚠  Alexandria boot proof error: {_ae}")

    # ── Voice Session Reload from SSD ──────────────────────────────────────────
    try:
        _persisted = load_persisted_sessions(max_age_hours=24)
        if _persisted:
            active_sessions.update(_persisted)
            print(f"  ✓ Voice sessions reloaded from SSD: {len(_persisted)} sessions")
        else:
            print(f"  ✓ Voice sessions: no recent sessions on SSD")
    except Exception as _vse:
        print(f"  ⚠  Voice session reload error: {_vse}")

    _SSD_RECEIPT_LEDGER = Path("/Volumes/NSExternal/ALEXANDRIA/ledger/ns_receipt_chain.jsonl")

    async def emit_receipt(event_type: str, source: dict, inputs: dict, outputs: dict) -> dict:
        """Emit receipt and broadcast receipt.new to connected consoles."""
        receipt = receipt_chain.emit(event_type, source, inputs, outputs)
        try:
            await bus.broadcast("receipt.new", receipt)
        except Exception:
            pass
        try:
            if _SSD_RECEIPT_LEDGER.parent.exists():
                with _SSD_RECEIPT_LEDGER.open("a") as _lf:
                    _lf.write(json.dumps(receipt) + "\n")
        except Exception:
            pass
        return receipt


    boot_receipt = receipt_chain.emit(
        event_type="BOOT",
        source={"kind": "system", "ref": "omega_boot_v2"},
        inputs={},
        outputs={
            "storage":    storage_health(),
            "voice_lane": voice_health,
            "alpaca":     alpaca.health(),
            "conciliar":  "v1.0",
        },
    )

    print(f"")
    print(f"─── Intelligence Layer ──────────────────────────────────")
    print("✓ Claude" if os.environ.get("ANTHROPIC_API_KEY") else "✗ Claude")
    print("✓ GPT-4o" if os.environ.get("OPENAI_API_KEY") else "  GPT-4o: not set")
    print("✓ Gemini" if os.environ.get("GOOGLE_API_KEY") else "  Gemini: not set")
    print("✓ Grok"   if os.environ.get("GROK_API_KEY") else "  Grok: not set")
    print(f"─── Voice ───────────────────────────────────────────────")
    print(f"{'✓' if voice_health['lane_active'] else '✗'} Computer: {TWILIO_PHONE_NUMBER}")
    print(f"  Webhook: {'✓' if voice_health['webhook_configured'] else '⚠ Run ngrok, then set NORTHSTAR_WEBHOOK_BASE'}")
    print(f"─── Console ─────────────────────────────────────────────")
    print(f"  Dashboard: http://localhost:{os.environ.get('NORTHSTAR_PORT', 9000)}")
    print(f"  Console:   http://localhost:{os.environ.get('NORTHSTAR_PORT', 9000)}/console")
    print(f"  Login:     user=founder, password=northstar (change on first boot)")
    print(f"=" * 62)
    print(f"")

    # ═══════════════════════════════════════════════════════════════════════════
    # AUTH ENDPOINTS
    # ═══════════════════════════════════════════════════════════════════════════

    @app.post("/auth/login")
    async def auth_login(request: Request):
        body = await request.json()
        user_id = body.get("user_id", "").strip()
        password = body.get("password", "")
        device_name = body.get("device_name", "unknown")
        ip = request.client.host if request.client else "unknown"

        result = auth.login(user_id, password, device_name, ip)
        if not result:
            return JSONResponse({"error": "Invalid credentials"}, status_code=401)

        receipt_chain.emit(
            event_type="AUTH_LOGIN",
            source={"kind": "auth", "ref": user_id},
            inputs={"device_name": device_name, "ip": ip},
            outputs={"role": result["role"], "session_id": result["session_id"]},
        )
        return result

    @app.post("/auth/refresh")
    async def auth_refresh(request: Request):
        body = await request.json()
        result = auth.refresh(body.get("refresh_token", ""))
        if not result:
            return JSONResponse({"error": "Invalid refresh token"}, status_code=401)
        return result

    @app.post("/auth/logout")
    async def auth_logout(request: Request, ctx: AuthContext = Depends(require_auth)):
        auth.logout(ctx.session_id)
        return {"status": "logged_out"}

    @app.get("/auth/me")
    async def auth_me(request: Request, ctx: AuthContext = Depends(require_auth)):
        return ctx.to_dict()

    @app.get("/auth/sessions")
    async def auth_sessions(request: Request, ctx: AuthContext = Depends(require_auth)):
        if ctx.is_founder():
            sessions = list(auth.sessions._sessions.values())
        else:
            sessions = auth.sessions.list_for_user(ctx.user_id)
        return {"sessions": sessions}

    @app.get("/auth/users")
    async def auth_users(request: Request, ctx: AuthContext = Depends(require_founder)):
        return {"users": auth.users.list_users()}

    @app.post("/auth/users/create")
    async def auth_create_user(request: Request, ctx: AuthContext = Depends(require_founder)):
        body = await request.json()
        try:
            user = auth.users.create_user(
                user_id=body["user_id"],
                display_name=body.get("display_name", body["user_id"]),
                role=body["role"],
                allowed_domains=body.get("allowed_domains", ["voice"]),
                password=body["password"],
            )
            receipt_chain.emit("USER_CREATED", {"kind": "auth", "ref": ctx.user_id},
                               {}, {"new_user": user["user_id"], "role": user["role"]})
            return user
        except Exception as e:
            return JSONResponse({"error": str(e)}, status_code=400)

    # ═══════════════════════════════════════════════════════════════════════════
    # YUBIKEY AUTH
    # ═══════════════════════════════════════════════════════════════════════════

    _YUBIKEY_SERIAL    = os.environ.get("YUBIKEY_SERIAL", "")
    _YUBIKEY_CLIENT_ID = os.environ.get("YUBIKEY_CLIENT_ID", "").strip()
    _YUBIKEY_SECRET    = os.environ.get("YUBIKEY_SECRET_KEY", "").strip()
    _YUBIKEY_MODHEX    = "cbdefghijklnrtuv"
    _YUBIKEY_SESSIONS: dict = {}

    if not _YUBIKEY_CLIENT_ID:
        print("  ⚠  YUBIKEY_CLIENT_ID not set — using public demo client (id=1). "
              "Get a real key at https://upgrade.yubico.com/getapikey/")

    def _is_modhex(s: str) -> bool:
        return all(c in _YUBIKEY_MODHEX for c in s.lower())

    async def _yubicloud_verify(otp: str, nonce: str) -> dict:
        """Call YubiCloud OTP verification API (api.yubico.com).
        Uses YUBIKEY_CLIENT_ID if set; falls back to public demo client id=1.
        Returns dict with keys: status, nonce, t (timestamp), sl (sync level).
        """
        import urllib.parse
        client_id = _YUBIKEY_CLIENT_ID or "1"
        params = urllib.parse.urlencode({"id": client_id, "otp": otp, "nonce": nonce})
        url = f"https://api.yubico.com/wsapi/2.0/verify?{params}"
        try:
            import httpx as _httpx
            async with _httpx.AsyncClient(timeout=8.0) as _c:
                resp = await _c.get(url)
            lines = resp.text.strip().splitlines()
            result = {}
            for line in lines:
                if "=" in line:
                    k, _, v = line.partition("=")
                    result[k.strip()] = v.strip()
            return result
        except Exception as e:
            return {"status": "YUBICLOUD_UNREACHABLE", "error": str(e)}

    @app.post("/auth/yubikey")
    async def auth_yubikey(request: Request):
        try:
            body = await request.json()
        except Exception:
            form = dict(await request.form())
            body = form
        otp = (body.get("otp") or "").strip()
        if not otp:
            return JSONResponse({"ok": False, "error": "otp_required"}, status_code=400)
        if len(otp) != 44 or not _is_modhex(otp):
            return JSONResponse({"ok": False, "error": "invalid_otp_format",
                                 "detail": "OTP must be 44 modhex characters"}, status_code=400)
        device_id = otp[:12]
        import hashlib, secrets
        nonce = secrets.token_hex(16)
        cloud = await _yubicloud_verify(otp, nonce)
        cloud_status = cloud.get("status", "")
        if cloud_status == "YUBICLOUD_UNREACHABLE":
            return JSONResponse({"ok": False, "error": "yubicloud_unreachable",
                                 "detail": cloud.get("error", "network error")}, status_code=503)
        if cloud_status != "OK":
            return JSONResponse({"ok": False, "error": "otp_rejected",
                                 "yubicloud_status": cloud_status,
                                 "device_id": device_id}, status_code=401)
        # OTP valid — issue session token
        token_payload = f"{device_id}:{_YUBIKEY_SERIAL}:{datetime.utcnow().isoformat()}"
        token = "ysk_" + hashlib.sha256((token_payload + nonce).encode()).hexdigest()[:32]
        _YUBIKEY_SESSIONS[token] = {
            "device_id": device_id,
            "serial": _YUBIKEY_SERIAL,
            "issued_at": datetime.utcnow().isoformat() + "Z",
            "yubicloud_status": cloud_status,
            "yubicloud_sl": cloud.get("sl", ""),
        }
        receipt_chain.emit("YUBIKEY_AUTH", {"kind": "auth", "ref": device_id},
                           {"serial": _YUBIKEY_SERIAL, "device_id": device_id,
                            "yubicloud_status": cloud_status}, {})
        return {
            "ok": True,
            "token": token,
            "device_id": device_id,
            "serial": _YUBIKEY_SERIAL,
            "yubicloud_status": cloud_status,
            "issued_at": _YUBIKEY_SESSIONS[token]["issued_at"],
        }

    @app.get("/auth/yubikey/test")
    async def auth_yubikey_test():
        """Diagnostic endpoint — reports YubiKey config state without auth."""
        client_id_set = bool(_YUBIKEY_CLIENT_ID)
        return {
            "ok": client_id_set,
            "client_id_set": client_id_set,
            "client_id": _YUBIKEY_CLIENT_ID if client_id_set else None,
            "secret_set": bool(_YUBIKEY_SECRET),
            "serial_set": bool(_YUBIKEY_SERIAL),
            "serial": _YUBIKEY_SERIAL or None,
            "mode": "live_yubicloud" if client_id_set else "demo_client_id_1",
            "error": None if client_id_set else "client_id_not_configured",
            "instructions": "POST /auth/yubikey with {\"otp\": \"<44-char modhex OTP from key touch>\"}",
        }

    # ═══════════════════════════════════════════════════════════════════════════
    # WEBSOCKET
    # ═══════════════════════════════════════════════════════════════════════════

    @app.websocket("/ws")
    async def websocket_endpoint(ws: WebSocket):
        await ws.accept()
        # Verify token from query param
        token = ws.query_params.get("token", "")
        ctx = auth.verify_request("Bearer " + token)
        if not ctx:
            await ws.send_text(json.dumps({"event": "error", "data": {"message": "Unauthorized"}}))
            await ws.close()
            return

        conn = WSConnection(
            ws=ws,
            user_id=ctx.user_id,
            role=ctx.role,
            session_id=ctx.session_id,
            allowed_domains=ctx.allowed_domains,
        )
        await bus.connect(conn)

        try:
            while True:
                raw = await ws.receive_text()
                msg = json.loads(raw)
                event = msg.get("event", "")
                data  = msg.get("data", {})

                if event == "chat.send":
                    # Route through arbiter
                    query = data.get("query", "")
                    if query:
                        result = await asyncio.to_thread(
                            arbiter.route, query,
                            {"tier": ctx.role, "session_id": ctx.session_id}
                        )
                        response = result.fused_response if result else "No response."
                        msg_obj = {
                            "role": "assistant",
                            "content": response,
                            "confidence": "draft",
                            "session_id": data.get("session_id", "default"),
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        }
                        await bus.broadcast("chat.message.new", msg_obj, user_id=ctx.user_id)

                elif event == "approval.respond":
                    approval_id = data.get("approval_id")
                    resolution  = data.get("resolution")
                    nonce       = data.get("nonce", "")
                    result = approval_store.resolve(approval_id, ctx.user_id, resolution, nonce)
                    if result:
                        await bus.broadcast("action.status", result)

        except WebSocketDisconnect:
            pass
        finally:
            await bus.disconnect(ctx.session_id)

    # ═══════════════════════════════════════════════════════════════════════════
    # HEALTH
    # ═══════════════════════════════════════════════════════════════════════════

    # ── MCP TOOL ROUTER ───────────────────────────────────────────────────────

    @app.get("/mcp/tools")
    async def mcp_list_tools(category: str = None,
                              ctx: AuthContext = Depends(require_auth)):
        tools = mcp.list_tools(category=category)
        return {"tools": tools, "count": len(tools)}

    @app.post("/mcp/execute")
    async def mcp_execute_tool(request: Request,
                                ctx: AuthContext = Depends(require_auth)):
        body = await request.json()
        tool_name = body.get("tool_name", "")
        args = body.get("args", {})
        domain = body.get("domain", "general")
        if not tool_name:
            return JSONResponse({"error": "tool_name required"}, status_code=400)
        call = ToolCall(tool_name=tool_name, args=args,
                        requested_by=ctx.user_id, domain=domain,
                        session_id=body.get("session_id", ""))
        result = await mcp.execute(call, ctx_role=ctx.role)
        await bus.broadcast("mcp.tool.executed",
                            {"tool": tool_name, "success": result.success,
                             "duration_ms": result.duration_ms},
                            min_role="EXEC")
        return result.to_dict()

    @app.get("/mcp/log")
    async def mcp_call_log(limit: int = 50,
                            ctx: AuthContext = Depends(require_auth)):
        if not ctx.has("VIEW_PRESSURE"):
            return JSONResponse({"error": "Forbidden"}, status_code=403)
        return {"calls": mcp.get_call_log(limit), "count": limit}

    # ── ARTIFACTS ──────────────────────────────────────────────────────────────

    @app.post("/artifacts/infographic")
    async def artifact_infographic(request: Request,
                                    ctx: AuthContext = Depends(require_auth)):
        spec = await request.json()
        svg = render_infographic_svg(spec)
        return {"svg": svg, "bytes": len(svg)}

    @app.post("/artifacts/deck")
    async def artifact_deck(request: Request,
                             ctx: AuthContext = Depends(require_auth)):
        spec = await request.json()
        import time as _time
        out = f"/tmp/ns_workspace/deck_{int(_time.time())}.pptx"
        pathlib.Path(out).parent.mkdir(parents=True, exist_ok=True)
        render_deck_pptx(spec, out)
        from fastapi.responses import FileResponse
        return FileResponse(out, media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                            filename="NS_deck.pptx")

    @app.post("/artifacts/brief")
    async def artifact_brief(request: Request,
                              ctx: AuthContext = Depends(require_auth)):
        spec = await request.json()
        import time as _time
        out = f"/tmp/ns_workspace/brief_{int(_time.time())}.pdf"
        pathlib.Path(out).parent.mkdir(parents=True, exist_ok=True)
        render_brief_pdf(spec, out)
        from fastapi.responses import FileResponse
        return FileResponse(out, media_type="application/pdf",
                            filename="NS_brief.pdf")

    @app.get("/artifacts/runs")
    async def artifact_runs(ctx: AuthContext = Depends(require_auth)):
        return {"runs": list_runs(20)}

    # ── PODCAST ────────────────────────────────────────────────────────────────

    @app.get("/podcast/episodes")
    async def podcast_list(ctx: AuthContext = Depends(require_auth)):
        return {"episodes": list_episodes(20)}

    @app.post("/podcast/package")
    async def podcast_package(request: Request,
                               ctx: AuthContext = Depends(require_auth)):
        body = await request.json()
        sources = body.get("sources", [])
        episode_id = body.get("episode_id")
        if not sources:
            return JSONResponse({"error": "sources required"}, status_code=400)
        packager = SourcePackager()
        pack = packager.package(sources, episode_id)
        receipt_chain.emit("PODCAST_SOURCED",
                           {"kind": "podcast", "ref": ctx.user_id},
                           {"pack_id": pack["pack_id"]},
                           {"source_count": len(sources), "word_count": pack["word_count"]})
        return pack

    @app.post("/podcast/generate")
    async def podcast_generate(request: Request,
                                ctx: AuthContext = Depends(require_auth)):
        body = await request.json()
        pack_id = body.get("pack_id", "")
        style = body.get("style", "conversational")
        hosts = body.get("hosts")
        if not pack_id:
            return JSONResponse({"error": "pack_id required"}, status_code=400)
        runner = Showrunner()
        try:
            episode = runner.generate(pack_id, style=style, hosts=hosts)
        except ValueError as e:
            return JSONResponse({"error": str(e)}, status_code=404)
        receipt_chain.emit("PODCAST_GENERATED",
                           {"kind": "podcast", "ref": ctx.user_id},
                           {"episode_id": episode["episode_id"], "pack_id": pack_id},
                           {"segment_count": len(episode["segments"]),
                            "claim_count": len(episode["claims"])})
        await bus.broadcast("podcast.episode.ready",
                            {"episode_id": episode["episode_id"],
                             "title": episode["title"]},
                            min_role="EXEC")
        return episode

    @app.get("/podcast/{episode_id}")
    async def podcast_get(episode_id: str, ctx: AuthContext = Depends(require_auth)):
        ep = load_episode(episode_id)
        if not ep:
            return JSONResponse({"error": "Not found"}, status_code=404)
        return ep

    @app.post("/podcast/{episode_id}/audio")
    async def podcast_audio(episode_id: str, ctx: AuthContext = Depends(require_auth)):
        ep = load_episode(episode_id)
        if not ep:
            return JSONResponse({"error": "Not found"}, status_code=404)
        audio_eng = AudioEngine()
        result = audio_eng.generate_audio(ep)
        return result

    @app.post("/podcast/{episode_id}/listener")
    async def podcast_listener_input(episode_id: str, request: Request,
                                      ctx: AuthContext = Depends(require_auth)):
        """Live listener input — creates CCT trajectory in pressure engine."""
        ep = load_episode(episode_id)
        if not ep:
            return JSONResponse({"error": "Episode not found"}, status_code=404)
        body = await request.json()
        text = body.get("text", "")
        speaker = body.get("speaker", ctx.user_id)
        from nss.actuators.podcast import LiveSession
        session = LiveSession(ep, pressure_engine=stab, receipt_chain=receipt_chain)
        result = session.handle_listener_input(text, speaker)
        spf = session.get_spf_status()
        await bus.broadcast("podcast.listener.input",
                            {"episode_id": episode_id, "approved": result["approved"],
                             "spf_zone": spf.get("zone")},
                            min_role="USER")
        return {**result, "pressure": spf}

    # ── PRESSURE / STABILIZATION ──────────────────────────────────────────────

    @app.get("/pressure/domains")
    async def pressure_all_domains(ctx: AuthContext = Depends(require_auth)):
        """SPF summary for all known domains."""
        if not ctx.has("VIEW_PRESSURE"):
            return JSONResponse({"error": "Forbidden"}, status_code=403)
        domains = stab.get_all_domains_overview()
        return {"domains": domains, "count": len(domains)}

    @app.get("/pressure/{domain}")
    async def pressure_domain(domain: str, ctx: AuthContext = Depends(require_auth)):
        """Full stabilization dashboard for one domain."""
        if not ctx.has("VIEW_PRESSURE"):
            return JSONResponse({"error": "Forbidden"}, status_code=403)
        dashboard = stab.get_domain_dashboard(domain)
        return dashboard

    @app.get("/pressure/{domain}/trajectories")
    async def pressure_trajectories(domain: str, ctx: AuthContext = Depends(require_auth)):
        """Active CCTs for a domain."""
        if not ctx.has("VIEW_PRESSURE"):
            return JSONResponse({"error": "Forbidden"}, status_code=403)
        ccts = stab.cct.get_active_ccts(domain)
        return {
            "domain": domain,
            "active_ccts": [c.to_dict() for c in ccts],
            "count": len(ccts)
        }

    @app.post("/pressure/{domain}/trajectory")
    async def pressure_add_trajectory(domain: str, request: Request,
                                       ctx: AuthContext = Depends(require_auth)):
        """Manually add a trajectory to a domain's CCT."""
        if not ctx.has("MANAGE_PRESSURE"):
            return JSONResponse({"error": "Forbidden"}, status_code=403)
        body = await request.json()
        topic = body.get("topic", "")
        summary = body.get("summary", "")
        if not topic or not summary:
            return JSONResponse({"error": "topic and summary required"}, status_code=400)
        cct = stab.cct.get_or_create_cct(domain, topic)
        traj = stab.cct.add_trajectory(domain, cct.id, summary,
                                         receipt_chain=receipt_chain)
        receipt_chain.emit("TRAJECTORY_ADDED",
                           {"kind": "pressure", "ref": ctx.user_id},
                           {"domain": domain, "topic": topic},
                           {"trajectory_id": traj.id, "summary": summary})
        await bus.broadcast("pressure.trajectory.added",
                            {"domain": domain, "cct_id": cct.id},
                            min_role="EXEC")
        return {"cct_id": cct.id, "trajectory_id": traj.id}

    @app.post("/pressure/{domain}/commit")
    async def pressure_commit(domain: str, request: Request,
                               ctx: AuthContext = Depends(require_founder)):
        """Commit a winning trajectory for a domain. Founder only."""
        body = await request.json()
        cct_id = body.get("cct_id", "")
        trajectory_id = body.get("trajectory_id", "")
        if not cct_id or not trajectory_id:
            return JSONResponse({"error": "cct_id and trajectory_id required"}, status_code=400)
        spf = stab.spf.compute_spf(domain)
        scs = stab.scs.compute_scs(domain)
        result = stab.cct.commit_trajectory(
            domain, cct_id, trajectory_id,
            spf_at_commit=spf, scs_at_commit=scs.total,
            receipt_chain=receipt_chain
        )
        if not result:
            return JSONResponse({"error": "CCT or trajectory not found"}, status_code=404)
        stab.post_commit_reset(domain)
        await bus.broadcast("pressure.domain.committed",
                            {"domain": domain, "commit_form": result.commit_form},
                            min_role="EXEC")
        return {"status": "committed", "domain": domain, "commit_form": result.commit_form}

    @app.post("/pressure/{domain}/signal")
    async def pressure_add_signal(domain: str, request: Request,
                                   ctx: AuthContext = Depends(require_auth)):
        """Manually record a pressure signal for a domain."""
        if not ctx.has("MANAGE_PRESSURE"):
            return JSONResponse({"error": "Forbidden"}, status_code=403)
        body = await request.json()
        from nss.core.pressure import PressureSignal
        sig = PressureSignal(
            signal_type=body.get("signal_type", "epistemic_conflict"),
            value=float(body.get("value", 0.3)),
            weight=float(body.get("weight", 0.2)),
            description=body.get("description", "")
        )
        stab.spf.add_signal(domain, sig)
        spf = stab.spf.compute_spf(domain)
        zone = get_spf_zone(spf)
        receipt_chain.emit("PRESSURE_SIGNAL_ADDED",
                           {"kind": "pressure", "ref": ctx.user_id},
                           {"domain": domain, "signal_type": sig.signal_type},
                           {"spf_after": spf, "zone": zone})
        if zone in (SPFZone.CRITICAL, SPFZone.FRACTURE):
            await bus.broadcast("pressure.zone.change",
                                {"domain": domain, "zone": zone, "spf": spf},
                                min_role="FOUNDER")
        return {"spf": spf, "zone": zone}


    # ── ETHER INGEST ───────────────────────────────────────────────────────────

    @app.post("/ingest/exec")
    async def ingest_exec(req: ExecRequest, request: Request):
        ops_key = request.headers.get("X-NS-OPS-KEY", "")
        _ops_guard(ops_key)

        body = {
            "task_type": "ops_exec_cmd",
            "objective": f"execute governed command through ns authenticated ingest: {req.cmd}",
            "payload": {"cmd": req.cmd},
        }

        r = requests.post("http://handrail:8011/v1/task", json=body, timeout=30)
        try:
            payload = r.json()
        except Exception:
            payload = {
                "ok": r.ok,
                "status_code": r.status_code,
                "raw_text": r.text,
            }
        return JSONResponse(status_code=r.status_code, content=payload)


    @app.post("/ingest/snapshot")
    async def ingest_snapshot(request: Request):
        ops_key = request.headers.get("X-NS-OPS-KEY", "")
        _ops_guard(ops_key)

        body = {
            "task_type": "ops_snapshot",
            "objective": "capture governed snapshot through ns authenticated ingest",
            "payload": {},
        }

        try:
            r = requests.post("http://handrail:8011/v1/task", json=body, timeout=120)
            try:
                payload = r.json()
            except Exception:
                payload = {
                    "ok": r.ok,
                    "status_code": r.status_code,
                    "raw_text": r.text,
                }
            return JSONResponse(status_code=r.status_code, content=payload)
        except req_exc.Timeout as e:
            return JSONResponse(
                status_code=504,
                content={
                    "ok": False,
                    "status_code": 504,
                    "error": "snapshot_bridge_timeout",
                    "detail": str(e),
                },
            )
        except req_exc.RequestException as e:
            return JSONResponse(
                status_code=502,
                content={
                    "ok": False,
                    "status_code": 502,
                    "error": "snapshot_bridge_request_error",
                    "detail": str(e),
                },
            )


    @app.get("/ingest/status")
    async def ingest_status(ctx: AuthContext = Depends(require_auth)):
        stats = ingest.get_stats()
        return stats

    @app.post("/ingest/bootstrap")
    async def ingest_bootstrap(request: Request,
                                ctx: AuthContext = Depends(require_auth)):
        """Bootstrap ingest from an existing directory."""
        body = await request.json()
        directory = body.get("directory", "")
        if not directory:
            return JSONResponse({"error": "directory required"}, status_code=400)
        recursive = body.get("recursive", True)
        results = ingest.bootstrap_directory(
            Path(directory).expanduser(), recursive=recursive
        )
        receipt_chain.emit("ETHER_BOOTSTRAP",
                           {"kind": "ether", "ref": ctx.user_id},
                           {"directory": directory},
                           {"ingested": results.get("ingested", 0),
                            "total": results.get("total", 0)})
        await bus.broadcast("ether.bootstrap.complete",
                            {"directory": directory, "results": {
                                "ingested": results["ingested"],
                                "skipped": results["skipped"],
                                "errors": results["errors"],
                                "total": results["total"]
                            }}, min_role="EXEC")
        return results

    @app.post("/ingest/url")
    async def ingest_url(request: Request,
                          ctx: AuthContext = Depends(require_auth)):
        """Ingest a single URL into ether."""
        body = await request.json()
        url = body.get("url", "")
        if not url:
            return JSONResponse({"error": "url required"}, status_code=400)
        label = body.get("label", "")
        result = await ingest.ingest_url(url, label=label)
        if result.get("ok") and not result.get("skipped"):
            await bus.broadcast("ether.url.ingested",
                                {"url": url, "id": result.get("id")},
                                min_role="EXEC")
        return result

    @app.post("/ingest/crawl")
    async def ingest_crawl(request: Request,
                            ctx: AuthContext = Depends(require_founder)):
        """Crawl from a seed URL. Founder only."""
        body = await request.json()
        seed = body.get("seed_url", "")
        if not seed:
            return JSONResponse({"error": "seed_url required"}, status_code=400)
        depth = min(int(body.get("depth", 2)), 4)  # max depth 4
        domain_limit = body.get("domain_limit", None)
        crawler = get_crawler(receipt_chain=receipt_chain)
        result = await crawler.crawl(seed, depth=depth,
                                     domain_limit=domain_limit, rate_limit=1.0)
        return result

    @app.get("/ingest/search")
    async def ingest_search(q: str, limit: int = 10,
                             ctx: AuthContext = Depends(require_auth)):
        """Full-text search over ingested ether."""
        results = ingest.search(q, limit=limit)
        return {"query": q, "results": results, "count": len(results)}

    @app.post("/ingest/file")
    async def ingest_file_endpoint(request: Request,
                                    ctx: AuthContext = Depends(require_auth)):
        """Ingest a file by path."""
        body = await request.json()
        file_path = body.get("path", "")
        if not file_path:
            return JSONResponse({"error": "path required"}, status_code=400)
        result = ingest.ingest_file(Path(file_path).expanduser())
        return result


    # ── SAN USPTO TERRAIN ─────────────────────────────────────────────────────

    @app.get("/san/status")
    async def san_status(ctx: AuthContext = Depends(require_auth)):
        stats = san.store.get_stats()
        recent = san.store.get_recent_patents(limit=10)
        progress = get_last_progress()
        active = get_active_run()
        return {
            "stats": stats,
            "recent_patents": recent,
            "active_run": active is not None and not active.done(),
            "last_progress": progress[-5:],
        }

    @app.post("/san/hello")
    async def san_hello(ctx: AuthContext = Depends(require_auth)):
        """Quick smoke test — verify pipeline, fetch sample. < 1MB."""
        config = TerrainConfig(mode=TerrainMode.HELLO)
        engine = get_san_engine(config=config, receipt_chain=receipt_chain)
        progress_log = []
        async def _cb(p): progress_log.append(p)
        result = await engine.run(progress_cb=_cb)
        return {"result": result, "progress": progress_log}

    @app.post("/san/terrain")
    async def san_run_terrain(request: Request,
                               ctx: AuthContext = Depends(require_auth)):
        """Run targeted terrain build. Cap-aware, < 500MB."""
        global _active_run
        body = await request.json()
        cpc_codes = body.get("cpc_codes", ["G06F", "G06N"])
        gb_cap = float(body.get("gb_cap", 0.5))
        config = TerrainConfig(
            mode=TerrainMode.TERRAIN,
            target_cpc_codes=cpc_codes,
            gb_cap=gb_cap,
        )
        engine = get_san_engine(config=config, receipt_chain=receipt_chain)

        async def _run():
            progress = get_last_progress()
            async def _cb(p):
                progress.append(p)
                await bus.broadcast("san.terrain.progress", p, min_role="EXEC")
            result = await engine.run(progress_cb=_cb)
            await bus.broadcast("san.terrain.complete", result, min_role="EXEC")
            return result

        import asyncio as _aio
        from nss.jobs.san_uspto import _active_run as _ar
        task = _aio.create_task(_run())
        import nss.jobs.san_uspto as _san_mod
        _san_mod._active_run = task
        return {"status": "started", "mode": "terrain", "cpc_codes": cpc_codes, "gb_cap": gb_cap}

    @app.post("/san/overnight")
    async def san_run_overnight(request: Request,
                                 ctx: AuthContext = Depends(require_founder)):
        """Schedule overnight full terrain build. Founder only."""
        body = await request.json()
        cpc_codes = body.get("cpc_codes", ["G06F", "G06N", "G06Q", "H04L"])
        gb_cap = float(body.get("gb_cap", 5.0))
        config = TerrainConfig(
            mode=TerrainMode.OVERNIGHT,
            target_cpc_codes=cpc_codes,
            gb_cap=gb_cap,
            two_hop_expansion=True,
        )
        engine = get_san_engine(config=config, receipt_chain=receipt_chain)

        async def _run():
            async def _cb(p):
                import nss.jobs.san_uspto as _m
                _m._last_progress.append(p)
                await bus.broadcast("san.terrain.progress", p, min_role="EXEC")
            result = await engine.run(progress_cb=_cb)
            await bus.broadcast("san.terrain.complete", result, min_role="EXEC")
            return result

        import asyncio as _aio
        import nss.jobs.san_uspto as _san_mod
        task = _aio.create_task(_run())
        _san_mod._active_run = task
        return {"status": "started", "mode": "overnight",
                "cpc_codes": cpc_codes, "gb_cap": gb_cap,
                "message": "Overnight terrain build started. Monitor via /san/status."}

    @app.post("/san/cancel")
    async def san_cancel(ctx: AuthContext = Depends(require_founder)):
        """Cancel active terrain run."""
        engine = get_san_engine()
        engine.cancel()
        import nss.jobs.san_uspto as _san_mod
        if _san_mod._active_run and not _san_mod._active_run.done():
            _san_mod._active_run.cancel()
        return {"status": "cancelled"}

    @app.post("/san/novelty")
    async def san_novelty(request: Request,
                           ctx: AuthContext = Depends(require_auth)):
        """Novelty check against terrain corpus."""
        body = await request.json()
        claim_text = body.get("claim_text", "")
        if not claim_text:
            return JSONResponse({"error": "claim_text required"}, status_code=400)
        results = san.novelty_check(claim_text, limit=10)
        return {"results": results, "count": len(results)}

    @app.get("/san/whitespace")
    async def san_whitespace(cpc: str = "G06N",
                              ctx: AuthContext = Depends(require_auth)):
        """White-space analysis for a CPC subtree."""
        result = san.whitespace_query(cpc)
        return result

    @app.get("/san/patents")
    async def san_patents(limit: int = 20,
                           ctx: AuthContext = Depends(require_auth)):
        recent = san.store.get_recent_patents(limit=limit)
        return {"patents": recent, "count": len(recent)}

    @app.get("/san/search")
    async def san_search(q: str, limit: int = 10,
                          ctx: AuthContext = Depends(require_auth)):
        results = san.store.search_patents(q, limit=limit)
        return {"query": q, "results": results, "count": len(results)}


    # ── SAN TERRAIN ────────────────────────────────────────────────────────────

    @app.get("/san/status")
    async def san_status(ctx: AuthContext = Depends(require_auth)):
        return terrain.stats()

    @app.post("/san/novelty")
    async def san_novelty(request: Request,
                           ctx: AuthContext = Depends(require_auth)):
        body = await request.json()
        claim_text = body.get("claim_text", "")
        if not claim_text:
            return JSONResponse({"error": "claim_text required"}, status_code=400)
        cpc_scope = body.get("cpc_scope", None)
        result = terrain.novelty_check(claim_text, cpc_scope=cpc_scope)
        return {
            "query_hash": result.query_claim_hash,
            "collision_risk": result.collision_risk,
            "risk_level": result.risk_level,
            "nearest_neighbors": result.nearest_neighbors[:10],
            "cpc_overlap": result.cpc_overlap,
            "latency_ms": result.query_latency_ms,
        }

    @app.post("/san/whitespace")
    async def san_whitespace(request: Request,
                              ctx: AuthContext = Depends(require_auth)):
        body = await request.json()
        cpc_code = body.get("cpc_code", "")
        if not cpc_code:
            return JSONResponse({"error": "cpc_code required"}, status_code=400)
        result = terrain.whitespace_query(cpc_code,
                    assignee_filter=body.get("assignee_filter"))
        return {
            "cpc_code": result.cpc_code,
            "sparse_regions": result.sparse_regions,
            "under_occupied": result.under_occupied[:10],
            "assignee_pressure": result.assignee_pressure_map,
            "latency_ms": result.query_latency_ms,
        }

    @app.get("/san/competitor/{cpc_code}")
    async def san_competitor(cpc_code: str,
                              ctx: AuthContext = Depends(require_auth)):
        return terrain.competitor_pressure(cpc_code)

    @app.post("/san/snapshot")
    async def san_snapshot(request: Request,
                            ctx: AuthContext = Depends(require_founder)):
        body = await request.json()
        snap = terrain.take_snapshot(
            cpc_scope=body.get("cpc_scope", []),
            tier=body.get("tier", "terrain")
        )
        return asdict(snap) if hasattr(snap, '__dataclass_fields__') else snap.__dict__

    @app.get("/san/ingest/status")
    async def san_ingest_status(ctx: AuthContext = Depends(require_auth)):
        ingest_eng = get_uspto_ingest(terrain_engine=terrain,
                                      receipt_chain=receipt_chain)
        return ingest_eng.status()

    @app.post("/san/ingest/plan")
    async def san_ingest_plan(request: Request,
                               ctx: AuthContext = Depends(require_founder)):
        body = await request.json()
        mode = body.get("mode", "terrain")
        cpc_scope = body.get("cpc_scope", [])
        budget_gb = body.get("budget_gb", None)
        ingest_eng = get_uspto_ingest(terrain_engine=terrain,
                                       receipt_chain=receipt_chain)
        if mode == "terrain":
            run = ingest_eng.plan_terrain_run(cpc_scope=cpc_scope,
                                               budget_gb=budget_gb)
        else:
            year_range = tuple(body.get("year_range", [2020, 2026]))
            run = ingest_eng.plan_deep_run(cpc_scope=cpc_scope,
                                            year_range=year_range,
                                            budget_gb=budget_gb)
        return {
            "run_id": run.run_id,
            "mode": run.mode,
            "job_count": len(run.jobs),
            "estimated_gb": round(sum(j.estimated_bytes for j in run.jobs) / 1e9, 2),
            "jobs": [{"id": j.job_id, "type": j.job_type,
                      "priority": j.priority,
                      "estimated_gb": round(j.estimated_bytes / 1e9, 2),
                      "url_preview": j.url[:80]}
                     for j in run.jobs],
        }

    @app.post("/san/ingest/execute")
    async def san_ingest_execute(request: Request,
                                  ctx: AuthContext = Depends(require_founder)):
        """Start an ingest run. Returns immediately; run executes as background task."""
        body = await request.json()
        mode = body.get("mode", "terrain")
        cpc_scope = body.get("cpc_scope", [])
        budget_gb = body.get("budget_gb", 10.0)  # Safe default: 10GB
        ingest_eng = get_uspto_ingest(terrain_engine=terrain,
                                       receipt_chain=receipt_chain)
        ingest_eng.set_budget(soft_limit_pct=0.80)

        if mode == "terrain":
            run = ingest_eng.plan_terrain_run(cpc_scope=cpc_scope,
                                               budget_gb=budget_gb)
        else:
            run = ingest_eng.plan_deep_run(
                cpc_scope=cpc_scope,
                budget_gb=budget_gb,
                year_range=tuple(body.get("year_range", [2020, 2026]))
            )

        async def _run():
            def on_prog(evt):
                asyncio.create_task(bus.broadcast(
                    "san.ingest.progress", evt, min_role="FOUNDER"))
            await ingest_eng.execute_run(run, on_progress=on_prog)
            await bus.broadcast("san.ingest.complete",
                                {"run_id": run.run_id, "status": run.status,
                                 "patents": run.patents_processed,
                                 "bandwidth_gb": round(run.bandwidth_used_gb, 3)},
                                min_role="FOUNDER")

        asyncio.create_task(_run())
        return {"started": True, "run_id": run.run_id, "mode": mode,
                "job_count": len(run.jobs)}

    @app.post("/san/ingest/budget")
    async def san_set_budget(request: Request,
                              ctx: AuthContext = Depends(require_founder)):
        body = await request.json()
        ingest_eng = get_uspto_ingest(terrain_engine=terrain,
                                       receipt_chain=receipt_chain)
        ingest_eng.set_budget(
            daily_cap_gb=body.get("daily_cap_gb"),
            soft_limit_pct=body.get("soft_limit_pct"),
        )
        return ingest_eng.status()["bandwidth"]

    @app.post("/san/lexicon/anchor")
    async def san_lexicon_anchor(request: Request,
                                  ctx: AuthContext = Depends(require_auth)):
        body = await request.json()
        anchor = terrain.create_lexicon_anchor(
            term_id=body.get("term_id", ""),
            claim_text=body.get("claim_text", ""),
            claim_id=body.get("claim_id", ""),
            pub_id=body.get("pub_id", ""),
            confidence=float(body.get("confidence", 0.8)),
        )
        from dataclasses import asdict
        return asdict(anchor)

    @app.get("/health")
    async def health():
        vh = check_voice_configured()
        return {
            "status": "ok",
            "version": "2.0.0",
            "architecture": "conciliar_v1",
            "storage": storage_health(),
            "voice": {"active": vh["lane_active"], "webhook": vh["webhook_configured"]},
            "alpaca": alpaca.health(),
            "intelligence": {
                "claude": bool(os.environ.get("ANTHROPIC_API_KEY")),
                "gpt4o":  bool(os.environ.get("OPENAI_API_KEY")),
                "gemini": bool(os.environ.get("GOOGLE_API_KEY")),
                "grok":   bool(os.environ.get("GROK_API_KEY")),
            },
            "ether": {
                "ssd_mounted": Path("/Volumes/NSExternal").exists(),
                "polygon":  bool(os.environ.get("POLYGON_API_KEY")),
                "fred":     bool(os.environ.get("FRED_API_KEY")),
                "newsapi":  bool(os.environ.get("NEWSAPI_KEY")),
            },
            "ws_connections": bus.connection_count(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    @app.get("/healthz")
    async def healthz():
        return await health()

    @app.get("/health/full")
    async def health_full():
        """Unified system status — no auth required. Checks all services."""
        import asyncio
        import aiohttp

        async def _get(url: str) -> dict:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=4)) as r:
                        body = await r.json()
                        return {"status": "ok", "code": r.status, "data": body}
            except Exception as e:
                return {"status": "error", "error": str(e)}

        handrail_res, continuum_res = await asyncio.gather(
            _get("http://handrail:8011/healthz"),
            _get("http://continuum:8788/continuum/status"),
        )

        snap_dir = Path("/tmp/alexandria_snapshots")
        ssd_snapshots_dir = Path("/Volumes/NSExternal/ALEXANDRIA/snapshots")
        ssd_ledger = Path("/Volumes/NSExternal/ALEXANDRIA/ledger/ns_receipt_chain.jsonl")
        alexandria = {
            "local_snapshots": len(list(snap_dir.glob("*.json"))) if snap_dir.exists() else 0,
            "ssd_snapshots": len(list(ssd_snapshots_dir.glob("*.json"))) if ssd_snapshots_dir.exists() else 0,
            "ssd_ledger_entries": sum(1 for _ in ssd_ledger.open()) if ssd_ledger.exists() else 0,
            "ssd_mounted": Path("/Volumes/NSExternal/ALEXANDRIA").exists(),
        }

        voice_cfg = check_voice_configured()
        ngrok_url = os.environ.get("NORTHSTAR_WEBHOOK_BASE", "")
        ngrok_live = bool(ngrok_url and "REPLACE" not in ngrok_url and "localhost" not in ngrok_url)

        yubikey_serial = os.environ.get("YUBIKEY_SERIAL", "")

        all_ok = (
            handrail_res["status"] == "ok"
            and continuum_res["status"] == "ok"
            and alexandria["ssd_mounted"]
        )

        return {
            "ok": all_ok,
            "ts": datetime.utcnow().isoformat() + "Z",
            "services": {
                "handrail": {"url": "http://handrail:8011/healthz", **handrail_res},
                "continuum": {"url": "http://continuum:8788/continuum/status", **continuum_res},
                "ns": {"status": "ok", "version": "2.0.0"},
            },
            "alexandria": alexandria,
            "voice": {
                "webhook_configured": voice_cfg.get("webhook_configured", False),
                "ngrok_live": ngrok_live,
                "ngrok_url": ngrok_url,
            },
            "yubikey": {
                "serial_set": bool(yubikey_serial),
                "client_id_set": bool(os.environ.get("YUBIKEY_CLIENT_ID", "")),
            },
        }

    @app.get("/health/voice")
    async def health_voice():
        return check_voice_configured()

    @app.get("/health/alexandria")
    async def health_alexandria():
        ssd = Path("/Volumes/NSExternal")
        return {
            "ssd_mounted": ssd.exists(),
            "path": str(ssd / "ALEXANDRIA") if ssd.exists() else None,
            "ether_active": (ssd / "ALEXANDRIA" / "ether").exists() if ssd.exists() else False,
        }

    @app.get("/alexandria/status")
    async def alexandria_status():
        snap_dir = Path("/tmp/alexandria_snapshots")
        snapshots = list(snap_dir.glob("*.json")) if snap_dir.exists() else []
        ssd_snapshots_dir = Path("/Volumes/NSExternal/ALEXANDRIA/snapshots")
        ssd_ledger_file = Path("/Volumes/NSExternal/ALEXANDRIA/ledger/ns_receipt_chain.jsonl")
        ssd_snaps = list(ssd_snapshots_dir.glob("snapshot_*.json")) if ssd_snapshots_dir.exists() else []
        ssd_ledger_entries = 0
        if ssd_ledger_file.exists():
            with ssd_ledger_file.open() as _f:
                ssd_ledger_entries = sum(1 for line in _f if line.strip())
        total = len(snapshots) + len(ssd_snaps)
        return {
            "ok": total > 0,
            "snapshot_count": total,
            "local_snapshots": len(snapshots),
            "ssd_snapshots": len(ssd_snaps),
            "ssd_snapshots_dir": str(ssd_snapshots_dir),
            "ssd_ledger_entries": ssd_ledger_entries,
            "snapshots_dir": str(snap_dir),
        }

    @app.get("/alexandria/proof")
    async def alexandria_proof(n: int = 50):
        """Compute SHA256 Merkle chain over last N ledger entries. Returns root_hash + chain_length + proof_valid."""
        import hashlib
        ssd_ledger_file = Path("/Volumes/NSExternal/ALEXANDRIA/ledger/ns_receipt_chain.jsonl")
        local_ledger_file = Path("/tmp/ns_alexandria_boot.jsonl")
        ledger_file = ssd_ledger_file if ssd_ledger_file.exists() else local_ledger_file
        if not ledger_file.exists():
            return JSONResponse({"ok": False, "error": "ledger not found", "proof_valid": False}, status_code=404)
        lines = []
        with ledger_file.open() as _f:
            for line in _f:
                line = line.strip()
                if line:
                    lines.append(line)
        entries = lines[-n:] if len(lines) >= n else lines
        chain_hash = "0" * 64
        for entry in entries:
            chain_hash = hashlib.sha256((chain_hash + entry).encode()).hexdigest()
        return {
            "ok": True,
            "root_hash": "sha256:" + chain_hash,
            "chain_length": len(entries),
            "total_entries": len(lines),
            "ledger_source": str(ledger_file),
            "proof_valid": len(entries) > 0,
        }

    @app.get("/health/models")
    async def health_models():
        return {
            "claude": bool(os.environ.get("ANTHROPIC_API_KEY")),
            "gpt4o":  bool(os.environ.get("OPENAI_API_KEY")),
            "gemini": bool(os.environ.get("GOOGLE_API_KEY")),
            "grok":   bool(os.environ.get("GROK_API_KEY")),
        }

    # ═══════════════════════════════════════════════════════════════════════════
    # CHAT
    # ═══════════════════════════════════════════════════════════════════════════

    @app.post("/chat/send")
    async def chat_send(request: Request, ctx: AuthContext = Depends(require_auth)):
        body = await request.json()
        query = body.get("query", "").strip()
        session_id = body.get("session_id", "default")
        if not query:
            return JSONResponse({"error": "query required"}, status_code=400)

        # Route through arbiter
        arb_ctx = {"tier": ctx.role, "session_id": session_id, "user_id": ctx.user_id}
        result = await asyncio.to_thread(arbiter.route, query, arb_ctx)
        response = result.fused_response if result else "Arbiter unavailable."

        # Confidence from disagreement score
        confidence = "draft"
        if result and result.disagreement_score < 0.2:
            confidence = "proposed"

        # Receipt
        msg_id = secrets.token_hex(8)
        receipt = receipt_chain.emit(
            event_type="CHAT_QUERY",
            source={"kind": "console", "ref": ctx.user_id},
            inputs={"query_len": len(query), "session_id": session_id},
            outputs={"response_len": len(response), "confidence": confidence,
                     "message_id": msg_id,
                     "disagreement": result.disagreement_score if result else 0},
        )

        # Broadcast to WS
        msg_obj = {
            "role": "assistant", "content": response,
            "confidence": confidence, "session_id": session_id,
            "message_id": msg_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        await bus.broadcast("chat.message.new", msg_obj)

        return {
            "response": response,
            "confidence": confidence,
            "message_id": msg_id,
            "session_id": session_id,
            "receipt_id": receipt.get("receipt_id"),
            "disagreement_score": result.disagreement_score if result else 0,
        }

    @app.get("/chat/sessions")
    async def chat_sessions(request: Request, ctx: AuthContext = Depends(require_auth)):
        sessions = chat_store.list_sessions(
            user_id=None if ctx.is_founder() else ctx.user_id
        )
        return {"sessions": sessions}

    @app.post("/chat/sessions/new")
    async def chat_new_session(request: Request, ctx: AuthContext = Depends(require_auth)):
        body = await request.json()
        sid = secrets.token_hex(8)
        meta = chat_store.new_session(sid, ctx.user_id, body.get("title", "New Session"))
        return meta

    @app.get("/chat/session/{session_id}")
    async def chat_get_session(session_id: str, request: Request,
                                ctx: AuthContext = Depends(require_auth)):
        msgs = chat_store.get_session(session_id)
        return {"session_id": session_id, "messages": msgs}

    @app.post("/chat/session/{session_id}/rename")
    async def chat_rename(session_id: str, request: Request,
                           ctx: AuthContext = Depends(require_auth)):
        body = await request.json()
        chat_store.rename_session(session_id, body.get("title", ""))
        return {"status": "ok"}

    # ═══════════════════════════════════════════════════════════════════════════
    # RECEIPTS
    # ═══════════════════════════════════════════════════════════════════════════

    @app.get("/receipts")
    async def get_receipts(request: Request,
                            limit: int = 50,
                            lane: Optional[str] = None,
                            ctx: AuthContext = Depends(require_auth)):
        receipts = receipt_chain.recent(limit)
        # Redact for non-founders
        if not ctx.is_founder():
            receipts = [auth.redact_for_role(r, ctx.role) for r in receipts]
        return {"receipts": receipts, "total": len(receipts)}

    @app.get("/receipts/{receipt_id}")
    async def get_receipt(receipt_id: str, request: Request,
                           ctx: AuthContext = Depends(require_auth)):
        receipt = receipt_chain.get(receipt_id)
        if not receipt:
            return JSONResponse({"error": "Not found"}, status_code=404)
        if not ctx.is_founder():
            receipt = auth.redact_for_role(receipt, ctx.role)
        return receipt

    @app.post("/receipts/{receipt_id}/export")
    async def export_receipt(receipt_id: str, request: Request,
                              ctx: AuthContext = Depends(require_founder)):
        receipt = receipt_chain.get(receipt_id)
        if not receipt:
            return JSONResponse({"error": "Not found"}, status_code=404)
        return JSONResponse(receipt)

    # ═══════════════════════════════════════════════════════════════════════════
    # APPROVALS
    # ═══════════════════════════════════════════════════════════════════════════

    @app.get("/approvals/pending")
    async def get_pending_approvals(request: Request,
                                     ctx: AuthContext = Depends(require_auth)):
        approvals = approval_store.pending()
        if not ctx.has("APPROVE_ACTION"):
            return {"approvals": [], "message": "Permission required"}
        return {"approvals": approvals}

    @app.post("/approvals/{approval_id}/approved")
    async def approve_action(approval_id: str, request: Request,
                              ctx: AuthContext = Depends(require_auth)):
        if not ctx.has("APPROVE_ACTION") and not ctx.is_founder():
            return JSONResponse({"error": "Permission denied"}, status_code=403)
        body = await request.json()
        nonce = body.get("nonce", "")
        result = approval_store.resolve(approval_id, ctx.user_id, "approved", nonce)
        if not result:
            return JSONResponse({"error": "Invalid nonce or approval not found"}, status_code=400)
        receipt_chain.emit("APPROVAL_RESOLVED",
                            {"kind": "governance", "ref": ctx.user_id},
                            {"approval_id": approval_id, "nonce_provided": bool(nonce)},
                            {"status": "approved", "resolved_by": ctx.user_id})
        await bus.broadcast("action.status", result)
        return result

    @app.post("/approvals/{approval_id}/denied")
    async def deny_action(approval_id: str, request: Request,
                           ctx: AuthContext = Depends(require_auth)):
        if not ctx.has("APPROVE_ACTION") and not ctx.is_founder():
            return JSONResponse({"error": "Permission denied"}, status_code=403)
        body = await request.json()
        nonce = body.get("nonce", "")
        result = approval_store.resolve(approval_id, ctx.user_id, "denied", nonce)
        if not result:
            return JSONResponse({"error": "Invalid nonce or approval not found"}, status_code=400)
        receipt_chain.emit("APPROVAL_DENIED",
                            {"kind": "governance", "ref": ctx.user_id},
                            {"approval_id": approval_id},
                            {"status": "denied", "resolved_by": ctx.user_id})
        await bus.broadcast("action.status", result)
        return result

    @app.post("/actions/propose")
    async def propose_action(request: Request, ctx: AuthContext = Depends(require_auth)):
        body = await request.json()
        nonce = secrets.token_hex(4).upper()
        phrase = f"CONFIRM-{body.get('action_type','ACTION').upper()}-{nonce}"
        approval = approval_store.create(
            action_summary=body.get("action_summary", ""),
            risk_tier=body.get("risk_tier", "MEDIUM"),
            domain=body.get("domain", "ops"),
            proposed_by=ctx.user_id,
            confirm_phrase=phrase,
            nonce=nonce,
        )
        receipt_chain.emit("ACTION_PROPOSED",
                            {"kind": "action", "ref": ctx.user_id},
                            body, {"approval_id": approval["approval_id"], "nonce": nonce})
        await bus.broadcast("approval.pending", approval, min_role="EXEC")
        return approval

    @app.post("/actions/confirm")
    async def confirm_action(request: Request, ctx: AuthContext = Depends(require_founder)):
        body = await request.json()
        approval_id = body.get("approval_id")
        nonce = body.get("nonce", "")
        result = approval_store.resolve(approval_id, ctx.user_id, "approved", nonce)
        if not result:
            return JSONResponse({"error": "Invalid nonce"}, status_code=400)
        receipt_chain.emit("ACTION_CONFIRMED",
                            {"kind": "governance", "ref": ctx.user_id},
                            {"approval_id": approval_id},
                            {"confirmed_by": ctx.user_id})
        return result

    # ═══════════════════════════════════════════════════════════════════════════
    # VISUALS
    # ═══════════════════════════════════════════════════════════════════════════

    @app.get("/visuals")
    async def get_visuals_list(request: Request,
                                session_id: Optional[str] = None,
                                ctx: AuthContext = Depends(require_auth)):
        if not ctx.has("VIEW_VISUALS"):
            return JSONResponse({"error": "Permission denied"}, status_code=403)
        visuals = visual_store.list_for_session(session_id) if session_id else \
                  list(visual_store._visuals.values())
        return {"visuals": visuals}

    @app.get("/visuals/{visual_id}")
    async def get_visual(visual_id: str, request: Request,
                          ctx: AuthContext = Depends(require_auth)):
        v = visual_store.get(visual_id)
        if not v:
            return JSONResponse({"error": "Not found"}, status_code=404)
        return v

    @app.post("/visuals/{visual_id}/pin_to_chat")
    async def pin_visual(visual_id: str, request: Request,
                          ctx: AuthContext = Depends(require_auth)):
        visual_store.pin(visual_id)
        return {"status": "pinned"}

    @app.post("/visuals/{visual_id}/mark_shareable")
    async def mark_shareable(visual_id: str, request: Request,
                              ctx: AuthContext = Depends(require_founder)):
        visual_store.mark_shareable(visual_id)
        return {"status": "shareable"}

    # ═══════════════════════════════════════════════════════════════════════════
    # VOICE (Twilio + upload)
    # ═══════════════════════════════════════════════════════════════════════════

    @app.get("/voice/health")
    async def voice_health():
        return check_voice_configured()

    @app.post("/voice/inbound")
    async def voice_inbound(request: Request):
        raw = await request.form()
        form = dict(raw)
        call_sid = form.get("CallSid", "unknown")
        caller   = form.get("From", "unknown")
        base     = os.environ.get("NORTHSTAR_WEBHOOK_BASE", "").rstrip("/")
        tier     = TIER_F if caller == os.environ.get("FOUNDER_PHONE", "") else TIER_E
        get_or_create_session(call_sid, caller, os.environ.get("TWILIO_PHONE_NUMBER", ""))
        receipt_chain.emit("VOICE_INBOUND",
                            {"kind": "voice", "ref": call_sid},
                            {"caller": caller, "tier": tier}, {})
        respond_url = f"{base}/voice/respond"
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Gather input="speech" action="{respond_url}" method="POST"
          speechTimeout="auto" timeout="10">
    <Say voice="Polly.Matthew" language="en-US">Northstar online. How can I serve you?</Say>
  </Gather>
  <Redirect method="POST">{respond_url}</Redirect>
</Response>"""
        return Response(content=twiml, media_type="application/xml")

    @app.post("/voice/respond")
    async def voice_respond(request: Request):
        raw = await request.form()
        form = dict(raw)
        call_sid   = form.get("CallSid", "unknown")
        transcript = form.get("SpeechResult", "").strip()
        caller     = form.get("From", "unknown")
        base       = os.environ.get("NORTHSTAR_WEBHOOK_BASE", "").rstrip("/")
        respond_url = f"{base}/voice/respond"

        # Null guard
        session = active_sessions.get(call_sid)
        if not session:
            session = get_or_create_session(
                call_sid, caller, os.environ.get("TWILIO_PHONE_NUMBER", "")
            )

        # No speech — re-prompt and loop
        if not transcript:
            twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Gather input="speech" action="{respond_url}" method="POST"
          speechTimeout="auto" timeout="10">
    <Say voice="Polly.Matthew" language="en-US">I didn't catch that. Go ahead.</Say>
  </Gather>
  <Redirect method="POST">{respond_url}</Redirect>
</Response>"""
            return Response(content=twiml, media_type="application/xml")

        # Call Anthropic directly — sonnet-4-6, voice-optimized
        anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "")
        response_text = "I couldn't reach my intelligence layer right now. Please try again."
        try:
            import anthropic as _anthropic
            client = _anthropic.Anthropic(api_key=anthropic_key)
            ai_resp = await asyncio.to_thread(
                client.messages.create,
                model="claude-sonnet-4-6",
                max_tokens=300,
                system=(
                    "You are NORTHSTAR, a voice AI assistant. "
                    "Respond in 1-3 plain spoken sentences only. "
                    "No markdown, no lists, no bullet points. "
                    "Be concise and direct — this will be spoken aloud."
                ),
                messages=[{"role": "user", "content": transcript}],
            )
            response_text = ai_resp.content[0].text.strip()
        except Exception as exc:
            receipt_chain.emit("VOICE_ERROR", {"kind": "voice", "ref": call_sid},
                               {"error": str(exc)[:200]}, {})

        filtered, _blocked = safe_speak_filter(response_text)
        if _blocked:
            filtered += " Some details were withheld."

        session.add_turn(heard=transcript, spoke=filtered)
        receipt_chain.emit("VOICE_TURN",
                            {"kind": "voice", "ref": call_sid},
                            {"transcript": transcript[:100]},
                            {"response_len": len(filtered), "safespeak": _blocked})

        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Say voice="Polly.Matthew" language="en-US">{filtered}</Say>
  <Gather input="speech" action="{respond_url}" method="POST"
          speechTimeout="auto" timeout="10">
  </Gather>
  <Say voice="Polly.Matthew" language="en-US">I didn't catch that. Go ahead.</Say>
  <Redirect method="POST">{respond_url}</Redirect>
</Response>"""
        return Response(content=twiml, media_type="application/xml")

    @app.post("/voice/transcription")
    async def voice_transcription(request: Request):
        raw = await request.form()
        form = dict(raw)
        call_sid  = form.get("CallSid", "unknown")
        transcript = form.get("SpeechResult", "").strip()

        # Null guard: recreate session if missing (restart / race)
        session = active_sessions.get(call_sid)
        if not session:
            caller  = form.get("From", "unknown")
            session = get_or_create_session(
                call_sid, caller, os.environ.get("TWILIO_PHONE_NUMBER", "")
            )

        if not transcript:
            base = os.environ.get("NORTHSTAR_WEBHOOK_BASE", "")
            return Response(
                content=twiml_respond_for("I didn't catch that. Go ahead.", session),
                media_type="application/xml"
            )

        # Build voice-aware context: tier scope + UX constitution
        arb_ctx = build_arbiter_context(session, transcript)

        # Frame query for voice: short, speakable, no markdown
        voice_query = (
            f"[VOICE CALL | TIER: {session.tier} | "
            f"TURN: {len(session.turns) + 1} | "
            f"Respond in 2-3 plain spoken sentences max. No lists, no markdown.]\n\n"
            f"Caller said: {transcript}"
        )

        try:
            result = await asyncio.to_thread(
                arbiter.route, voice_query, arb_ctx.get("ux_constitution", "")
            )
            response_text = result.fused_response if result else "I couldn't process that request."
        except Exception as exc:
            response_text = "I ran into an issue. Please try again."
            receipt_chain.emit("VOICE_ERROR", {"kind": "voice", "ref": call_sid},
                               {"error": str(exc)[:200]}, {})

        filtered, _blocked = safe_speak_filter(response_text)
        if _blocked:
            filtered += " Some details were withheld for security."

        session.add_turn(heard=transcript, spoke=filtered)

        receipt_chain.emit("VOICE_TURN",
                            {"kind": "voice", "ref": call_sid},
                            {"transcript": transcript[:100]},
                            {"response_len": len(filtered), "safespeak": _blocked})
        return Response(content=twiml_respond_for(filtered, session), media_type="application/xml")

    @app.post("/voice/confirm")
    async def voice_confirm(request: Request):
        raw = await request.form()
        form = dict(raw)
        call_sid = form.get("CallSid", "unknown")
        speech = form.get("SpeechResult", "")
        session = active_sessions.get(call_sid)
        if not session:
            return Response(content=twiml_hangup_for(), media_type="application/xml")
        return Response(
            content=twiml_confirm_for(session, speech),
            media_type="application/xml"
        )

    @app.post("/voice/recording")
    async def voice_recording(request: Request):
        form = dict(await request.form())
        return JSONResponse({"status": "received"})

    @app.post("/voice/status")
    async def voice_status(request: Request):
        form = dict(await request.form())
        call_sid = form.get("CallSid", "unknown")
        status = form.get("CallStatus", "unknown")
        if status in ("completed", "failed", "busy", "no-answer"):
            close_session(call_sid)
        return JSONResponse({"status": "ok"})

    @app.get("/voice/session/{call_id}")
    async def voice_session(call_id: str, request: Request,
                             ctx: AuthContext = Depends(require_auth)):
        session = active_sessions.get(call_id)
        if not session:
            return JSONResponse({"error": "Session not found"}, status_code=404)
        return {"call_sid": call_id, "tier": session.tier, "turns": len(session.turns)}

    @app.get("/voice/sessions")
    async def voice_sessions(request: Request, ctx: AuthContext = Depends(require_auth)):
        ssd_sessions_dir = Path("/Volumes/NSExternal/ALEXANDRIA/sessions")
        persisted_count = len(list(ssd_sessions_dir.glob("*.json"))) if ssd_sessions_dir.exists() else 0
        return {
            "active_sessions": len(active_sessions),
            "persisted_sessions": persisted_count,
            "sessions_dir": str(ssd_sessions_dir),
            "sessions": [{"call_sid": k, "tier": v.tier, "turns": len(v.turns)}
                         for k, v in active_sessions.items()],
        }

    # ── Twilio URL alias (what Twilio console is configured to hit) ────────────
    @app.post("/voice/incoming")
    async def voice_incoming(request: Request):
        """Alias for /voice/inbound — Twilio webhook target."""
        raw = await request.form()
        form = dict(raw)
        call_sid = form.get("CallSid", "unknown")
        caller   = form.get("From", "unknown")
        base     = os.environ.get("NORTHSTAR_WEBHOOK_BASE", "")
        tier     = TIER_F if caller == os.environ.get("FOUNDER_PHONE", "") else TIER_E
        session  = get_or_create_session(call_sid, caller, os.environ.get("TWILIO_PHONE_NUMBER", ""))
        receipt_chain.emit("VOICE_INBOUND",
                           {"kind": "voice", "ref": call_sid},
                           {"caller": caller, "tier": tier}, {})
        return Response(content=twiml_answer_for(session), media_type="application/xml")



    # ═══════════════════════════════════════════════════════════════════════════
    # SMS (Twilio Messaging)
    # ═══════════════════════════════════════════════════════════════════════════

    @app.get("/sms/health")
    async def sms_health():
        return {
            "twilio_sid_set": bool(os.environ.get("TWILIO_ACCOUNT_SID")),
            "twilio_token_set": bool(os.environ.get("TWILIO_AUTH_TOKEN")),
            "phone_number": os.environ.get("TWILIO_PHONE_NUMBER") or "NOT SET",
            "configured_hint": "Set Twilio Messaging webhook to /sms/incoming",
        }

    def _twiml_sms(message: str) -> str:
        # Minimal TwiML for SMS reply
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Message>{message}</Message>
</Response>"""

    @app.post("/sms/incoming")
    async def sms_incoming(request: Request):
        form = dict(await request.form())
        msg_sid = form.get("MessageSid", "unknown")
        from_n  = form.get("From", "unknown")
        body    = (form.get("Body") or "").strip()

        # Receipt (mask numbers in logs)
        def _mask(n: str) -> str:
            n = n or ""
            return (n[:2] + "***" + n[-2:]) if len(n) >= 6 else "***"

        receipt_chain.emit(
            "SMS_INBOUND",
            {"kind": "sms", "ref": msg_sid},
            {"from": _mask(from_n), "len": len(body)},
            {"preview": body[:120]},
        )

        # Route as a short text query (never executes actions; always advisory)
        if not body:
            return Response(content=_twiml_sms("Heard nothing. Send a short message."), media_type="application/xml")

        result = await asyncio.to_thread(arbiter.route, body, {"tier": "TEXT"})
        reply  = (result.fused_response if result else "I couldn't process that.")
        reply, _blocked = safe_speak_filter(reply)
        if _blocked:
            reply = reply + " Some details were withheld for security."

        # Keep SMS tight
        if len(reply) > 1200:
            reply = reply[:1190] + "…"

        receipt_chain.emit(
            "SMS_TURN",
            {"kind": "sms", "ref": msg_sid},
            {"heard": body[:120]},
            {"reply_len": len(reply), "safespeak": _blocked},
        )

        return Response(content=_twiml_sms(reply), media_type="application/xml")

    # ── Conference endpoints ──────────────────────────────────────────────────
    @app.post("/voice/conference/create")
    async def conference_create(request: Request, ctx: AuthContext = Depends(require_founder)):
        """Create a conference room and return join TwiML. FOUNDER only."""
        body = await request.json()
        room  = body.get("room", f"NS-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M')}")
        conf  = get_or_create_conference(room, initiated_by=ctx.user_id)
        base  = os.environ.get("NORTHSTAR_WEBHOOK_BASE", "")
        receipt_chain.emit("CONFERENCE_CREATED",
                           {"kind": "conference", "ref": room},
                           {"room": room, "initiated_by": ctx.user_id}, {})
        return {
            "room": room,
            "join_url": f"{base}/voice/conference/join/{room}",
            "dial_url": f"{base}/voice/conference/dial",
            "status_url": f"{base}/voice/conference/status/{room}",
            "twiml": twiml_conference_join(room),
        }

    @app.post("/voice/conference/join/{room}")
    async def conference_join(room: str, request: Request):
        """Twilio webhook: caller joins named conference room."""
        form = dict(await request.form())
        call_sid = form.get("CallSid", "unknown")
        caller   = form.get("From", "unknown")
        conf = get_or_create_conference(room)
        conf.add_participant(caller, call_sid, role="guest")
        receipt_chain.emit("CONFERENCE_JOINED",
                           {"kind": "conference", "ref": room},
                           {"caller": caller, "call_sid": call_sid}, {})
        return Response(content=twiml_conference_join(room), media_type="application/xml")

    @app.post("/voice/conference/dial")
    async def conference_dial(request: Request, ctx: AuthContext = Depends(require_founder)):
        """Dial a third party into an active conference. FOUNDER only."""
        body = await request.json()
        to_number = body.get("to")
        room      = body.get("room")
        if not to_number or not room:
            return JSONResponse({"error": "to and room required"}, status_code=400)
        try:
            from twilio.rest import Client as TwilioClient
            client = TwilioClient(
                os.environ.get("TWILIO_ACCOUNT_SID"),
                os.environ.get("TWILIO_AUTH_TOKEN")
            )
            base = os.environ.get("NORTHSTAR_WEBHOOK_BASE", "")
            call = client.calls.create(
                to=to_number,
                from_=os.environ.get("TWILIO_PHONE_NUMBER"),
                url=f"{base}/voice/conference/join/{room}",
                status_callback=f"{base}/voice/conference/status/{room}",
            )
            conf = get_or_create_conference(room)
            conf.add_participant(to_number, call.sid, role="third_party")
            receipt_chain.emit("CONFERENCE_DIAL_OUT",
                               {"kind": "conference", "ref": room},
                               {"to": to_number, "call_sid": call.sid}, {})
            return {"status": "dialing", "to": to_number, "call_sid": call.sid, "room": room}
        except Exception as e:
            return JSONResponse({"error": str(e)}, status_code=500)

    @app.post("/voice/conference/ns_speak")
    async def conference_ns_speak(request: Request, ctx: AuthContext = Depends(require_founder)):
        """Inject NS voice into active conference (explicit invite only). FOUNDER only."""
        body = await request.json()
        room = body.get("room")
        text = body.get("text", "")
        if not room or not text:
            return JSONResponse({"error": "room and text required"}, status_code=400)
        conf = get_or_create_conference(room)
        conf.ns_speak(text)
        receipt_chain.emit("CONFERENCE_NS_SPEAK",
                           {"kind": "conference", "ref": room},
                           {"text": text[:100]}, {})
        # Inject via Twilio Modify Participant API (mute=false briefly)
        try:
            from twilio.rest import Client as TwilioClient
            client = TwilioClient(
                os.environ.get("TWILIO_ACCOUNT_SID"),
                os.environ.get("TWILIO_AUTH_TOKEN")
            )
            # Use Twilio Say in conference via outbound call to conference
            base = os.environ.get("NORTHSTAR_WEBHOOK_BASE", "")
            call = client.calls.create(
                to=f"conference:{room}",
                from_=os.environ.get("TWILIO_PHONE_NUMBER"),
                twiml=f'<Response><Say voice="Polly.Matthew">{text}</Say></Response>'
            )
            return {"status": "spoken", "text": text, "room": room}
        except Exception as e:
            return JSONResponse({"error": str(e)}, status_code=500)

    @app.get("/voice/conference/status/{room}")
    async def conference_status(room: str, request: Request,
                                ctx: AuthContext = Depends(require_auth)):
        conf = _conferences.get(room)
        if not conf:
            return JSONResponse({"error": "Conference not found"}, status_code=404)
        return conf.to_receipt()

    @app.get("/voice/conferences")
    async def conferences_list(request: Request, ctx: AuthContext = Depends(require_auth)):
        return {"conferences": active_conferences()}

    @app.post("/voice/say")
    async def voice_say(request: Request, ctx: AuthContext = Depends(require_founder)):
        body = await request.json()
        text = body.get("text", "")
        call_sid = body.get("call_sid", "")
        return {"status": "queued", "text": text, "call_sid": call_sid}

    @app.post("/voice/upload")
    async def voice_upload(request: Request, ctx: AuthContext = Depends(require_auth)):
        """Phase 1 voice: upload audio file, return transcript."""
        from fastapi import UploadFile, File
        form = await request.form()
        audio_file = form.get("audio")
        if not audio_file:
            return JSONResponse({"error": "No audio file"}, status_code=400)
        audio_bytes = await audio_file.read()
        # Store to ether
        ether = get_ether()
        path = ether.store_voice(audio_bytes, ctx.session_id)
        # In Phase 2: call Whisper API. For now return placeholder.
        return {
            "status": "received",
            "path": str(path),
            "transcript": "",  # Phase 2: Whisper ASR here
            "message": "Audio stored. Transcription requires Whisper API (Phase 2).",
        }

    @app.post("/voice/whisper_prompt")
    async def voice_whisper_prompt(request: Request, ctx: AuthContext = Depends(require_auth)):
        if not ctx.has("VOICE_WHISPER"):
            return JSONResponse({"error": "Permission denied"}, status_code=403)
        body = await request.json()
        query = body.get("text", "")
        result = await asyncio.to_thread(arbiter.route, query, {"tier": ctx.role, "mode": "whisper"})
        return {"coaching": result.fused_response if result else "", "mode": "whisper"}

    # ═══════════════════════════════════════════════════════════════════════════
    # CANON (Conciliar)
    # ═══════════════════════════════════════════════════════════════════════════

    @app.post("/canon/propose")
    async def canon_propose(request: Request, ctx: AuthContext = Depends(require_auth)):
        if not ctx.has("PROMOTE_CANON_PROPOSAL"):
            return JSONResponse({"error": "Permission denied"}, status_code=403)
        body = await request.json()
        proposal = canon_store.propose(
            title=body.get("title", ""),
            content=body.get("content", ""),
            proposed_by=ctx.user_id,
            domains_affected=body.get("domains_affected", []),
        )
        receipt_chain.emit("CANON_PROPOSED",
                            {"kind": "canon", "ref": ctx.user_id},
                            {"title": proposal["title"]},
                            {"proposal_id": proposal["proposal_id"]})
        await bus.broadcast("canon.proposal.update", proposal)
        return proposal

    @app.post("/canon/vote")
    async def canon_vote(request: Request, ctx: AuthContext = Depends(require_auth)):
        body = await request.json()
        pid = body.get("proposal_id", "")
        vote = body.get("vote", "")  # support | dissent
        note = body.get("note", "")
        ok = canon_store.vote(pid, ctx.user_id, vote, note)
        if not ok:
            return JSONResponse({"error": "Vote failed"}, status_code=400)
        receipt_chain.emit("CANON_VOTE",
                            {"kind": "canon", "ref": ctx.user_id},
                            {"proposal_id": pid, "vote": vote},
                            {"note_length": len(note)})
        proposal = canon_store._proposals.get(pid, {})
        await bus.broadcast("canon.proposal.update", proposal)
        return {"status": "voted", "vote": vote, "proposal_id": pid}

    @app.get("/canon/proposals")
    async def canon_proposals(request: Request,
                               status: Optional[str] = None,
                               ctx: AuthContext = Depends(require_auth)):
        if not ctx.has("VIEW_CANON_SUMMARY"):
            return JSONResponse({"error": "Permission denied"}, status_code=403)
        proposals = canon_store.list_proposals(status)
        return {"proposals": proposals}

    @app.post("/canon/proposals/{proposal_id}/ratify")
    async def canon_ratify(proposal_id: str, request: Request,
                            ctx: AuthContext = Depends(require_founder)):
        result = canon_store.ratify(proposal_id, ctx.user_id)
        if not result:
            return JSONResponse({"error": "Proposal not found"}, status_code=404)
        receipt_chain.emit("CANON_RATIFIED",
                            {"kind": "canon", "ref": ctx.user_id},
                            {"proposal_id": proposal_id},
                            {"status": "canonical", "ratified_by": ctx.user_id})
        await bus.broadcast("canon.proposal.update", result)
        return result

    @app.post("/canon/proposals/{proposal_id}/expire")
    async def canon_expire(proposal_id: str, request: Request,
                            ctx: AuthContext = Depends(require_founder)):
        result = canon_store.expire(proposal_id)
        if not result:
            return JSONResponse({"error": "Proposal not found"}, status_code=404)
        receipt_chain.emit("CANON_EXPIRED",
                            {"kind": "canon", "ref": ctx.user_id},
                            {"proposal_id": proposal_id}, {"status": "expired"})
        await bus.broadcast("canon.proposal.update", result)
        return result

    # ═══════════════════════════════════════════════════════════════════════════
    # CREDENTIAL MANAGER
    # ═══════════════════════════════════════════════════════════════════════════

    ROTATION_URLS = {
        "ANTHROPIC_API_KEY":  "https://console.anthropic.com/settings/keys",
        "OPENAI_API_KEY":     "https://platform.openai.com/api-keys",
        "GOOGLE_API_KEY":     "https://console.cloud.google.com/apis/credentials",
        "GROK_API_KEY":       "https://console.x.ai/",
        "TWILIO_AUTH_TOKEN":  "https://console.twilio.com/us1/account/manage-account/general",
        "POLYGON_API_KEY":    "https://polygon.io/dashboard/api-keys",
        "FRED_API_KEY":       "https://fredaccount.stlouisfed.org/apikeys",
        "NEWSAPI_KEY":        "https://newsapi.org/account",
        "ALPACA_API_KEY":     "https://app.alpaca.markets/paper/dashboard/overview",
    }
    ENV_PATH_SERVER = Path.home() / "NSS" / ".env"

    @app.get("/credential/status")
    async def credential_status(request: Request, ctx: AuthContext = Depends(require_founder)):
        keys = {}
        for key in ROTATION_URLS.keys():
            val = os.environ.get(key, "")
            keys[key] = {"status": "present" if val else "missing",
                          "masked": val[:8] + "..." + val[-4:] if len(val) > 14 else ("present" if val else "")}
        return {"keys": keys}

    @app.get("/credential/rotate/{key_name}")
    async def credential_rotate_open(key_name: str, request: Request,
                                      ctx: AuthContext = Depends(require_founder)):
        import subprocess
        url = ROTATION_URLS.get(key_name.upper())
        if not url:
            return JSONResponse({"error": f"Unknown key: {key_name}"}, status_code=404)
        subprocess.Popen(["open", url])
        return {"opened": url, "key": key_name.upper()}

    @app.post("/credential/update")
    async def credential_update(request: Request, ctx: AuthContext = Depends(require_founder)):
        import re, subprocess
        body = await request.json()
        key_name = body.get("key", "").upper()
        new_value = body.get("value", "").strip()
        if not key_name or not new_value:
            return JSONResponse({"error": "key and value required"}, status_code=400)
        os.environ[key_name] = new_value
        try:
            if ENV_PATH_SERVER.exists():
                env_text = ENV_PATH_SERVER.read_text()
                pattern = rf"^{key_name}=.*$"
                new_line = f"{key_name}={new_value}"
                if re.search(pattern, env_text, re.MULTILINE):
                    env_text = re.sub(pattern, new_line, env_text, flags=re.MULTILINE)
                else:
                    env_text += f"\n{new_line}"
                ENV_PATH_SERVER.write_text(env_text)
                ENV_PATH_SERVER.chmod(0o600)
            subprocess.run(["security", "add-generic-password",
                            "-a", "northstar", "-s", f"northstar.{key_name.lower()}",
                            "-w", new_value, "-U"], capture_output=True, check=False)
        except Exception as e:
            return JSONResponse({"error": str(e)}, status_code=500)
        receipt_chain.emit("CREDENTIAL_UPDATED",
                            {"kind": "credential_manager", "ref": key_name},
                            {"key": key_name}, {"status": "updated"})
        return {"updated": key_name, "env_written": True, "keychain": True, "live": True}

    @app.get("/credential/rotate-all")
    async def credential_rotate_all(request: Request, ctx: AuthContext = Depends(require_founder)):
        import subprocess
        opened = []
        for key, url in ROTATION_URLS.items():
            if not os.environ.get(key):
                subprocess.Popen(["open", url])
                opened.append({"key": key, "url": url})
        return {"opened_tabs": len(opened), "keys": opened}

    # ═══════════════════════════════════════════════════════════════════════════
    # TRADING
    # ═══════════════════════════════════════════════════════════════════════════

    @app.post("/trade/request")
    async def trade_request(request: Request, ctx: AuthContext = Depends(require_founder)):
        if not ctx.can_access_domain("trading"):
            return JSONResponse({"error": "Trading domain not in allowed_domains"}, status_code=403)
        body = await request.json()
        nonce = secrets.token_hex(4).upper()
        phrase = f"CONFIRM-TRADE-{nonce}"
        approval = approval_store.create(
            action_summary=f"Trade: {body.get('symbol','?')} {body.get('side','?')} {body.get('qty','?')}",
            risk_tier="HIGH",
            domain="trading",
            proposed_by=ctx.user_id,
            confirm_phrase=phrase,
            nonce=nonce,
        )
        receipt_chain.emit("TRADE_PROPOSED",
                            {"kind": "trading", "ref": ctx.user_id},
                            body, {"nonce": nonce, "approval_id": approval["approval_id"]})
        await bus.broadcast("approval.pending", approval, min_role="FOUNDER")
        return {"status": "requires_confirmation", "nonce": nonce,
                "confirm_phrase": phrase, "approval_id": approval["approval_id"]}

    @app.get("/trade/health")
    async def trade_health():
        return alpaca.health()

    # ═══════════════════════════════════════════════════════════════════════════
    # LEXICON / SFE (Socratic Field Engine)
    # ═══════════════════════════════════════════════════════════════════════════

    @app.get("/lexicon/summary")
    async def lexicon_summary(request: Request, ctx: AuthContext = Depends(require_auth)):
        return sfe.lexicon_summary()

    @app.post("/lexicon/concepts/create")
    async def lexicon_create_concept(request: Request,
                                      ctx: AuthContext = Depends(require_auth)):
        body = await request.json()
        concept = sfe.create_concept(
            label=body["label"],
            invariant_core=body["invariant_core"],
            domain_tags=body.get("domain_tags", []),
            created_by=ctx.user_id,
            primitive_mapping=body.get("primitive_mapping", {}),
        )
        return concept

    @app.get("/lexicon/concepts/{concept_id}")
    async def lexicon_get_concept(concept_id: str, request: Request,
                                   ctx: AuthContext = Depends(require_auth)):
        c = sfe.get_concept_with_groundings(concept_id)
        if not c:
            return JSONResponse({"error": "Not found"}, status_code=404)
        return c

    @app.get("/lexicon/concepts")
    async def lexicon_list_concepts(request: Request,
                                     label: Optional[str] = None,
                                     ctx: AuthContext = Depends(require_auth)):
        if label:
            return {"concepts": sfe.find_concept_by_label(label)}
        return {"concepts": list(sfe._concepts.values())}

    @app.post("/lexicon/concepts/{concept_id}/answer")
    async def lexicon_record_answer(concept_id: str, request: Request,
                                     ctx: AuthContext = Depends(require_auth)):
        body = await request.json()
        try:
            qt = QuestionType(body["question_type"])
        except ValueError:
            return JSONResponse({"error": f"Invalid question_type. Valid: {[q.value for q in QuestionType]}"}, status_code=400)
        answer, refusal = sfe.record_answer(
            concept_id=concept_id,
            question_type=qt,
            answer_payload=body["answer_payload"],
            evidence_pack_id=body.get("evidence_pack_id", ""),
            context_id=body.get("context_id", "default"),
            confidence=body.get("confidence", 0.5),
            created_by=ctx.user_id,
        )
        if refusal:
            return JSONResponse(refusal.to_dict(), status_code=422)
        return answer

    @app.get("/lexicon/concepts/{concept_id}/grounding")
    async def lexicon_check_grounding(concept_id: str, request: Request,
                                       ctx: AuthContext = Depends(require_auth)):
        grounded, refusals = sfe.check_grounding(concept_id)
        return {
            "concept_id": concept_id,
            "grounded": grounded,
            "completeness": sfe.evaluate_completeness(concept_id)[0],
            "confidence_tier": sfe.evaluate_completeness(concept_id)[1].value,
            "gaps": [r.to_dict() for r in refusals],
        }

    @app.post("/lexicon/concepts/{concept_id}/boundary")
    async def lexicon_add_boundary(concept_id: str, request: Request,
                                    ctx: AuthContext = Depends(require_auth)):
        body = await request.json()
        boundary = sfe.add_boundary(
            concept_id=concept_id,
            constraint_human=body["constraint_human"],
            constraint_machine=body.get("constraint_machine", ""),
            scope=body.get("scope", []),
            evidence_pack_id=body.get("evidence_pack_id", ""),
            created_by=ctx.user_id,
        )
        return boundary

    @app.post("/lexicon/concepts/{concept_id}/outcome")
    async def lexicon_log_outcome(concept_id: str, request: Request,
                                   ctx: AuthContext = Depends(require_auth)):
        body = await request.json()
        outcome = sfe.log_outcome(
            action_receipt_id=body.get("action_receipt_id", "manual"),
            linked_concept_ids=[concept_id] + body.get("also_concepts", []),
            measured_deltas=body.get("measured_deltas", {}),
            predicted=body.get("predicted"),
            actual=body.get("actual"),
            irreversibility=body.get("irreversibility", "reversible"),
        )
        split = sfe.detect_split_pressure(concept_id)
        return {"outcome": outcome, "split_pressure": split}

    @app.post("/lexicon/concepts/{concept_id}/split")
    async def lexicon_split_concept(concept_id: str, request: Request,
                                     ctx: AuthContext = Depends(require_founder)):
        body = await request.json()
        children = sfe.split_concept(
            parent_id=concept_id,
            child_labels=body["child_labels"],
            split_reason=body["split_reason"],
            evidence_pack_id=body.get("evidence_pack_id", ""),
            created_by=ctx.user_id,
        )
        return {"children": children, "parent_deprecated": True}

    @app.post("/lexicon/terms/upsert")
    async def lexicon_upsert_term(request: Request,
                                   ctx: AuthContext = Depends(require_auth)):
        body = await request.json()
        term = sfe.upsert_term(
            surface_form=body["surface_form"],
            domain_tags=body.get("domain_tags", []),
            usage_coord=body.get("usage_coord", ""),
        )
        return term

    @app.post("/lexicon/translations/create")
    async def lexicon_create_translation(request: Request,
                                          ctx: AuthContext = Depends(require_auth)):
        body = await request.json()
        tm = sfe.create_translation_map(
            source_concept_id=body["source_concept_id"],
            source_domain=body["source_domain"],
            target_concept_id=body["target_concept_id"],
            target_domain=body["target_domain"],
            shared_questions=body.get("shared_questions", []),
            evidence_pack_id=body.get("evidence_pack_id", ""),
        )
        return tm

    @app.get("/lexicon/conflicts")
    async def lexicon_list_conflicts(request: Request,
                                      ctx: AuthContext = Depends(require_auth)):
        return {
            "conflicts": list(sfe._conflicts.values()),
            "open": sum(1 for c in sfe._conflicts.values()
                        if isinstance(c, dict) and c.get("resolution_state") == "open"),
        }

    @app.post("/lexicon/bootstrap")
    async def lexicon_bootstrap(request: Request,
                                 ctx: AuthContext = Depends(require_founder)):
        body = await request.json()
        report = sfe.bootstrap_lexicon_v0(
            corpus_terms=body.get("terms", []),
            domain=body.get("domain", "general"),
        )
        return report

        # ═══════════════════════════════════════════════════════════════════════════
    # LEGACY TEXT QUERY (kept for backward compat)
    # ═══════════════════════════════════════════════════════════════════════════

    @app.post("/query")
    async def query_text(request: Request):
        body = await request.json()
        query = body.get("query", "")
        if not query:
            return JSONResponse({"error": "query required"}, status_code=400)
        result = await asyncio.to_thread(arbiter.route, query, {"tier": "FOUNDER"})
        response = result.fused_response if result else "Arbiter unavailable."
        receipt_chain.emit("QUERY", {"kind": "api", "ref": "legacy"},
                            {"query_len": len(query)}, {"response_len": len(response)})
        return {"response": response}

    # ═══════════════════════════════════════════════════════════════════════════
    # RECEIPT LIST (legacy)
    # ═══════════════════════════════════════════════════════════════════════════

    @app.get("/receipts-legacy")
    async def receipts_legacy():
        receipts = receipt_chain.recent(20)
        return {"receipts": receipts}

    # ═══════════════════════════════════════════════════════════════════════════
    # CONSOLE + DASHBOARD UIs
    # ═══════════════════════════════════════════════════════════════════════════

    @app.get("/console", response_class=HTMLResponse)
    async def console():
        """NS Console — full SPA for iPhone/iPad/Mac Safari."""
        return HTMLResponse(content=CONSOLE_HTML)


    @app.get("/hud", response_class=HTMLResponse)
    async def hud():
        """Call HUD — live view for voice + sms."""
        html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>NS Call HUD</title>
<style>
:root{--bg:#050d1a;--p:#080f1e;--b:#112240;--t:#c8ddf0;--mu:#3a5570;--s:#7090a8;--g:#00e87a;--a:#f0a030;--r:#ff4455;--bl:#4488ff;}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--t);font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:12px;padding:14px}
.h{display:flex;justify-content:space-between;align-items:center;margin-bottom:12px}
.h .t{letter-spacing:4px;color:var(--g);font-weight:700}
.h .sub{color:var(--mu);font-size:10px}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.card{background:var(--p);border:1px solid var(--b);border-radius:6px;padding:12px}
.lbl{color:var(--mu);letter-spacing:3px;font-size:9px;margin-bottom:8px}
.row{display:flex;justify-content:space-between;gap:10px;border-bottom:1px solid rgba(17,34,64,.6);padding:6px 0}
.row:last-child{border-bottom:none}
.k{color:var(--s);min-width:90px}
.v{flex:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.badge{padding:2px 6px;border:1px solid var(--b);border-radius:999px;font-size:9px;color:var(--s)}
.badge.ok{border-color:var(--g);color:var(--g)}
.badge.warn{border-color:var(--a);color:var(--a)}
.small{color:var(--mu);font-size:10px;margin-top:8px;line-height:1.5}
</style>
</head>
<body>
<div class="h">
  <div>
    <div class="t">NS HUD</div>
    <div class="sub">Voice + SMS live view (refreshes every 5s)</div>
  </div>
  <div class="badge" id="st">LOADING</div>
</div>
<div class="grid">
  <div class="card">
    <div class="lbl">VOICE SESSIONS</div>
    <div id="voice"></div>
    <div class="small">Tip: If calls fail, check ngrok URL and Twilio VoiceUrl → /voice/inbound.</div>
  </div>
  <div class="card">
    <div class="lbl">RECENT RECEIPTS</div>
    <div id="rcpt"></div>
    <div class="small">Shows last 15 receipt types. Use /console for full detail.</div>
  </div>
</div>
<script>
async function refresh(){
  try{
    const [v,r,h]=await Promise.all([
      fetch('/voice/sessions').then(x=>x.json()),
      fetch('/receipts-legacy').then(x=>x.json()),
      fetch('/health').then(x=>x.json())
    ]);
    document.getElementById('st').textContent='OK';
    document.getElementById('st').className='badge ok';
    const vs=v.sessions||[];
    const vwrap=document.getElementById('voice');
    vwrap.innerHTML='';
    if(!vs.length){
      vwrap.innerHTML='<div class="row"><div class="k">active</div><div class="v">0</div></div>';
    } else {
      vwrap.innerHTML += `<div class="row"><div class="k">active</div><div class="v">${vs.length}</div></div>`;
      for(const s of vs){
        vwrap.innerHTML += `<div class="row"><div class="k">${s.tier}</div><div class="v">${s.call_sid}</div></div>`;
      }
    }
    const rr=(r.receipts||[]).slice(0,15);
    const rwrap=document.getElementById('rcpt');
    rwrap.innerHTML='';
    for(const it of rr){
      const et=(it.event_type||'').slice(0,40);
      const ref=((it.source||{}).ref||'').slice(0,24);
      rwrap.innerHTML += `<div class="row"><div class="k">${et}</div><div class="v">${ref}</div></div>`;
    }
  } catch(e){
    document.getElementById('st').textContent='WARN';
    document.getElementById('st').className='badge warn';
  }
}
refresh();
setInterval(refresh, 5000);
</script>
</body>
</html>"""
        return HTMLResponse(content=html)

    @app.get("/", response_class=HTMLResponse)
    async def dashboard():
        """NORTHSTAR Dashboard — quick status overview."""
        vh = check_voice_configured()
        llm_keys = {
            "Claude":  bool(os.environ.get("ANTHROPIC_API_KEY")),
            "GPT-4o":  bool(os.environ.get("OPENAI_API_KEY")),
            "Gemini":  bool(os.environ.get("GOOGLE_API_KEY")),
            "Grok":    bool(os.environ.get("GROK_API_KEY")),
        }
        ssd_ok = Path("/Volumes/NSExternal").exists()
        alpaca_health = alpaca.health()
        alpaca_ok = alpaca_health.get("status") == "ok"
        return get_dashboard_html(vh, llm_keys, ssd_ok, alpaca_ok, active_sessions, alpaca)

    return app


app = create_app()


# ── OPS (Handrail internal) ────────────────────────────────────────────────
# Lightweight internal control plane for Handrail -> NS boot orchestration.
# Secured with a shared secret header X-NS-OPS-KEY.

from fastapi import Header

def _ops_guard(x_ns_ops_key: str | None) -> None:
    from fastapi import HTTPException
    import os
    key = os.environ.get("NS_OPS_KEY", "")
    if not key or not x_ns_ops_key or x_ns_ops_key != key:
        raise HTTPException(status_code=401, detail="ops key required")

@app.get("/ops/ingest/status")
async def ops_ingest_status(x_ns_ops_key: str | None = Header(default=None)):
    _ops_guard(x_ns_ops_key)
    return ingest.get_stats()

@app.post("/ops/ingest/bootstrap")
async def ops_ingest_bootstrap(request: Request, x_ns_ops_key: str | None = Header(default=None)):
    _ops_guard(x_ns_ops_key)
    body = await request.json()
    directory = body.get("directory", "")
    if not directory:
        return JSONResponse({"error": "directory required"}, status_code=400)
    recursive = body.get("recursive", True)
    results = ingest.bootstrap_directory(Path(directory).expanduser(), recursive=recursive)
    return {"ok": True, "results": results}
