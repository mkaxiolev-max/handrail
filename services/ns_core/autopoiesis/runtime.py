"""Autopoiesis ProgramRuntime — wraps the existing program_runtime.ProgramRuntime."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

# Import existing runtime if available — do NOT redefine
try:
    from program_runtime.runtime import ProgramRuntime as _ExistingRuntime
    _EXISTING_AVAILABLE = True
except ImportError:
    _ExistingRuntime = None
    _EXISTING_AVAILABLE = False

from .initiatives import SEED_INITIATIVES, StrategicInitiative


class ProgramRuntime:
    """Autopoietic ProgramRuntime wrapping the existing runtime."""

    def __init__(self):
        self._inner = _ExistingRuntime() if _EXISTING_AVAILABLE else None
        self._initiatives: List[StrategicInitiative] = list(SEED_INITIATIVES)
        self._adaptations: List[Dict[str, Any]] = []

    def summary(self) -> Dict[str, Any]:
        base = {}
        if self._inner:
            try:
                base = self._inner.summary()
            except Exception:
                pass
        return {
            **base,
            "initiatives": [i.to_dict() for i in self._initiatives],
            "adaptation_count": len(self._adaptations),
            "existing_runtime": _EXISTING_AVAILABLE,
        }

    def record_adaptation(self, proposal: Dict[str, Any]) -> Dict[str, Any]:
        record = {
            "id": str(uuid.uuid4()),
            "proposal": proposal,
            "recorded_at": datetime.now(timezone.utc).isoformat(),
        }
        self._adaptations.append(record)
        return record
