"""Reversibility registry — AXIOLEV © 2026."""
from dataclasses import dataclass
from enum import Enum

class Kind(str, Enum):
    REVERSIBLE = "reversible"
    IRREVERSIBLE = "irreversible"

@dataclass(frozen=True)
class Transition:
    name: str; kind: Kind; inverse: str | None = None; justification_receipt: str | None = None
    def __post_init__(self):
        if self.kind == Kind.IRREVERSIBLE and not self.justification_receipt:
            raise ValueError(f"irreversible transition {self.name} requires justification_receipt")

REGISTRY: dict[str, Transition] = {}
def register(t: Transition) -> None: REGISTRY[t.name] = t
