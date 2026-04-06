"""Conference HTTP router — full Phase 7 implementation."""
import uuid
import httpx
import logging
from fastapi import APIRouter, HTTPException
from shared.models.conference import (
    Conference, CreateConferenceRequest, ConferenceParticipant,
    JoinConferenceRequest, ModerateRequest, SummarizeRequest,
)

router = APIRouter(prefix="/api/v1/conference", tags=["conference"])
logger = logging.getLogger("conference_orchestrator.http")

_conferences: dict[str, Conference] = {}

NS_URL = "http://localhost:9000"


def _get_or_404(conference_id: str) -> Conference:
    conf = _conferences.get(conference_id)
    if not conf:
        raise HTTPException(status_code=404, detail=f"Conference {conference_id} not found")
    return conf


@router.post("/create", response_model=Conference)
async def create_conference(request: CreateConferenceRequest):
    conference_id = f"conf_{uuid.uuid4().hex[:12]}"
    conf = Conference(
        conference_id=conference_id,
        title=request.title,
        status="init",
        ns_role=request.ns_role,
        participants=[],
    )
    _conferences[conference_id] = conf
    logger.info(f"[create] {conference_id} ns_role={request.ns_role}")
    return conf


@router.post("/{conference_id}/join", response_model=Conference)
async def join_conference(conference_id: str, request: JoinConferenceRequest):
    conf = _get_or_404(conference_id)
    participant = ConferenceParticipant(
        participant_id=f"part_{uuid.uuid4().hex[:8]}",
        call_sid=request.call_sid,
        label=request.label,
        name=request.name,
        role=request.role,
    )
    conf.participants.append(participant)
    conf.status = "active"
    logger.info(f"[join] {conference_id} participant={participant.participant_id} role={request.role}")
    return conf


@router.get("/{conference_id}/state", response_model=Conference)
async def get_conference_state(conference_id: str):
    return _get_or_404(conference_id)


@router.post("/{conference_id}/moderate")
async def moderate(conference_id: str, request: ModerateRequest):
    conf = _get_or_404(conference_id)
    result = {"action": request.action, "conference_id": conference_id}

    if request.action == "mute":
        target = next(
            (p for p in conf.participants if p.participant_id == request.target_participant_id),
            None,
        )
        if target:
            target.muted = True
            result["target"] = request.target_participant_id
            result["muted"] = True
        else:
            raise HTTPException(status_code=404, detail=f"Participant {request.target_participant_id} not found")

    elif request.action == "summarize":
        result["summary"] = conf.summary or "No summary yet — call /summarize"

    elif request.action == "extract_action":
        result["actions"] = conf.actions_extracted

    logger.info(f"[moderate] {conference_id} action={request.action}")
    return result


@router.post("/{conference_id}/summarize")
async def summarize(conference_id: str, request: SummarizeRequest = None):
    conf = _get_or_404(conference_id)
    participants_str = ", ".join(
        p.name or p.label or p.participant_id for p in conf.participants
    ) or "no participants"

    # Call NS for summary
    summary_text = None
    actions = []
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.post(
                f"{NS_URL}/intel/suggest",
                json={
                    "topic": f"conference summary for {conf.title}",
                    "context": f"Participants: {participants_str}. Status: {conf.status}. {request.context if request else ''}",
                },
            )
            if r.status_code == 200:
                data = r.json()
                suggestions = data.get("suggestions", [])
                summary_text = suggestions[0] if suggestions else f"Conference '{conf.title}' with {participants_str}"
    except Exception as e:
        logger.warning(f"[summarize] NS unreachable: {e}")
        summary_text = f"Conference '{conf.title}' — {len(conf.participants)} participants ({participants_str})"

    conf.summary = summary_text
    conf.actions_extracted = actions
    logger.info(f"[summarize] {conference_id}")
    return {"summary": summary_text, "actions_extracted": actions}


@router.post("/{conference_id}/sidecar-mode", response_model=Conference)
async def sidecar_mode(conference_id: str):
    conf = _get_or_404(conference_id)
    conf.ns_role = "scribe"
    logger.info(f"[sidecar_mode] {conference_id} ns_role=scribe")
    return conf
