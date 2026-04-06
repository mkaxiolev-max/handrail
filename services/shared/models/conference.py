from typing import Optional
from datetime import datetime
from .base import StrictModel, utc_now
from .enums import ConferenceState


class ConferenceParticipant(StrictModel):
    participant_id: str
    name: Optional[str] = None
    phone: Optional[str] = None
    joined_at: datetime = None

    def model_post_init(self, __context):
        if self.joined_at is None:
            object.__setattr__(self, "joined_at", utc_now())


class Conference(StrictModel):
    conference_id: str
    name: str
    state: ConferenceState = ConferenceState.PENDING
    participants: list[ConferenceParticipant] = []
    created_at: datetime = None
    ended_at: Optional[datetime] = None

    def model_post_init(self, __context):
        if self.created_at is None:
            object.__setattr__(self, "created_at", utc_now())


class CreateConferenceRequest(StrictModel):
    name: str
    participants: list[str] = []
