"""Conference WebSocket router stub."""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter(tags=["conference_ws"])


@router.websocket("/ws/conference/{conference_id}")
async def conference_ws(websocket: WebSocket, conference_id: str):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f'{{"echo": "{data}", "conference_id": "{conference_id}"}}')
    except WebSocketDisconnect:
        pass
