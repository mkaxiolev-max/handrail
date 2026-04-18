"""LivingArchitecture — live 10-layer stack renderer for the Founder Console (B6).

Renders the canonical 10-layer ontology with per-layer health signals sourced
from EngineRoom state.  L10 (Narrative) may NEVER amend L1–L9 per doctrinal
partition; this renderer is strictly read-only toward all layers.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

LAYER_NAMES: list[str] = [
    "L1 Constitutional",
    "L2 Gradient Field",
    "L3 Intake",
    "L4 The Loom",
    "L5 Alexandrian Lexicon",
    "L6 State Manifold",
    "L7 Alexandrian Archive",
    "L8 Lineage Fabric",
    "L9 Error & Correction",
    "L10 Narrative",
]


@dataclass
class LayerStatus:
    layer: str
    index: int
    health: str = "nominal"  # nominal | degraded | offline
    signal: Optional[str] = None
    active: bool = True


@dataclass
class ArchitectureFrame:
    layers: list[LayerStatus] = field(default_factory=list)
    active_layer_index: int = 5  # default: L6 State Manifold
    invariants_satisfied: list[str] = field(default_factory=list)
    invariants_violated: list[str] = field(default_factory=list)

    def active_layer_name(self) -> str:
        if 0 <= self.active_layer_index < len(self.layers):
            return self.layers[self.active_layer_index].layer
        return "unknown"


class LivingArchitecture:
    """Read-only view of the 10-layer stack derived from EngineRoom state."""

    def __init__(self) -> None:
        self._health: dict[int, str] = {}
        self._signals: dict[int, str] = {}

    def set_layer_health(self, layer_index: int, health: str, signal: Optional[str] = None) -> None:
        self._health[layer_index] = health
        if signal:
            self._signals[layer_index] = signal

    def render(self, active_layer_index: int = 5) -> ArchitectureFrame:
        layers = [
            LayerStatus(
                layer=name,
                index=i,
                health=self._health.get(i, "nominal"),
                signal=self._signals.get(i),
                active=(i == active_layer_index),
            )
            for i, name in enumerate(LAYER_NAMES)
        ]
        return ArchitectureFrame(
            layers=layers,
            active_layer_index=active_layer_index,
        )

    def render_dict(self, active_layer_index: int = 5) -> dict:
        frame = self.render(active_layer_index)
        return {
            "active_layer": frame.active_layer_name(),
            "layers": [
                {
                    "index": ls.index,
                    "layer": ls.layer,
                    "health": ls.health,
                    "signal": ls.signal,
                    "active": ls.active,
                }
                for ls in frame.layers
            ],
        }
