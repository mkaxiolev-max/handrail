"""Conference HTTP router."""
import uuid
from fastapi import APIRouter, HTTPException
from shared.models.conference import Conference, CreateConferenceRequest, ConferenceParticipant
from shared.models.enums import ConferenceState

router = APIRouter(prefix="/api/v1/conference", tags=["conference"])

_conferences: dict[str, Conference] = {}


@router.post("/create", response_model=Conference)
async def create_conference(request: CreateConferenceRequest):
    conference_id = f"conf_{uuid.uuid4().hex[:12]}"
    participants = [
        ConferenceParticipant(participant_id=f"part_{uuid.uuid4().hex[:8]}", phone=p)
        for p in request.participants
    ]
    conf = Conference(
        conference_id=conference_id,
        name=request.name,
        state=ConferenceState.PENDING,
        participants=participants,
    )
    _conferences[conference_id] = conf
    return conf


@router.get("/{conference_id}/state", response_model=Conference)
async def get_conference_state(conference_id: str):
    conf = _conferences.get(conference_id)
    if not conf:
        raise HTTPException(status_code=404, detail=f"Conference {conference_id} not found")
    return conf
