"""AXIOLEV NS∞ — Offer adapter (mocked)."""
from datetime import datetime, timezone

class OfferAdapter:
    def __init__(self, config=None):
        self.config = config or {}
        self.mock = self.config.get("mock", True)

    def generate(self, terms):
        return {"ok": True, "adapter": "offer.generate", "mock": self.mock,
                "offer_id": f"off_{int(datetime.now(timezone.utc).timestamp())}",
                "terms": terms}

    def compare(self, offers):
        return {"ok": True, "adapter": "offer.compare", "mock": self.mock,
                "ranking": list(range(len(offers)))}

    def counter_generate(self, offer_id, changes):
        return {"ok": True, "adapter": "offer.counter_generate", "mock": self.mock,
                "offer_id": offer_id, "counter": changes}
