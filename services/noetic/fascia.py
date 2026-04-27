"""Noetic Fascia — connective tissue binding noetic nodes."""
from __future__ import annotations
from dataclasses import dataclass


@dataclass
class FasciaBinding:
    source: str
    target: str
    strength: float  # 0.0–1.0
    binding_type: str


class NoeticFascia:
    def __init__(self):
        self._bindings: list[FasciaBinding] = []

    def bind(self, source: str, target: str, strength: float = 0.5, binding_type: str = "semantic") -> FasciaBinding:
        if not 0.0 <= strength <= 1.0:
            raise ValueError(f"Strength must be 0–1, got {strength}")
        b = FasciaBinding(source, target, strength, binding_type)
        self._bindings.append(b)
        return b

    def bindings_for(self, concept: str) -> list[FasciaBinding]:
        return [b for b in self._bindings if b.source == concept or b.target == concept]

    def avg_strength(self) -> float:
        if not self._bindings:
            return 0.0
        return round(sum(b.strength for b in self._bindings) / len(self._bindings), 4)
