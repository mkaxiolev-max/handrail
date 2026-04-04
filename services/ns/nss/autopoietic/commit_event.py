"""
NS∞ CommitEvent Governance
===========================
Separates provisional change from committed truth.
Authority only exists at commit events.

States: pending_review → approved → committed | rejected

This is the human gate. NS proposes. Founder commits.
"""
from __future__ import annotations
import json, uuid
from datetime import datetime, timezone
from pathlib import Path


_EVENTS_SSD  = Path("/Volumes/NSExternal/ALEXANDRIA/commit_events.jsonl")
_EVENTS_FALL = Path(".runs/commit_events.jsonl")


def _events_path() -> Path:
    return _EVENTS_SSD if _EVENTS_SSD.parent.exists() else _EVENTS_FALL


def create_event(plan_id: str, spec_id: str, proposed_by: str = "ns") -> dict:
    event = {
        "event_id":    str(uuid.uuid4())[:8],
        "plan_id":     plan_id,
        "spec_id":     spec_id,
        "proposed_by": proposed_by,
        "status":      "pending_review",
        "ts":          datetime.now(timezone.utc).isoformat(),
    }
    _append(event)
    return event


def approve(event_id: str, approved_by: str = "founder") -> dict:
    event = {
        "event_id":    event_id,
        "action":      "approved",
        "approved_by": approved_by,
        "ts":          datetime.now(timezone.utc).isoformat(),
    }
    _append(event)
    return {"ok": True, "event_id": event_id, "status": "approved"}


def reject(event_id: str, reason: str = "") -> dict:
    event = {
        "event_id": event_id,
        "action":   "rejected",
        "reason":   reason,
        "ts":       datetime.now(timezone.utc).isoformat(),
    }
    _append(event)
    return {"ok": True, "event_id": event_id, "status": "rejected"}


def _append(event: dict) -> None:
    p = _events_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "a") as f:
        f.write(json.dumps(event) + "\n")


def recent_events(n: int = 10) -> list[dict]:
    p = _events_path()
    if not p.exists():
        return []
    lines = p.read_text().splitlines()[-n:]
    events = []
    for l in lines:
        try:
            events.append(json.loads(l))
        except Exception:
            pass
    return list(reversed(events))
