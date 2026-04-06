"""Twilio status callback router."""
from fastapi import APIRouter, Request
import logging

router = APIRouter(prefix="/api/v1/telephony", tags=["telephony"])
logger = logging.getLogger("telephony_bridge.status")


@router.post("/status-callback")
async def status_callback(request: Request):
    form = await request.form()
    call_sid = form.get("CallSid", "unknown")
    status = form.get("CallStatus", "unknown")
    duration = form.get("Duration", "0")
    logger.info(f"Call {call_sid} status: {status} duration: {duration}s")
    return {"received": True, "call_sid": call_sid, "status": status}
