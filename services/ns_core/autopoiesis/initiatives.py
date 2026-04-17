"""5 seed StrategicInitiatives."""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import List


@dataclass
class StrategicInitiative:
    id: str
    name: str
    cadence: str
    status: str = "active"

    def to_dict(self):
        return asdict(self)


SEED_INITIATIVES: List[StrategicInitiative] = [
    StrategicInitiative("SI-1", "Ledger hygiene",                "hourly"),
    StrategicInitiative("SI-2", "Canon candidate review",        "daily"),
    StrategicInitiative("SI-3", "NER baseline calibration",      "daily"),
    StrategicInitiative("SI-4", "Clearing abstention audit",     "weekly"),
    StrategicInitiative("SI-5", "Cathedral progress attestation","weekly"),
]
