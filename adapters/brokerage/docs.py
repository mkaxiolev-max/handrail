"""AXIOLEV NS∞ — Docs adapter (DocuSign-shape, mocked)."""
from datetime import datetime, timezone

class DocsAdapter:
    def __init__(self, config=None):
        self.config = config or {}
        self.mock = self.config.get("mock", True)

    def request_esign(self, doc, signers):
        return {"ok": True, "adapter": "docs.request_esign", "mock": self.mock,
                "envelope_id": f"env_{int(datetime.now(timezone.utc).timestamp())}",
                "signers": [s.get("email") for s in signers]}

    def send_pamphlet(self, to, pamphlet_kind):
        return {"ok": True, "adapter": "docs.send_pamphlet", "mock": self.mock,
                "to": to, "kind": pamphlet_kind}

    def surface_wa_brokerage_pamphlet(self, buyer_or_seller):
        return {"ok": True, "adapter": "docs.surface_wa_brokerage_pamphlet",
                "mock": self.mock, "party": buyer_or_seller}
