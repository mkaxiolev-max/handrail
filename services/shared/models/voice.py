from typing import Optional
from datetime import datetime
from .base import StrictModel, utc_now
from .enums import VoiceMode


class VoiceSession(StrictModel):
    session_id: str
    caller: Optional[str] = None
    mode: VoiceMode = VoiceMode.ACTIVE
    active: bool = True
    transcript_lines: int = 0
    started_at: datetime = None
    last_activity: datetime = None

    def model_post_init(self, __context):
        now = utc_now()
        if self.started_at is None:
            object.__setattr__(self, "started_at", now)
        if self.last_activity is None:
            object.__setattr__(self, "last_activity", now)


class VoiceState(StrictModel):
    active_sessions: list[VoiceSession] = []
    mode: VoiceMode = VoiceMode.ACTIVE
    muted: bool = False
    webhook_configured: bool = False
    ngrok_domain: Optional[str] = None


class VoiceSettings(StrictModel):
    mode: VoiceMode = VoiceMode.ACTIVE
    greeting_enabled: bool = True
    memory_context_enabled: bool = True
    proactive_intel_enabled: bool = True


class CreateSessionRequest(StrictModel):
    caller: Optional[str] = None
    mode: VoiceMode = VoiceMode.ACTIVE


class ModeChangeRequest(StrictModel):
    mode: VoiceMode


class MuteRequest(StrictModel):
    muted: bool
