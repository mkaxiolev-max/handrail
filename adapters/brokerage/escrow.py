"""AXIOLEV NS∞ — Escrow adapter (mocked)."""
from datetime import datetime, timezone

class EscrowAdapter:
    def __init__(self, config=None):
        self.config = config or {}
        self.mock = self.config.get("mock", True)

    def open(self, contract_id):
        return {"ok": True, "adapter": "escrow.open", "mock": self.mock,
                "escrow_id": f"esc_{int(datetime.now(timezone.utc).timestamp())}"}

    def track_deadline(self, escrow_id, deadline):
        return {"ok": True, "adapter": "escrow.track_deadline", "mock": self.mock,
                "escrow_id": escrow_id, "deadline": deadline}

    def attach_title_update(self, escrow_id, update):
        return {"ok": True, "adapter": "escrow.attach_title_update", "mock": self.mock,
                "escrow_id": escrow_id}

    def attach_lender_update(self, escrow_id, update):
        return {"ok": True, "adapter": "escrow.attach_lender_update", "mock": self.mock,
                "escrow_id": escrow_id}
