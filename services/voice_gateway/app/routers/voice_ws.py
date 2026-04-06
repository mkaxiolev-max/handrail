"""Voice WebSocket router stub."""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter(tags=["voice_ws"])


@router.websocket("/ws/voice/{session_id}")
async def voice_ws(websocket: WebSocket, session_id: str):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f'{{"echo": "{data}", "session_id": "{session_id}"}}')
    except WebSocketDisconnect:
        pass
