"""Twilio status callback router."""
from fastapi import APIRouter, Request
import logging
from telephony_bridge.app.routers.twilio_voice import _calls

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
