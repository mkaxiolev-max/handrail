"""Twilio voice webhook router."""
from fastapi import APIRouter, Request, Response
from telephony_bridge.app.config import NGROK_DOMAIN

router = APIRouter(prefix="/api/v1/telephony", tags=["telephony"])


@router.post("/inbound")
async def inbound(request: Request):
    """Inbound call webhook — returns TwiML with Polly.Matthew greeting + media stream."""
    form = await request.form()
    call_sid = form.get("CallSid", "unknown")
    caller = form.get("From", "unknown")

    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Say voice="Polly.Matthew" language="en-US">
    Hello. You have reached the NS infinity system. Please hold while I connect you.
  </Say>
  <Connect>
    <Stream url="wss://{NGROK_DOMAIN}/ws/voice/{call_sid}">
      <Parameter name="caller" value="{caller}"/>
    </Stream>
  </Connect>
</Response>"""

    return Response(content=twiml, media_type="application/xml")
