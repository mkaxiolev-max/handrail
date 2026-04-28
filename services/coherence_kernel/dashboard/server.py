"""NCOM — Non-Classical Observer Monitor FastAPI server (port 9020).

Panels: 8 read-only data sources + WebSocket live push.
"""
from __future__ import annotations
import asyncio, json
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from services.coherence_kernel.dashboard.panels import PANEL_HANDLERS

app = FastAPI(title="NCOM Dashboard", version="1.0.0")

_SPA = Path(__file__).parent / "spa" / "index.html"

_subscribers: list[WebSocket] = []


@app.get("/", response_class=HTMLResponse)
async def spa_root():
    if _SPA.exists():
        return HTMLResponse(_SPA.read_text())
    return HTMLResponse("<h1>NCOM</h1><p>SPA not found at spa/index.html</p>")


@app.get("/ncom/healthz")
async def healthz():
    return {"ok": True, "service": "ncom"}


@app.get("/ncom/panels")
async def list_panels():
    return {"panels": list(PANEL_HANDLERS.keys())}


@app.get("/ncom/panels/{panel_id}")
async def get_panel(panel_id: str):
    handler = PANEL_HANDLERS.get(panel_id)
    if not handler:
        raise HTTPException(status_code=404, detail=f"unknown panel: {panel_id!r}")
    try:
        data = handler()
        return JSONResponse(content=data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ncom/ws")
async def ws_endpoint(websocket: WebSocket):
    await websocket.accept()
    _subscribers.append(websocket)
    try:
        while True:
            # Push all 8 panels every 5 seconds; also respond to ping
            await asyncio.sleep(5)
            payload = {}
            for panel_id, handler in PANEL_HANDLERS.items():
                try:
                    payload[panel_id] = handler()
                except Exception as e:
                    payload[panel_id] = {"error": str(e)}
            await websocket.send_text(json.dumps(payload))
    except WebSocketDisconnect:
        _subscribers.remove(websocket)
    except Exception:
        if websocket in _subscribers:
            _subscribers.remove(websocket)
