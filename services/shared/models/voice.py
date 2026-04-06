from typing import Any, Optional
from datetime import datetime
from .base import StrictModel, utc_now
from .enums import VoiceMode


class VoiceSessionSettings(StrictModel):
    listening_mode: str = "continuous"          # continuous | push_to_talk | manual
    privacy_mode: str = "local_first"           # local_first | cloud_only
    execution_mode: str = "discuss"             # discuss | execute | silent


class VoiceSession(StrictModel):
    model_config = {"extra": "allow"}

    session_id: str
    channel: str = "desktop"                    # desktop | mobile | telephony
    state: str = "ready"                        # ready | listening | responding | dormant
    caller: Optional[str] = None
    mode: VoiceMode = VoiceMode.ACTIVE
    listening_mode: str = "continuous"
    settings: VoiceSessionSettings = None
    transcript_lines: int = 0
    started_at: datetime = None
    last_activity: datetime = None

    def model_post_init(self, __context):
        now = utc_now()
        if self.started_at is None:
            object.__setattr__(self, "started_at", now)
        if self.last_activity is None:
            object.__setattr__(self, "last_activity", now)
        if self.settings is None:
            object.__setattr__(self, "settings", VoiceSessionSettings())


class VoiceState(StrictModel):
    active_sessions: list[VoiceSession] = []
    active_session: Optional[VoiceSession] = None
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
    model_config = {"extra": "allow"}
    channel: str = "desktop"
    caller: Optional[str] = None
    mode: VoiceMode = VoiceMode.ACTIVE
    settings: Optional[VoiceSessionSettings] = None


class ModeChangeRequest(StrictModel):
    model_config = {"extra": "allow"}
    listening_mode: Optional[str] = None
    mode: Optional[VoiceMode] = None


class UpdateSettingsRequest(StrictModel):
    model_config = {"extra": "allow"}
    listening_mode: Optional[str] = None
    privacy_mode: Optional[str] = None
    execution_mode: Optional[str] = None


class MuteRequest(StrictModel):
    muted: bool
