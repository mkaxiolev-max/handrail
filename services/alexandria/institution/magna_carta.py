from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4
from .events import get_event_spine

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()

@dataclass
class Amendment:
    amendment_id: str = field(default_factory=lambda: str(uuid4()))
    version: int = 1
    description: str = ""
    rationale: str = ""
    evidence_refs: list[str] = field(default_factory=list)
    authorized_by: str = "founder"
    supersedes_version: int | None = None
    issued_at: str = field(default_factory=utc_now)
    policy_hash: str = ""

@dataclass
class MagnaCarta:
    charter_id: str = field(default_factory=lambda: str(uuid4()))
    name: str = "NS∞ Operating Charter"
    hard_prohibitions: list[str] = field(default_factory=lambda: [
        "NS may not take destructive action without Founder authorization",
        "NS may not modify its own constitutional constraints",
        "NS may not bypass the receipt chain",
        "NS may not disclose restricted data to external providers",
        "NS may not execute irreversible actions without recorded receipt",
    ])
    autonomous_domain: list[str] = field(default_factory=lambda: [
        "information retrieval from Alexandria",
        "draft plan generation (proposals only, not execution)",
        "Violet narrative synthesis from permitted projections",
        "voice session management within Twilio bounds",
        "feed generation and atom classification",
    ])
    escalation_triggers: list[str] = field(default_factory=lambda: [
        "any irreversible real-world action",
        "any external financial transaction",
        "any modification to Ring 5 credentials",
        "any action with policy.decision == deny",
        "any action where epistemic.confidence < 0.5",
    ])
    degradation_states: list[str] = field(default_factory=lambda: [
        "insufficient_context", "low_confidence", "policy_conflict",
        "chain_break", "quorum_failure",
    ])
    amendments: list[Amendment] = field(default_factory=list)
    current_version: int = 1
    created_at: str = field(default_factory=utc_now)

    def issue_amendment(self, description: str, rationale: str,
                        authorized_by: str = "founder",
                        evidence_refs: list[str] | None = None) -> Amendment:
        amendment = Amendment(
            version=self.current_version + 1,
            description=description, rationale=rationale,
            evidence_refs=evidence_refs or [], authorized_by=authorized_by,
            supersedes_version=self.current_version,
        )
        self.amendments.append(amendment)
        self.current_version += 1
        get_event_spine().append("magna_carta_amended", {
            "entity_id": self.charter_id, "amendment_id": amendment.amendment_id,
            "version": amendment.version, "description": description,
            "authorized_by": authorized_by,
        }, agent_id=authorized_by)
        return amendment

    def check_action_allowed(self, action_description: str) -> tuple[bool, str]:
        for prohibition in self.hard_prohibitions:
            if any(kw in action_description.lower()
                   for kw in ["destroy", "delete", "override", "bypass", "modify charter"]):
                return False, f"PROHIBITED: matches hard prohibition"
        return True, "within_odd"

_carta = MagnaCarta()
def get_magna_carta() -> MagnaCarta:
    return _carta
