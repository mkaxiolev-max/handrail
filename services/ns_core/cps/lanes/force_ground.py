"""force_ground CPS lane.

When NER exceeds threshold, subsequent ops must include explicit ground-truth
anchors (receipt IDs, file SHAs, endpoint responses). Until YK slot_2,
force_ground is advisory — it logs the demand and records state.
"""
from __future__ import annotations

from typing import Any, Dict, Optional


class ForceGroundState:
    def __init__(self):
        self.active = False
        self.trigger_count = 0
        self.last_trigger_rate: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "active": self.active,
            "trigger_count": self.trigger_count,
            "last_trigger_rate": self.last_trigger_rate,
        }


class ForceGroundLane:
    """Advisory force_ground lane — deterministic trigger, advisory enforcement."""

    def __init__(self):
        self._state = ForceGroundState()

    def activate(self, ner_rate: float) -> Dict[str, Any]:
        self._state.active = True
        self._state.trigger_count += 1
        self._state.last_trigger_rate = ner_rate
        return {
            "activated": True,
            "ner_rate": ner_rate,
            "advisory": True,
            "note": "force_ground advisory: ops must include ground-truth anchors",
            "hw_abort_available": False,  # false until YK slot_2
        }

    def deactivate(self) -> Dict[str, Any]:
        self._state.active = False
        return {"activated": False}

    def check(self, op: Dict[str, Any]) -> Dict[str, Any]:
        """Check if op carries required anchors when force_ground is active."""
        if not self._state.active:
            return {"pass": True, "force_ground_active": False}
        has_anchor = bool(
            op.get("receipt_id") or op.get("sha") or op.get("endpoint_response")
        )
        return {
            "pass": has_anchor,
            "force_ground_active": True,
            "advisory": True,
            "missing_anchor": not has_anchor,
        }

    def state(self) -> Dict[str, Any]:
        return self._state.to_dict()
