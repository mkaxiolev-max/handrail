"""Object-model wrapper around service.dashboard() for renderers."""
from dataclasses import dataclass, asdict
from typing import Optional
@dataclass
class AletheiaControlDashboard:
    classifications: int
    atoms:           int
    chains:          int
    wastes:          int
    control_ratio:   float
    concern_leakage: float
    false_control_rate: float
    feedback_integrity: float
    influence_conversion: float
    omega:           Optional[float] = None
    @classmethod
    def from_dict(cls, d: dict) -> "AletheiaControlDashboard":
        return cls(**{k:v for k,v in d.items() if k in cls.__dataclass_fields__})
    def to_dict(self) -> dict: return asdict(self)
