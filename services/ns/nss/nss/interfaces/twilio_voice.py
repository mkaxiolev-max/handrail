"""
NORTHSTAR Twilio Voice Interface
Step 3 per MVP spec: accept calls, record, transcribe, classify, route to Loom, speak back.

Endpoints:
  POST /twilio/voice     - answer inbound call
  POST /twilio/recording - recording callback (audio available)
  POST /twilio/status    - call status updates
  POST /twilio/conference - conference call support
"""

import os
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# Twilio TwiML response builder
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN", "")
TWILIO_PHONE_NUMBER = os.environ.get("TWILIO_PHONE_NUMBER", "")
NORTHSTAR_WEBHOOK_BASE = os.environ.get("NORTHSTAR_WEBHOOK_BASE", "https://your-ngrok-url.ngrok.io")


def twiml_answer(gather_action: str) -> str:
    """
    TwiML to answer a call and gather speech input.
    """
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Gather input="speech"
            action="{gather_action}"
            method="POST"
            timeout="5"
            speechTimeout="auto">
        <Say voice="Polly.Matthew" language="en-US">
            North Star online. How can I serve you?
        </Say>
    </Gather>
    <Say voice="Polly.Matthew" language="en-US">
        I did not catch that. Please try again.
    </Say>
    <Redirect method="POST">{gather_action.rsplit("/voice/transcription",1)[0]}/voice/incoming</Redirect>
</Response>"""


def twiml_respond(message: str, gather_action: Optional[str] = None) -> str:
    """
    TwiML to speak a response back to the caller.
    Optionally continue gathering input.
    """
    gather_block = ""
    if gather_action:
        gather_block = f"""
    <Gather input="speech" action="{gather_action}" method="POST" timeout="5" speechTimeout="auto">
        recordingStatusCallback="{NORTHSTAR_WEBHOOK_BASE}/twilio/recording"
        maxLength="120"
        timeout="5"
        </Gather>"""

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Matthew" language="en-US">{message}</Say>{gather_block}
</Response>"""




def twiml_hangup(farewell: str = "NORTHSTAR standing by.") -> str:
    """TwiML to say farewell and hang up."""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Matthew" language="en-US">{farewell}</Say>
    <Hangup/>
</Response>"""
def twiml_conference(room_name: str = "NORTHSTAR", moderator_pin: str = "0000") -> str:
    """TwiML for conference call."""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Matthew">Joining North Star conference.</Say>
    <Dial>
        <Conference
            startConferenceOnEnter="true"
            endConferenceOnExit="false"
            record="record-from-start"
            recordingStatusCallback="{NORTHSTAR_WEBHOOK_BASE}/twilio/recording"
        >{room_name}</Conference>
    </Dial>
</Response>"""


def parse_twilio_form(body: bytes) -> dict:
    """Parse URL-encoded Twilio webhook body."""
    from urllib.parse import parse_qs
    parsed = parse_qs(body.decode())
    return {k: v[0] if len(v) == 1 else v for k, v in parsed.items()}


class VoiceSession:
    """
    Tracks a single inbound voice call through its lifecycle.
    """

    def __init__(self, call_sid: str):
        self.call_sid = call_sid
        self.started_at = datetime.now(timezone.utc).isoformat()
        self.transcripts = []
        self.responses = []
        self.recording_urls = []
        self.status = "active"

    def add_transcript(self, text: str):
        self.transcripts.append({
            "text": text,
            "ts": datetime.now(timezone.utc).isoformat()
        })

    def add_response(self, text: str):
        self.responses.append({
            "text": text,
            "ts": datetime.now(timezone.utc).isoformat()
        })

    def add_recording(self, url: str):
        self.recording_urls.append(url)

    def to_receipt_source(self) -> dict:
        return {
            "kind": "twilio_voice",
            "ref": self.call_sid,
            "started_at": self.started_at,
            "transcript_count": len(self.transcripts),
        }

    def to_dict(self) -> dict:
        return {
            "call_sid": self.call_sid,
            "started_at": self.started_at,
            "status": self.status,
            "transcripts": self.transcripts,
            "responses": self.responses,
            "recording_urls": self.recording_urls,
        }


# In-memory session store (bootstrapped; persisted to ether on close)
_sessions: dict = {}


