"""Voice HTTP router — /api/v1/voice/*"""
import uuid
from fastapi import APIRouter, HTTPException
from shared.models.voice import (
    VoiceState, VoiceSession, VoiceSessionSettings,
    CreateSessionRequest, ModeChangeRequest, UpdateSettingsRequest, MuteRequest,
)
from shared.models.enums import VoiceMode

router = APIRouter(prefix="/api/v1/voice", tags=["voice"])

# In-memory session store: session_id → VoiceSession
_sessions: dict[str, VoiceSession] = {}
_active_session_id: str | None = None


def _active_session() -> VoiceSession | None:
    return _sessions.get(_active_session_id) if _active_session_id else None


@router.get("/state")
async def get_state():
    active = _active_session()
    return {
        "active_session": active.model_dump(mode="json") if active else None,
        "active_sessions": [s.model_dump(mode="json") for s in _sessions.values()],
        "total_sessions": len(_sessions),
        "webhook_configured": True,
        "ngrok_domain": "monica-problockade-caylee.ngrok-free.dev",
    }


@router.post("/sessions", response_model=VoiceSession)
async def create_session(request: CreateSessionRequest):
    global _active_session_id
    session_id = f"vsess_{uuid.uuid4().hex[:12]}"
    settings = request.settings or VoiceSessionSettings()
    session = VoiceSession(
        session_id=session_id,
        channel=request.channel,
        state="ready",
        caller=request.caller,
        mode=request.mode or VoiceMode.ACTIVE,
        listening_mode=settings.listening_mode,
        settings=settings,
    )
    _sessions[session_id] = session
    _active_session_id = session_id
    return session


@router.post("/mode")
async def set_mode(request: ModeChangeRequest):
    active = _active_session()
    if active and request.listening_mode:
        active.listening_mode = request.listening_mode
        if active.settings:
            active.settings.listening_mode = request.listening_mode
    if active and request.mode:
        active.mode = request.mode
    return {
        "mode": active.mode if active else None,
        "listening_mode": active.listening_mode if active else None,
    }


@router.post("/settings")
async def update_settings(request: UpdateSettingsRequest):
    active = _active_session()
    if not active:
        raise HTTPException(status_code=404, detail="No active session")
    if active.settings is None:
        active.settings = VoiceSessionSettings()
    if request.listening_mode is not None:
        active.settings.listening_mode = request.listening_mode
        active.listening_mode = request.listening_mode
    if request.privacy_mode is not None:
        active.settings.privacy_mode = request.privacy_mode
    if request.execution_mode is not None:
        active.settings.execution_mode = request.execution_mode
    return active.model_dump(mode="json")


@router.post("/mute")
async def mute(request: MuteRequest):
    return {"muted": request.muted}


@router.post("/{session_id}/interrupt", response_model=VoiceSession)
async def interrupt(session_id: str):
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    session.state = "ready"
    return session


@router.delete("/{session_id}")
async def delete_session(session_id: str):
    global _active_session_id
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    del _sessions[session_id]
    if _active_session_id == session_id:
        _active_session_id = next(iter(_sessions), None)
    return {"deleted": True, "session_id": session_id}
