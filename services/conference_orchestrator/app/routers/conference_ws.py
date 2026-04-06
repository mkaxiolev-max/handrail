"""Conference WebSocket router — live event stream."""
import json
import asyncio
import logging
from datetime import timezone, datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from conference_orchestrator.app.routers.conference_http import _conferences

router = APIRouter(tags=["conference_ws"])
logger = logging.getLogger("conference_orchestrator.ws")

PING_INTERVAL = 30  # seconds


@router.websocket("/api/v1/conference/ws/{conference_id}/events")
async def conference_events(websocket: WebSocket, conference_id: str):
    await websocket.accept()
    logger.info(f"[conference_ws] connected: {conference_id}")

    conf = _conferences.get(conference_id)

    # Send initial state event
    await websocket.send_text(json.dumps({
        "event_type": "conference.state",
        "payload": conf.model_dump(mode="json") if conf else {"conference_id": conference_id, "status": "not_found"},
    }, default=str))

    # Ping loop + listen for disconnect
    ping_task = None

    async def ping_loop():
        while True:
            await asyncio.sleep(PING_INTERVAL)
            try:
                await websocket.send_text(json.dumps({
                    "event_type": "ping",
                    "payload": {"ts": datetime.now(timezone.utc).isoformat()},
                }))
            except Exception:
                break

    ping_task = asyncio.create_task(ping_loop())

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
            except Exception:
                continue
            # Re-broadcast conference state on any client message
            conf = _conferences.get(conference_id)
            await websocket.send_text(json.dumps({
                "event_type": "conference.state",
                "payload": conf.model_dump(mode="json") if conf else {"conference_id": conference_id},
            }, default=str))
    except WebSocketDisconnect:
        logger.info(f"[conference_ws] disconnected: {conference_id}")
    finally:
        if ping_task:
            ping_task.cancel()