def get_or_create_session(call_sid: str) -> VoiceSession:
    if call_sid not in _sessions:
        _sessions[call_sid] = VoiceSession(call_sid)
    return _sessions[call_sid]


def close_session(call_sid: str) -> Optional[VoiceSession]:
    session = _sessions.pop(call_sid, None)
    if session:
        session.status = "completed"
    return session


def active_sessions() -> list:
    return [s.to_dict() for s in _sessions.values()]


def check_twilio_configured() -> dict:
    return {
        "account_sid_set": bool(TWILIO_ACCOUNT_SID),
        "auth_token_set": bool(TWILIO_AUTH_TOKEN),
        "phone_number_set": bool(TWILIO_PHONE_NUMBER),
        "webhook_base_set": "ngrok" not in NORTHSTAR_WEBHOOK_BASE,
        "ready": bool(TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN and TWILIO_PHONE_NUMBER),
    }


# ─── Conference Bridge ────────────────────────────────────────────────────────

def twiml_conference_join(room_name: str, record: bool = True) -> str:
    """TwiML to join a named conference room as a participant."""
    record_attr = 'record-from-start' if record else 'do-not-record'
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Dial>
        <Conference
            startConferenceOnEnter="true"
            endConferenceOnExit="false"
            record="{record_attr}"
            recordingStatusCallback="{NORTHSTAR_WEBHOOK_BASE}/voice/recording"
            waitUrl="http://twimlets.com/holdmusic?Bucket=com.twilio.music.ambient"
            beep="false"
        >{room_name}</Conference>
    </Dial>
</Response>"""


def twiml_conference_moderator(room_name: str) -> str:
    """TwiML for NS as silent moderator — joins but does not announce."""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Dial>
        <Conference
            startConferenceOnEnter="true"
            endConferenceOnExit="false"
            record="record-from-start"
            recordingStatusCallback="{NORTHSTAR_WEBHOOK_BASE}/voice/recording"
            transcribe="true"
            beep="false"
            muted="false"
        >{room_name}</Conference>
    </Dial>
</Response>"""


def twiml_dial_out(to_number: str, conference_room: str) -> str:
    """TwiML to dial a third party into an existing conference."""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Dial>
        <Conference
            startConferenceOnEnter="false"
            endConferenceOnExit="false"
            beep="true"
        >{conference_room}</Conference>
    </Dial>
</Response>"""


class ConferenceSession:
    """Tracks a multi-party conference call."""

    def __init__(self, room_name: str, initiated_by: str):
        self.room_name = room_name
        self.initiated_by = initiated_by
        self.created_at = datetime.now(timezone.utc).isoformat()
        self.participants: list = []      # {number, call_sid, joined_at, role}
        self.ns_muted: bool = True        # NS silent by default
        self.transcript_segments: list = []
        self.ns_interventions: list = []  # Only NS-spoken turns
        self.recording_url: str = ""
        self.status: str = "active"

    def add_participant(self, number: str, call_sid: str, role: str = "guest"):
        self.participants.append({
            "number": number,
            "call_sid": call_sid,
            "joined_at": datetime.now(timezone.utc).isoformat(),
            "role": role
        })

    def ns_speak(self, text: str):
        """Log NS intervention when explicitly invited."""
        self.ns_interventions.append({
            "text": text,
            "ts": datetime.now(timezone.utc).isoformat()
        })
        self.ns_muted = True  # Return to silent after speaking

    def add_transcript(self, speaker: str, text: str):
        self.transcript_segments.append({
            "speaker": speaker,
            "text": text,
            "ts": datetime.now(timezone.utc).isoformat()
        })

    def to_receipt(self) -> dict:
        return {
            "room_name": self.room_name,
            "initiated_by": self.initiated_by,
            "created_at": self.created_at,
            "status": self.status,
            "participant_count": len(self.participants),
            "participants": self.participants,
            "ns_interventions": len(self.ns_interventions),
            "transcript_segments": len(self.transcript_segments),
            "recording_url": self.recording_url,
        }


# Conference session store
_conferences: dict = {}


def get_or_create_conference(room_name: str, initiated_by: str = "founder") -> ConferenceSession:
    if room_name not in _conferences:
        _conferences[room_name] = ConferenceSession(room_name, initiated_by)
    return _conferences[room_name]


def active_conferences() -> list:
    return [c.to_receipt() for c in _conferences.values() if c.status == "active"]
