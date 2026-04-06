"""Twilio status callback + voice status contract router."""
import os
from fastapi import APIRouter, Request
import logging
from app.routers.twilio_voice import _calls
from app.config import NGROK_DOMAIN

router = APIRouter(prefix="/api/v1/telephony", tags=["telephony"])
logger = logging.getLogger("telephony_bridge.status")


@router.post("/status-callback")
async def status_callback(request: Request):
    form = await request.form()
    call_sid = form.get("CallSid", "unknown")
    status = form.get("CallStatus", "unknown")
    duration = form.get("Duration", "0")
    direction = form.get("Direction", "unknown")
    error_code = form.get("ErrorCode")
    error_msg = form.get("ErrorMessage")

    # Update call state
    if call_sid in _calls:
        prev = _calls[call_sid].get("status", "unknown")
        _calls[call_sid]["status"] = status
        _calls[call_sid]["duration"] = duration
        logger.info(f"[status] {call_sid}: {prev} → {status} (duration={duration}s direction={direction})")
    else:
        logger.warning(f"[status] unknown call_sid {call_sid} → {status}")

    if error_code:
        logger.error(f"[status] {call_sid} error {error_code}: {error_msg}")

    return {
        "received": True,
        "call_sid": call_sid,
        "status": status,
        "duration": duration,
    }


@router.get("/voice-status")
async def voice_status():
    """Honest voice staging contract — what works vs what is staged."""
    return {
        "voice_completeness": "staged",
        "what_works": [
            "inbound_call",
            "polly_greeting",
            "twilio_media_stream",
            "audio_accumulation",
            "status_callbacks",
        ],
        "what_is_staged": [
            "speech_to_text",
            "intent_routing_from_voice",
            "tts_response_return",
            "barge_in",
        ],
        "voice_phase": "Phase 1 complete — ASR pipeline is Phase 2",
        "twilio_number": os.environ.get("TWILIO_PHONE_NUMBER", "+13072024418"),
        "ngrok_domain": NGROK_DOMAIN,
        "active_calls": len([c for c in _calls.values() if c.get("status") == "streaming"]),
        "total_calls_seen": len(_calls),
    }
