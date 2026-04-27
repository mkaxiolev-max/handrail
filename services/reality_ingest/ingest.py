"""Reality Ingest — voice + document + drive delta ingestion pipeline."""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import time


class SourceType(str, Enum):
    VOICE = "voice"
    DOCUMENT = "document"
    DRIVE_DELTA = "drive_delta"
    API = "api"


@dataclass
class IngestEvent:
    event_id: str
    source: SourceType
    payload: str
    ts: float
    hash: str
    processed: bool = False


def _event_id(source: SourceType, payload: str, ts: float) -> str:
    return hashlib.sha256(f"{source}:{payload}:{ts}".encode()).hexdigest()[:16]


class RealityIngestPipeline:
    def __init__(self):
        self._events: list[IngestEvent] = []
        self._processors: list = []

    def ingest(self, source: SourceType, payload: str) -> IngestEvent:
        ts = time.time()
        eid = _event_id(source, payload, ts)
        h = hashlib.sha256(payload.encode()).hexdigest()
        event = IngestEvent(event_id=eid, source=source, payload=payload, ts=ts, hash=h)
        self._events.append(event)
        return event

    def process_pending(self) -> int:
        count = 0
        for e in self._events:
            if not e.processed:
                e.processed = True
                count += 1
        return count

    def event_count(self, source: SourceType | None = None) -> int:
        if source is None:
            return len(self._events)
        return sum(1 for e in self._events if e.source == source)

    def recent(self, n: int = 10) -> list[IngestEvent]:
        return sorted(self._events, key=lambda e: e.ts, reverse=True)[:n]
