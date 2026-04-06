"""Voice HTTP router — /api/v1/voice/*"""
from fastapi import APIRouter
from shared.models.voice import VoiceState, VoiceSession, CreateSessionRequest, ModeChangeRequest, MuteRequest
from shared.models.enums import VoiceMode
import uuid

router = APIRouter(prefix="/api/v1/voice", tags=["voice"])

_sessions: dict[str, VoiceSession] = {}
_state = VoiceState(
    mode=VoiceMode.ACTIVE,
    muted=False,
    webhook_configured=True,
    ngrok_domain="monica-problockade-caylee.ngrok-free.dev",
)


@router.get("/state", response_model=VoiceState)
async def get_state():
    _state.active_sessions = list(_sessions.values())
    return _state


@router.post("/sessions", response_model=VoiceSession)
async def create_session(request: CreateSessionRequest):
    session = VoiceSession(
        session_id=f"vsess_{uuid.uuid4().hex[:12]}",
        caller=request.caller,
        mode=request.mode,
    )
    _sessions[session.session_id] = session
    return session


@router.post("/mode")
async def set_mode(request: ModeChangeRequest):
    _state.mode = request.mode
    return {"mode": _state.mode}


@router.get("/settings")
async def get_settings():
    from voice_gateway.app.config import NGROK_DOMAIN, NS_URL
    return {
        "mode": _state.mode,
        "muted": _state.muted,
        "ngrok_domain": NGROK_DOMAIN,
        "ns_url": NS_URL,
        "greeting_enabled": True,
        "memory_context_enabled": True,
    }


@router.post("/mute")
async def mute(request: MuteRequest):
    _state.muted = request.muted
    return {"muted": _state.muted}
