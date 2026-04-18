"""EngineRoom — aggregates live NCOM/PIIC runtime state for the Founder Console (B6).

Single source of truth for all /founder-console/* endpoints.
Holds a singleton NCOMStateMachine, PIICChain, and CollapseReadiness.
"""
from __future__ import annotations

import datetime
from typing import Optional

from ns.api.schemas.ncom_piic import (
    CollapseReadinessSnapshot,
    ContradictionEntry,
    ContradictionList,
    FounderConsoleHistory,
    FounderConsoleSnapshot,
    HistoryEntry,
    NCOMStateSnapshot,
    ObservationEntry,
    ObservationList,
    PIICStageSnapshot,
    ReceiptEntry,
    ReceiptList,
    RoutingCurrent,
)
from ns.services.ncom.readiness import CollapseReadiness
from ns.services.ncom.state import NCOMStateMachine
from ns.services.piic.chain import PIICChain


def _now() -> str:
    return datetime.datetime.utcnow().isoformat() + "Z"


class EngineRoom:
    """Live aggregator for Founder Console data.

    In the embedded runtime this is instantiated once per process. For a
    distributed deployment each field would be backed by a shared store, but
    the interface remains identical (I8 eventual-consistency boundary).
    """

    def __init__(self) -> None:
        self._ncom = NCOMStateMachine()
        self._piic = PIICChain()
        self._readiness = CollapseReadiness()
        self._contradictions: list[ContradictionEntry] = []
        self._observations: list[ObservationEntry] = []
        self._receipts: list[ReceiptEntry] = []
        self._routing_layer = "L6 State Manifold"
        self._top_interpretation: Optional[str] = None
        self._route_intent: Optional[str] = None

    # ------------------------------------------------------------------
    # Snapshot
    # ------------------------------------------------------------------

    def snapshot(self) -> FounderConsoleSnapshot:
        ncom_snap = NCOMStateSnapshot(
            state=self._ncom.state.value,
            history=[s.value for s in self._ncom.history],
            is_terminal=self._ncom.is_terminal(),
            is_collapse_ready=self._ncom.is_collapse_ready(),
        )
        piic_snap = PIICStageSnapshot(
            stage=self._piic.stage.value,
            history=[s.value for s in self._piic.history],
            is_committed=self._piic.is_committed(),
        )
        r = self._readiness
        readiness_snap = CollapseReadinessSnapshot(
            ERS=r.ERS,
            CRS=r.CRS,
            IPI=r.IPI,
            contradictionPressure=r.contradictionPressure,
            branchDiversityAdequacy=r.branchDiversityAdequacy,
            hardVetoes=list(r.hardVetoes),
            recommendedAction=r.recommendedAction,
        )
        return FounderConsoleSnapshot(
            ncom=ncom_snap,
            piic=piic_snap,
            readiness=readiness_snap,
            timestamp=_now(),
        )

    # ------------------------------------------------------------------
    # History
    # ------------------------------------------------------------------

    def history(self) -> FounderConsoleHistory:
        ncom_entries = [
            HistoryEntry(event_type="ncom_state", value=s.value, timestamp=_now())
            for s in self._ncom.history
        ]
        piic_entries = [
            HistoryEntry(event_type="piic_stage", value=s.value, timestamp=_now())
            for s in self._piic.history
        ]
        return FounderConsoleHistory(ncom_history=ncom_entries, piic_history=piic_entries)

    # ------------------------------------------------------------------
    # Contradictions
    # ------------------------------------------------------------------

    def active_contradictions(self) -> ContradictionList:
        return ContradictionList(
            active=list(self._contradictions),
            count=len(self._contradictions),
        )

    def add_contradiction(self, entry: ContradictionEntry) -> None:
        self._contradictions.append(entry)

    def clear_contradiction(self, contradiction_id: str) -> bool:
        before = len(self._contradictions)
        self._contradictions = [c for c in self._contradictions if c.id != contradiction_id]
        return len(self._contradictions) < before

    # ------------------------------------------------------------------
    # Observations
    # ------------------------------------------------------------------

    def open_observations(self) -> ObservationList:
        open_obs = [o for o in self._observations if o.open]
        return ObservationList(open=open_obs, count=len(open_obs))

    def add_observation(self, entry: ObservationEntry) -> None:
        self._observations.append(entry)

    # ------------------------------------------------------------------
    # Routing
    # ------------------------------------------------------------------

    def routing_current(self) -> RoutingCurrent:
        return RoutingCurrent(
            active_layer=self._routing_layer,
            top_interpretation=self._top_interpretation,
            route_intent=self._route_intent,
        )

    def update_routing(
        self,
        layer: str,
        top_interpretation: Optional[str] = None,
        route_intent: Optional[str] = None,
    ) -> None:
        self._routing_layer = layer
        self._top_interpretation = top_interpretation
        self._route_intent = route_intent

    # ------------------------------------------------------------------
    # Receipts
    # ------------------------------------------------------------------

    def recent_receipts(self, limit: int = 20) -> ReceiptList:
        recent = self._receipts[-limit:]
        return ReceiptList(recent=list(recent), count=len(recent))

    def append_receipt(self, receipt_name: str, payload: dict | None = None) -> None:
        self._receipts.append(
            ReceiptEntry(
                receipt_name=receipt_name,
                timestamp=_now(),
                payload=payload or {},
            )
        )

    # ------------------------------------------------------------------
    # Mutators (used by runtime event handlers)
    # ------------------------------------------------------------------

    @property
    def ncom(self) -> NCOMStateMachine:
        return self._ncom

    @property
    def piic(self) -> PIICChain:
        return self._piic

    def update_readiness(self, readiness: CollapseReadiness) -> None:
        self._readiness = readiness
