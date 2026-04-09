from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()

class NarrativeClass(str, Enum):
    observation = "observation"
    interpretation = "interpretation"
    hypothesis = "hypothesis"
    proposal = "proposal"
    instructional_summary = "instructional_summary"
    canonical_summary = "canonical_summary"

class NarrativeState(str, Enum):
    drafted = "drafted"
    buffered = "buffered"
    challenged = "challenged"
    stabilized = "stabilized"
    superseded = "superseded"

@dataclass
class NarrativeObject:
    narrative_id: str = field(default_factory=lambda: str(uuid4()))
    narrative_class: NarrativeClass = NarrativeClass.observation
    state: NarrativeState = NarrativeState.drafted
    human_text: str = ""
    based_on: list[str] = field(default_factory=list)
    unresolved: list[str] = field(default_factory=list)
    would_falsify: list[str] = field(default_factory=list)
    what_changed: list[str] = field(default_factory=list)
    not_claiming: list[str] = field(default_factory=list)
    machine_packet: dict[str, Any] = field(default_factory=dict)
    closure_risk: float = 0.5
    confidence: float = 0.5
    created_at: str = field(default_factory=utc_now)
    superseded_by: str | None = None

    def compute_closure_risk(self) -> float:
        risk = 0.5
        if not self.unresolved: risk += 0.15
        if not self.would_falsify: risk += 0.15
        if not self.not_claiming: risk += 0.1
        if not self.based_on: risk += 0.2
        if self.confidence > 0.8 and not self.based_on: risk += 0.2
        self.closure_risk = min(risk, 1.0)
        return self.closure_risk

    def can_stabilize(self) -> tuple[bool, str]:
        if not self.based_on:
            return False, "based_on is empty"
        if not self.unresolved and self.narrative_class not in [
            NarrativeClass.observation, NarrativeClass.instructional_summary
        ]:
            return False, "unresolved is empty — declare at least one open question"
        if self.compute_closure_risk() > 0.75:
            return False, f"closure_risk={self.closure_risk:.2f} too high"
        return True, "ok"

    def advance_state(self) -> tuple[bool, str]:
        transitions = {
            NarrativeState.drafted: NarrativeState.buffered,
            NarrativeState.buffered: NarrativeState.challenged,
            NarrativeState.challenged: NarrativeState.stabilized,
        }
        if self.state in (NarrativeState.stabilized, NarrativeState.superseded):
            return False, f"cannot advance from {self.state}"
        next_state = transitions.get(self.state)
        if next_state == NarrativeState.stabilized:
            ok, reason = self.can_stabilize()
            if not ok:
                return False, reason
        self.state = next_state
        return True, f"advanced to {next_state}"

    def to_dual_channel(self) -> dict[str, Any]:
        return {
            "human": {"text": self.human_text, "class": self.narrative_class,
                      "state": self.state, "confidence": self.confidence},
            "machine": {**self.machine_packet, "narrative_id": self.narrative_id,
                        "closure_risk": self.compute_closure_risk(),
                        "based_on_count": len(self.based_on),
                        "unresolved_count": len(self.unresolved)},
        }

class NarrativeBuffer:
    def __init__(self):
        self._buffer: dict[str, NarrativeObject] = {}

    def add(self, obj: NarrativeObject) -> NarrativeObject:
        self._buffer[obj.narrative_id] = obj
        return obj

    def get(self, narrative_id: str) -> NarrativeObject | None:
        return self._buffer.get(narrative_id)

    def get_stabilized(self) -> list[NarrativeObject]:
        return [o for o in self._buffer.values() if o.state == NarrativeState.stabilized]

    def get_high_risk(self, threshold: float = 0.7) -> list[NarrativeObject]:
        return [o for o in self._buffer.values() if o.compute_closure_risk() >= threshold]

    def count(self) -> dict[str, int]:
        counts = {s.value: 0 for s in NarrativeState}
        for obj in self._buffer.values():
            counts[obj.state.value] += 1
        return counts
