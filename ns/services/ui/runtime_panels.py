"""RuntimePanels — composable UI panel renderers for the Founder Console (B6).

Renders:
- NCOM state pill
- PIIC stage chain
- IPI / ERS / CRS gauges
- Contradiction list
- Top interpretation
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from ns.api.schemas.ncom_piic import (
    CollapseReadinessSnapshot,
    ContradictionEntry,
    NCOMStateSnapshot,
    PIICStageSnapshot,
)


# ---------------------------------------------------------------------------
# NCOM state pill
# ---------------------------------------------------------------------------

_STATE_COLOURS: dict[str, str] = {
    "inactive": "grey",
    "priming": "blue",
    "observing": "cyan",
    "branching": "yellow",
    "stabilizing": "orange",
    "ready_for_collapse": "green",
    "forced_collapse": "green",
    "aborted": "red",
}


@dataclass
class NCOMPill:
    state: str
    colour: str
    is_terminal: bool
    is_collapse_ready: bool

    def label(self) -> str:
        return self.state.replace("_", " ").upper()


def render_ncom_pill(snap: NCOMStateSnapshot) -> NCOMPill:
    return NCOMPill(
        state=snap.state,
        colour=_STATE_COLOURS.get(snap.state, "grey"),
        is_terminal=snap.is_terminal,
        is_collapse_ready=snap.is_collapse_ready,
    )


# ---------------------------------------------------------------------------
# PIIC stage chain
# ---------------------------------------------------------------------------

PIIC_STAGES = ["perception", "interpretation", "identification", "commitment"]


@dataclass
class PIICStageNode:
    stage: str
    active: bool
    complete: bool


@dataclass
class PIICChainPanel:
    nodes: list[PIICStageNode]
    current_stage: str
    is_committed: bool


def render_piic_chain(snap: PIICStageSnapshot) -> PIICChainPanel:
    current_idx = PIIC_STAGES.index(snap.stage) if snap.stage in PIIC_STAGES else 0
    nodes = [
        PIICStageNode(
            stage=s,
            active=(s == snap.stage),
            complete=(i < current_idx),
        )
        for i, s in enumerate(PIIC_STAGES)
    ]
    return PIICChainPanel(
        nodes=nodes,
        current_stage=snap.stage,
        is_committed=snap.is_committed,
    )


# ---------------------------------------------------------------------------
# Readiness gauges
# ---------------------------------------------------------------------------

@dataclass
class Gauge:
    name: str
    value: float
    pct: int
    status: str  # ok | warn | critical

    def bar(self, width: int = 20) -> str:
        filled = round(self.pct * width / 100)
        return "█" * filled + "░" * (width - filled)


def _gauge_status(value: float, inverted: bool = False) -> str:
    if inverted:
        if value <= 0.3:
            return "ok"
        if value <= 0.6:
            return "warn"
        return "critical"
    if value >= 0.7:
        return "ok"
    if value >= 0.5:
        return "warn"
    return "critical"


@dataclass
class ReadinessPanel:
    ERS: Gauge
    CRS: Gauge
    IPI: Gauge
    contradiction_pressure: Gauge
    branch_diversity: Gauge
    recommended_action: str
    hard_vetoes: list[str]


def render_readiness_gauges(snap: CollapseReadinessSnapshot) -> ReadinessPanel:
    def g(name: str, value: float, inverted: bool = False) -> Gauge:
        return Gauge(
            name=name,
            value=value,
            pct=round(value * 100),
            status=_gauge_status(value, inverted),
        )

    return ReadinessPanel(
        ERS=g("ERS", snap.ERS),
        CRS=g("CRS", snap.CRS),
        IPI=g("IPI", snap.IPI),
        contradiction_pressure=g("Contradiction Pressure", snap.contradictionPressure, inverted=True),
        branch_diversity=g("Branch Diversity", snap.branchDiversityAdequacy),
        recommended_action=snap.recommendedAction,
        hard_vetoes=list(snap.hardVetoes),
    )


# ---------------------------------------------------------------------------
# Contradiction list
# ---------------------------------------------------------------------------

@dataclass
class ContradictionPanel:
    entries: list[ContradictionEntry]
    count: int
    highest_weight: Optional[float]

    def top(self) -> Optional[ContradictionEntry]:
        if not self.entries:
            return None
        return max(self.entries, key=lambda e: e.weight)


def render_contradiction_list(entries: list[ContradictionEntry]) -> ContradictionPanel:
    return ContradictionPanel(
        entries=sorted(entries, key=lambda e: e.weight, reverse=True),
        count=len(entries),
        highest_weight=max((e.weight for e in entries), default=None),
    )


# ---------------------------------------------------------------------------
# Top interpretation
# ---------------------------------------------------------------------------

@dataclass
class InterpretationPanel:
    top_interpretation: Optional[str]
    route_intent: Optional[str]
    active_layer: str


def render_top_interpretation(
    top_interpretation: Optional[str],
    route_intent: Optional[str],
    active_layer: str,
) -> InterpretationPanel:
    return InterpretationPanel(
        top_interpretation=top_interpretation,
        route_intent=route_intent,
        active_layer=active_layer,
    )
