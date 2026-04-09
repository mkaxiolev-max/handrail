from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()

class ObjectLifecycle(str, Enum):
    raw = "raw"
    classified = "classified"
    digested = "digested"
    stressed = "stressed"
    compressed = "compressed"
    signaled = "signaled"
    superseded = "superseded"

@dataclass
class MetabolicObject:
    object_id: str = field(default_factory=lambda: str(uuid4()))
    content: Any = None
    object_type: str = ""
    lifecycle: ObjectLifecycle = ObjectLifecycle.raw
    metadata: dict = field(default_factory=dict)
    contradiction_refs: list[str] = field(default_factory=list)
    compression_source_ids: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)

@dataclass
class ExhaustEvent:
    exhaust_id: str = field(default_factory=lambda: str(uuid4()))
    loom: str = ""
    event_type: str = ""
    object_id: str = ""
    payload: dict = field(default_factory=dict)
    emitted_at: str = field(default_factory=utc_now)

class MetabolismEngine:
    def __init__(self):
        self._objects: dict[str, MetabolicObject] = {}
        self._exhaust_bus: list[ExhaustEvent] = []

    def _emit(self, loom: str, event_type: str, obj: MetabolicObject, payload: dict | None = None):
        self._exhaust_bus.append(ExhaustEvent(loom=loom, event_type=event_type,
                                               object_id=obj.object_id, payload=payload or {}))

    def intake(self, content: Any, object_type: str, metadata: dict | None = None) -> MetabolicObject:
        obj = MetabolicObject(content=content, object_type=object_type,
                              lifecycle=ObjectLifecycle.classified, metadata=metadata or {})
        self._objects[obj.object_id] = obj
        self._emit("intake", "classified", obj, {"object_type": object_type})
        return obj

    def digest(self, object_id: str, structured_form: dict) -> MetabolicObject:
        obj = self._objects.get(object_id)
        if not obj:
            raise ValueError(f"Object {object_id} not found")
        if obj.lifecycle != ObjectLifecycle.classified:
            raise ValueError(f"Expected classified, got {obj.lifecycle}")
        obj.metadata["structured"] = structured_form
        obj.lifecycle = ObjectLifecycle.digested
        obj.updated_at = utc_now()
        self._emit("digest", "processed", obj)
        return obj

    def stress(self, object_id: str, contradictions: list[str], stress_score: float) -> MetabolicObject:
        obj = self._objects.get(object_id)
        if not obj:
            raise ValueError(f"Object {object_id} not found")
        obj.contradiction_refs = contradictions
        obj.metadata["stress_score"] = stress_score
        obj.lifecycle = ObjectLifecycle.stressed
        obj.updated_at = utc_now()
        self._emit("stress", "contradicted" if contradictions else "processed", obj,
                   {"contradiction_count": len(contradictions), "stress_score": stress_score})
        return obj

    def compress(self, source_ids: list[str], canonical_summary: str) -> MetabolicObject:
        sources = [self._objects[sid] for sid in source_ids if sid in self._objects]
        if not sources:
            raise ValueError("No valid source objects")
        compressed = MetabolicObject(
            content=canonical_summary, object_type="canonical_compression",
            lifecycle=ObjectLifecycle.compressed,
            metadata={"source_count": len(sources), "canonical_summary": canonical_summary},
            compression_source_ids=source_ids,
        )
        for src in sources:
            src.lifecycle = ObjectLifecycle.superseded
            src.updated_at = utc_now()
        self._objects[compressed.object_id] = compressed
        self._emit("compress", "compressed", compressed, {"source_count": len(sources)})
        return compressed

    def signal(self, object_id: str, signal_type: str, target: str) -> MetabolicObject:
        obj = self._objects.get(object_id)
        if not obj:
            raise ValueError(f"Object {object_id} not found")
        obj.metadata.update({"signal_type": signal_type, "signal_target": target})
        obj.lifecycle = ObjectLifecycle.signaled
        obj.updated_at = utc_now()
        self._emit("signal", "signaled", obj, {"signal_type": signal_type, "target": target})
        return obj

    def get_exhaust(self, loom: str | None = None) -> list[ExhaustEvent]:
        if loom is None:
            return list(self._exhaust_bus)
        return [e for e in self._exhaust_bus if e.loom == loom]

    def contradiction_backlog(self) -> list[MetabolicObject]:
        return [o for o in self._objects.values() if o.contradiction_refs]

    def freshness_scan(self) -> dict[str, int]:
        return {lc.value: sum(1 for o in self._objects.values() if o.lifecycle == lc)
                for lc in ObjectLifecycle}

    def canon_pressure_report(self) -> dict[str, Any]:
        backlog = self.contradiction_backlog()
        fresh = self.freshness_scan()
        return {
            "contradiction_backlog_size": len(backlog),
            "undigested_objects": fresh.get("classified", 0),
            "compressed_objects": fresh.get("compressed", 0),
            "superseded_objects": fresh.get("superseded", 0),
            "signal_ready": fresh.get("signaled", 0),
            "total_objects": sum(fresh.values()),
        }

_engine = MetabolismEngine()
def get_metabolism_engine() -> MetabolismEngine:
    return _engine
