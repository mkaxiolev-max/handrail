"""Black Knight voice intake — escalates voice-triggered challenges to the IMO chamber.

Wires: NS voice session → challenge keyword detection → IMO adjudication → NCOM escalation.
"""
from __future__ import annotations
import re
from services.coherence_kernel import schemas
from services.coherence_kernel.imo import gate

_CHALLENGE_PATTERN = re.compile(
    r"\b(black\s+knight|arm\s+imo|collapse\s+challenge|gate\s+review)\b",
    re.IGNORECASE,
)


def parse_voice_challenge(transcript: str, branch: schemas.BranchState) -> dict:
    """Detect a Black Knight challenge in transcript; return escalation packet.

    Returns:
        {
          "escalated": bool,
          "proposal_id": str | None,
          "trigger_phrase": str | None,
        }
    """
    match = _CHALLENGE_PATTERN.search(transcript)
    if not match:
        return {"escalated": False, "proposal_id": None, "trigger_phrase": None}

    proposal_id = gate.propose(branch)
    return {
        "escalated": True,
        "proposal_id": proposal_id,
        "trigger_phrase": match.group(0),
    }


def run_voice_adjudication(proposal_id: str) -> schemas.PointerStatePromotion:
    """Execute adjudication for a voice-escalated proposal."""
    return gate.adjudicate(proposal_id)
