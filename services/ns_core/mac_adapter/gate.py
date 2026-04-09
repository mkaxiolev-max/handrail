"""
MacAdapterGate — capability gating for Mac OS adapter bridge.

Every Mac adapter call must pass through this gate.
Produces an AdapterReceipt on every evaluation (allow or deny).
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
import hashlib, json

# ── Capability lists ──────────────────────────────────────────────────────────

MAC_ALLOWED_CAPABILITIES = {
    "audio.get_volume",
    "audio.get_playing",
    "clipboard.read",
    "notify.send",
    "display.get_info",
    "battery.get_status",
    "battery.get_power_source",
    "calendar.today",
}

MAC_ESCALATION_REQUIRED = {
    "audio.set_volume",
    "clipboard.write",
    "display.set_brightness",
    "vision.screenshot",
    "vision.ocr_region",
    "keychain.check_entry",
    "keychain.list_services",
    "alert.dialog",
}

# ── Request / Receipt models ───────────────────────────────────────────────────

@dataclass
class AdapterRequest:
    capability: str
    requester: str
    args: dict = field(default_factory=dict)
    escalation_approved: bool = False
    request_id: str = field(default_factory=lambda: __import__("uuid").uuid4().hex)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

@dataclass
class GateDecision:
    allowed: bool
    reason: str
    requires_escalation: bool = False

@dataclass
class AdapterReceipt:
    request_id: str
    capability: str
    requester: str
    decision: GateDecision
    timestamp: str
    receipt_hash: str

    def to_dict(self) -> dict:
        return {
            "request_id": self.request_id,
            "capability": self.capability,
            "requester": self.requester,
            "allowed": self.decision.allowed,
            "reason": self.decision.reason,
            "requires_escalation": self.decision.requires_escalation,
            "timestamp": self.timestamp,
            "receipt_hash": self.receipt_hash,
        }

# ── Gate ─────────────────────────────────────────────────────────────────────

class MacAdapterGate:
    """
    Evaluate every Mac adapter capability request.
    Returns AdapterReceipt on every call — even denials.
    """

    def __init__(self):
        self._receipts: list[AdapterReceipt] = []

    def evaluate(self, request: AdapterRequest) -> AdapterReceipt:
        decision = self._decide(request)
        raw = json.dumps({
            "request_id": request.request_id,
            "capability": request.capability,
            "allowed": decision.allowed,
        }, sort_keys=True)
        receipt_hash = hashlib.sha256(raw.encode()).hexdigest()
        receipt = AdapterReceipt(
            request_id=request.request_id,
            capability=request.capability,
            requester=request.requester,
            decision=decision,
            timestamp=request.timestamp,
            receipt_hash=receipt_hash,
        )
        self._receipts.append(receipt)
        return receipt

    def _decide(self, request: AdapterRequest) -> GateDecision:
        cap = request.capability
        if cap in MAC_ALLOWED_CAPABILITIES:
            return GateDecision(allowed=True, reason="capability_in_allowed_list")
        if cap in MAC_ESCALATION_REQUIRED:
            if request.escalation_approved:
                return GateDecision(allowed=True, reason="escalation_approved", requires_escalation=True)
            return GateDecision(
                allowed=False,
                reason="escalation_required_but_not_approved",
                requires_escalation=True,
            )
        return GateDecision(allowed=False, reason="capability_unknown")

    def receipts(self) -> list[AdapterReceipt]:
        return list(self._receipts)

    def denied_count(self) -> int:
        return sum(1 for r in self._receipts if not r.decision.allowed)


_gate = MacAdapterGate()

def get_mac_gate() -> MacAdapterGate:
    return _gate
