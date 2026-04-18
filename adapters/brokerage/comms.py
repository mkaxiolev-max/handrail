"""AXIOLEV NS∞ — Comms adapter (Twilio-shape, mocked)."""
from datetime import datetime, timezone

class CommsAdapter:
    def __init__(self, config=None):
        self.config = config or {}
        self.mock = self.config.get("mock", True)

    def call_outbound(self, to, from_, twiml_url):
        return {"ok": True, "adapter": "comms.call_outbound", "mock": self.mock,
                "call_sid": f"CA{int(datetime.now(timezone.utc).timestamp()):x}"}

    def send_sms(self, to, from_, body):
        return {"ok": True, "adapter": "comms.send_sms", "mock": self.mock,
                "message_sid": f"SM{int(datetime.now(timezone.utc).timestamp()):x}"}

    def send_email(self, to, subject, body):
        return {"ok": True, "adapter": "comms.send_email", "mock": self.mock,
                "message_id": f"em_{int(datetime.now(timezone.utc).timestamp())}"}

    def schedule_showing(self, property_id, when, parties):
        return {"ok": True, "adapter": "comms.schedule_showing", "mock": self.mock,
                "showing_id": f"sh_{int(datetime.now(timezone.utc).timestamp())}"}
