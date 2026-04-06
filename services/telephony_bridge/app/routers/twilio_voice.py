"""Twilio voice webhook + media stream router."""
import json
import logging
from fastapi import APIRouter, Request, Response, WebSocket, WebSocketDisconnect
from app.config import NGROK_DOMAIN

router = APIRouter(prefix="/api/v1/telephony", tags=["telephony"])
logger = logging.getLogger("telephony_bridge.voice")

# In-memory call state: call_sid → dict
_calls: dict[str, dict] = {}


@router.post("/inbound")
async def inbound(request: Request):
    """Inbound call webhook — validate signature (warn only), return TwiML."""
    form = await request.form()
    call_sid = form.get("CallSid", "unknown")
    caller = form.get("From", "unknown")
    to = form.get("To", "unknown")

    # Validate Twilio signature — log warning if missing, never fail
    sig = request.headers.get("X-Twilio-Signature")
    if not sig:
        logger.warning(f"[inbound] No X-Twilio-Signature on call {call_sid} from {caller}")
    else:
        logger.info(f"[inbound] Signature present for call {call_sid}")

    # Store call state
    _calls[call_sid] = {
        "call_sid": call_sid,
        "caller": caller,
        "to": to,
        "status": "ringing",
        "stream_sid": None,
        "audio_chunks": 0,
    }
    logger.info(f"[inbound] New call: {call_sid} from {caller}")

    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Say voice="Polly.Matthew">Hello, this is Violet. How can I help you?</Say>
  <Connect>
    <Stream url="wss://{NGROK_DOMAIN}/api/v1/telephony/media-stream/{call_sid}"/>
  </Connect>
</Response>"""

    return Response(content=twiml, media_type="application/xml")


@router.websocket("/media-stream/{call_sid}")
async def media_stream(websocket: WebSocket, call_sid: str):
    """Twilio media stream WebSocket handler."""
    await websocket.accept()
    logger.info(f"[media_stream] connected: {call_sid}")

    call = _calls.setdefault(call_sid, {"call_sid": call_sid, "status": "streaming", "audio_chunks": 0})
    call["status"] = "streaming"

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
            except Exception:
                continue

            event = msg.get("event")

            if event == "connected":
                logger.info(f"[media_stream] Twilio connected for {call_sid}")

            elif event == "start":
                stream_sid = msg.get("streamSid", "")
                start = msg.get("start", {})
                call["stream_sid"] = stream_sid
                call["account_sid"] = start.get("accountSid")
                call["call_sid_confirmed"] = start.get("callSid")
                logger.info(f"[media_stream] Stream started: call={call_sid} stream={stream_sid}")

            elif event == "media":
                # Collect base64 mulaw audio payload
                payload = msg.get("media", {}).get("payload", "")
                call["audio_chunks"] = call.get("audio_chunks", 0) + 1
                chunks = call["audio_chunks"]

                # Honest ASR staging contract
                if chunks == 100:
                    logger.info(
                        f"[media_stream] ASR: staged — 100 audio chunks received, "
                        f"ASR pipeline deferred to Phase 2. call={call_sid}"
                    )
                    call["asr_status"] = "staged_phase2"
                elif chunks % 50 == 0:
                    logger.debug(f"[media_stream] {call_sid}: {chunks} chunks accumulated")

            elif event == "stop":
                logger.info(f"[media_stream] Stream stopped: {call_sid} — {call.get('audio_chunks', 0)} chunks received")
                call["status"] = "ended"
                break

    except WebSocketDisconnect:
        logger.info(f"[media_stream] disconnected: {call_sid}")
        call["status"] = "ended"
