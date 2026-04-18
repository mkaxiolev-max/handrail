"""AXIOLEV NS∞ — MLS adapter (RESO Web API shape, mocked)."""
from datetime import datetime, timezone

class MLSAdapter:
    def __init__(self, config=None):
        self.config = config or {}
        self.mock = self.config.get("mock", True)

    def fetch_property(self, address):
        return {"ok": True, "adapter": "mls.fetch_property", "mock": self.mock,
                "address": address, "data": {"beds": 3, "baths": 2, "sqft": 1820}}

    def fetch_comps(self, address, radius_mi=0.5):
        return {"ok": True, "adapter": "mls.fetch_comps", "mock": self.mock,
                "address": address, "comps": []}

    def stage_listing(self, listing):
        return {"ok": True, "adapter": "mls.stage_listing", "mock": self.mock,
                "listing_id": f"staged_{int(datetime.now(timezone.utc).timestamp())}"}

    def publish_listing(self, staging_id):
        return {"ok": True, "adapter": "mls.publish_listing", "mock": self.mock,
                "mls_number": f"MOCK{staging_id[-8:]}"}
