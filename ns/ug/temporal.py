"""
axiolev-ug-temporal-v2
AXIOLEV Holdings LLC © 2026

Temporal Geometry Layer adapter. Sits at L3 boundary. Pure read.
BOHMIAN/PILOT-WAVE LAYER: QUARANTINED — theoretical only.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from .entity import Entity


@dataclass(frozen=True)
class TemporalSlice:
    at: datetime
    entity_id: str
    state_snapshot: dict


def slice_entity(e: Entity, at: Optional[datetime] = None) -> TemporalSlice:
    return TemporalSlice(
        at=at or e.timestamps.updated_at,
        entity_id=e.id,
        state_snapshot=dict(e.state),
    )


BOHMIAN_PILOT_WAVE_STATUS = "QUARANTINED: theoretical only"
