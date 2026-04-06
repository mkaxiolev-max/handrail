from typing import Any, Optional
from datetime import datetime
from .base import StrictModel, utc_now
from .enums import ConferenceState


class ConferenceParticipant(StrictModel):
    participant_id: str
    call_sid: Optional[str] = None
    label: Optional[str] = None
    name: Optional[str] = None
    phone: Optional[str] = None
    role: str = "human"          # human | ns | scribe
    muted: bool = False
    joined_at: datetime = None

    def model_post_init(self, __context):
        if self.joined_at is None:
            object.__setattr__(self, "joined_at", utc_now())


class Conference(StrictModel):
    model_config = {"extra": "allow"}

    conference_id: str
    title: str = ""
    status: str = "init"         # init | active | ended
    ns_role: str = "observer"    # observer | scribe | moderator
    participants: list[ConferenceParticipant] = []
    summary: Optional[str] = None
    actions_extracted: list[str] = []
    created_at: datetime = None
    ended_at: Optional[datetime] = None

    def model_post_init(self, __context):
        if self.created_at is None:
            object.__setattr__(self, "created_at", utc_now())


class CreateConferenceRequest(StrictModel):
    model_config = {"extra": "allow"}
    title: str = "Untitled Conference"
    ns_role: str = "observer"
    participants: list[str] = []


class JoinConferenceRequest(StrictModel):
    call_sid: Optional[str] = None
    label: Optional[str] = None
    name: Optional[str] = None
    role: str = "human"


class ModerateRequest(StrictModel):
    action: str    # mute | summarize | extract_action
    target_participant_id: Optional[str] = None


class SummarizeRequest(StrictModel):
    context: Optional[str] = None
