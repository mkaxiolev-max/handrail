"""Noetic Mass — accumulated conceptual weight of a knowledge node."""
from __future__ import annotations
from dataclasses import dataclass, field
import math


@dataclass
class NoeticNode:
    concept: str
    references: int = 0
    connections: list[str] = field(default_factory=list)

    @property
    def mass(self) -> float:
        return round(math.log1p(self.references) * (1 + 0.1 * len(self.connections)), 4)


class NoeticMassRegistry:
    def __init__(self):
        self._nodes: dict[str, NoeticNode] = {}

    def register(self, concept: str) -> NoeticNode:
        if concept not in self._nodes:
            self._nodes[concept] = NoeticNode(concept)
        return self._nodes[concept]

    def increment(self, concept: str, count: int = 1) -> NoeticNode:
        node = self.register(concept)
        node.references += count
        return node

    def connect(self, a: str, b: str) -> None:
        self.register(a).connections.append(b)
        self.register(b).connections.append(a)

    def top_n(self, n: int = 5) -> list[NoeticNode]:
        return sorted(self._nodes.values(), key=lambda x: x.mass, reverse=True)[:n]
