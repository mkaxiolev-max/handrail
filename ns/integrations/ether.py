"""Gradient Field (L2 Gradient Layer) integration.

Canonical alias: ``gradient_field``
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class GradientTriple:
    """A gradient field observation triple: (subject, predicate, object)."""

    subject: str
    predicate: str
    object_: Any
    confidence: float = 1.0
    tick: int = 0


class GradientField:
    """L2 Gradient Layer — ingest and surface gradient triples."""

    def __init__(self) -> None:
        self._triples: list[GradientTriple] = []

    def ingest(self, triple: GradientTriple) -> None:
        self._triples.append(triple)

    def surface(self, min_confidence: float = 0.0) -> list[GradientTriple]:
        return [t for t in self._triples if t.confidence >= min_confidence]

    def clear(self) -> None:
        self._triples.clear()


# Canonical alias per locked ontology
gradient_field = GradientField
