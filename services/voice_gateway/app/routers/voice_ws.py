"""Voice WebSocket router — live transcript → intent execution stream."""
import json
import logging
import httpx
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from voice_gateway.app.routers.voice_http import _sessions

router = APIRouter(tags=["voice_ws"])
logger = logging.getLogger("voice_gateway.ws")

HANDRAIL_URL = "http://localhost:8011"


@router.websocket("/api/v1/voice/ws/{session_id}")
async def voice_ws(websocket: WebSocket, session_id: str):
    await websocket.accept()
    logger.info(f"[voice_ws] connected: {session_id}")

    session = _sessions.get(session_id)
    if session:
        session.state = "listening"

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
            except Exception:
                await websocket.send_text(json.dumps({"type": "error", "detail": "invalid JSON"}))
                continue

            msg_type = msg.get("type")
            data = msg.get("data", {})

            if msg_type == "transcript_partial":
                # Acknowledge partial — no forwarding
                await websocket.send_text(json.dumps({
                    "type": "transcript_partial_ack",
                    "session_id": session_id,
                }))

            elif msg_type == "transcript_final":
                text = data.get("text", "")
                if session:
                    session.state = "responding"
                    session.transcript_lines += 1

                # Forward to Handrail /intent/execute
                response_text = None
                try:
                    async with httpx.AsyncClient(timeout=15.0) as client:
                        r = await client.post(
                            f"{HANDRAIL_URL}/intent/execute",
                            json={"text": text},
                        )
                        if r.status_code == 200:
                            result = r.json()
                            response_text = result.get("response") or json.dumps(result)
                        else:
                            response_text = f"Handrail returned {r.status_code}"
                except Exception as e:
                    response_text = f"Error reaching Handrail: {e}"

                await websocket.send_text(json.dumps({
                    "type": "response_chunk",
                    "text": response_text,
                    "is_final": True,
                    "session_id": session_id,
                }))

                if session:
                    session.state = "ready"

            elif msg_type == "interrupt":
                prev_state = session.state if session else "unknown"
                if session:
                    session.state = "ready"
                await websocket.send_text(json.dumps({
                    "type": "state_changed",
                    "from": prev_state,
                    "to": "ready",
                    "session_id": session_id,
                }))

            elif msg_type == "mode_change":
                new_mode = data.get("listening_mode")
                if session and new_mode:
                    session.listening_mode = new_mode
                await websocket.send_text(json.dumps({
                    "type": "mode_changed",
                    "listening_mode": new_mode,
                    "session_id": session_id,
                }))

            else:
                await websocket.send_text(json.dumps({
                    "type": "unknown_message_type",
                    "received": msg_type,
                }))

    except WebSocketDisconnect:
        logger.info(f"[voice_ws] disconnected: {session_id}")
        if session:
            session.state = "dormant"
