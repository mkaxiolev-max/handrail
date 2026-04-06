from typing import Optional
from .base import StrictModel


class TwilioInboundRequest(StrictModel):
    """Twilio webhook inbound call fields (form-encoded, mapped to model)."""
    CallSid: Optional[str] = None
    AccountSid: Optional[str] = None
    From: Optional[str] = None
    To: Optional[str] = None
    CallStatus: Optional[str] = None
    Direction: Optional[str] = None
    ForwardedFrom: Optional[str] = None

    model_config = {"extra": "allow"}


class TwilioStatusCallback(StrictModel):
    CallSid: Optional[str] = None
    CallStatus: Optional[str] = None
    Duration: Optional[str] = None
    Timestamp: Optional[str] = None

    model_config = {"extra": "allow"}


class TwiMLResponse(StrictModel):
    twiml: str
    call_sid: Optional[str] = None
