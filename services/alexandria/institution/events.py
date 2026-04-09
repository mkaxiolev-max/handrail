from __future__ import annotations
import hashlib, json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()

@dataclass
class ProvenanceRecord:
    entity_id: str
    activity_id: str
    agent_id: str
    used_entities: list[str] = field(default_factory=list)
    generated_at: str = field(default_factory=utc_now)

@dataclass
class AlexandriaEvent:
    event_id: str = field(default_factory=lambda: str(uuid4()))
    event_type: str = ""
    payload: dict = field(default_factory=dict)
    provenance: ProvenanceRecord | None = None
    prev_event_hash: str = ""
    hash: str = ""
    timestamp: str = field(default_factory=utc_now)

    def compute_hash(self) -> str:
        content = json.dumps({
            "event_id": self.event_id, "event_type": self.event_type,
            "payload": self.payload, "prev_event_hash": self.prev_event_hash,
            "timestamp": self.timestamp,
        }, sort_keys=True, default=str)
        return hashlib.sha256(content.encode()).hexdigest()

    def verify_chain(self, prev: "AlexandriaEvent | None") -> bool:
        if prev is None:
            return self.prev_event_hash == ""
        return self.prev_event_hash == prev.hash

class EventSpine:
    def __init__(self):
        self._events: list[AlexandriaEvent] = []

    def append(self, event_type: str, payload: dict, agent_id: str,
               used_entities: list[str] | None = None) -> AlexandriaEvent:
        prev_hash = self._events[-1].hash if self._events else ""
        prov = ProvenanceRecord(
            entity_id=payload.get("entity_id", "unknown"),
            activity_id=event_type, agent_id=agent_id,
            used_entities=used_entities or [],
        )
        event = AlexandriaEvent(event_type=event_type, payload=payload,
                                provenance=prov, prev_event_hash=prev_hash)
        event.hash = event.compute_hash()
        self._events.append(event)
        return event

    def replay(self, up_to_hash: str | None = None) -> list[AlexandriaEvent]:
        if up_to_hash is None:
            return list(self._events)
        result = []
        for e in self._events:
            result.append(e)
            if e.hash == up_to_hash:
                break
        return result

    def verify_integrity(self) -> tuple[bool, str]:
        for i in range(1, len(self._events)):
            if not self._events[i].verify_chain(self._events[i - 1]):
                return False, f"CHAIN BREAK at event {i}"
        return True, f"{len(self._events)} events verified"

    def count(self) -> int:
        return len(self._events)

    def last(self) -> AlexandriaEvent | None:
        return self._events[-1] if self._events else None

_spine = EventSpine()
def get_event_spine() -> EventSpine:
    return _spine
