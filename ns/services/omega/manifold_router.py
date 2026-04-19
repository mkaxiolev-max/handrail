"""NS∞ CQHML Manifold Engine — Omega Manifold Router (E8).

Tri-objective Ω-router: G₂ coherence × Spin(7) coherence × dimensional projection.

Three objectives are evaluated for every routing request:
  1. G₂ coherence   — envelope.g2_phi_parallel (Ring 6 Fano plane, I6 Sentinel Gate)
  2. Spin(7) coherence — spin7_phi_parallel(envelope) (8D Cayley 4-form gate)
  3. Dimensional projection — DimensionalProjectionService.project(request)

Decision:
  ADMIT    — all three pass, no structural contradictions in projection
  ADVISORY — all three pass, but CLASS_2/CLASS_3 contradictions present in projection
  BLOCK    — any objective fails or projection yields a CLASS_1 block

Ontology alignment (locked — no deprecated names):
  Gradient Field      = L2
  Alexandrian Lexicon = L5
  State Manifold      = L6
  Alexandrian Archive = L7
  Lineage Fabric      = L8
  Narrative           = L10

Invariants enforced:
  I1  Never writes to Canon
  I2  _receipts list grows monotonically; never pruned
  I5  Pure evaluation — no side effects on domain state
  I6  G₂ failure → BLOCK with omega_router_g2_coherence_block receipt
  I7  Deterministic — same request always yields same decision
  I10 receipts() returns a copy, never the mutable internal list

Tag: cqhml-omega-router-v2
AXIOLEV Holdings LLC © 2026
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from ns.api.schemas.cqhml import DimensionalCoordinate, ProjectionRequest
from ns.domain.models.spin7_invariant import spin7_phi_parallel
from ns.services.cqhml.projection_service import DimensionalProjectionService


class RoutingObjective(str, Enum):
    G2_COHERENCE = "G2_COHERENCE"
    SPIN7_COHERENCE = "SPIN7_COHERENCE"
    DIMENSIONAL_PROJECTION = "DIMENSIONAL_PROJECTION"


class RoutingDecision(str, Enum):
    ADMIT = "ADMIT"
    BLOCK = "BLOCK"
    ADVISORY = "ADVISORY"


@dataclass
class ObjectiveResult:
    objective: RoutingObjective
    passed: bool
    receipts: list[str] = field(default_factory=list)
    detail: str = ""


@dataclass
class OmegaRoutingResult:
    request_id: str
    decision: RoutingDecision
    objectives: list[ObjectiveResult]
    receipts: list[str]
    trace: list[str]
    tick: int
    error: Optional[str] = None
    projected_coordinate: Optional[DimensionalCoordinate] = None
    g2_phi_parallel: bool = False
    spin7_phi_parallel: bool = False
    projection_success: bool = False


class OmegaManifoldRouter:
    """Tri-objective Omega manifold router.

    Evaluates G₂ coherence, Spin(7) coherence, and dimensional projection
    in sequence. All three must pass for an ADMIT decision.

    I1: never writes to Canon.
    I2: _receipts grows monotonically, never pruned.
    """

    def __init__(self) -> None:
        self._projection_svc = DimensionalProjectionService()
        self._receipts: list[str] = []

    def route(self, request: ProjectionRequest) -> OmegaRoutingResult:
        """Route a ProjectionRequest through all three manifold objectives."""
        envelope = request.envelope
        tick = request.tick if request.tick else envelope.tick
        trace: list[str] = []
        all_receipts: list[str] = []
        objectives: list[ObjectiveResult] = []

        # ------------------------------------------------------------------
        # Objective 1: G₂ coherence
        # I6: g2_phi_parallel=False on envelope is a sentinel gate block
        # ------------------------------------------------------------------
        g2_pass = bool(envelope.g2_phi_parallel)
        g2_receipts = (
            ["omega_router_g2_coherence_pass"] if g2_pass
            else ["omega_router_g2_coherence_block"]
        )
        objectives.append(ObjectiveResult(
            objective=RoutingObjective.G2_COHERENCE,
            passed=g2_pass,
            receipts=g2_receipts,
            detail="envelope.g2_phi_parallel — Ring 6 G₂ 3-form coherence gate",
        ))
        all_receipts.extend(g2_receipts)
        trace.append(f"obj1_g2_coherence: {'pass' if g2_pass else 'block'}")

        # ------------------------------------------------------------------
        # Objective 2: Spin(7) coherence
        # Checks envelope.spin7_coherent via nabla_phi_4_zero
        # ------------------------------------------------------------------
        spin7_pass = spin7_phi_parallel(envelope)
        spin7_receipts = (
            ["omega_router_spin7_coherence_pass"] if spin7_pass
            else ["omega_router_spin7_coherence_block"]
        )
        objectives.append(ObjectiveResult(
            objective=RoutingObjective.SPIN7_COHERENCE,
            passed=spin7_pass,
            receipts=spin7_receipts,
            detail="spin7_phi_parallel(envelope) — Spin(7) Cayley 4-form coherence gate",
        ))
        all_receipts.extend(spin7_receipts)
        trace.append(f"obj2_spin7_coherence: {'pass' if spin7_pass else 'block'}")

        # ------------------------------------------------------------------
        # Objective 3: Dimensional projection
        # ------------------------------------------------------------------
        proj_result = self._projection_svc.project(request)
        proj_pass = proj_result.success
        proj_receipts = (
            ["omega_router_projection_pass"] if proj_pass
            else ["omega_router_projection_block"]
        )
        objectives.append(ObjectiveResult(
            objective=RoutingObjective.DIMENSIONAL_PROJECTION,
            passed=proj_pass,
            receipts=proj_receipts,
            detail=proj_result.error or "projection_success",
        ))
        all_receipts.extend(proj_receipts)
        all_receipts.extend(proj_result.receipts_emitted)
        trace.append(f"obj3_projection: {'pass' if proj_pass else 'block'}")
        trace.extend(proj_result.trace)

        # ------------------------------------------------------------------
        # Joint decision
        # ------------------------------------------------------------------
        blocking = not g2_pass or not spin7_pass or not proj_pass

        if blocking:
            decision = RoutingDecision.BLOCK
            decision_receipts = ["omega_router_block"]
            if not g2_pass:
                error: Optional[str] = (
                    "I6: G₂ coherence block — envelope.g2_phi_parallel is False"
                )
            elif not spin7_pass:
                error = "Spin(7) coherence block — spin7_phi_parallel returned False"
            else:
                error = proj_result.error or "Dimensional projection failed"
        else:
            advisory = "cqhml_projection_advisory_contradictions" in proj_result.receipts_emitted
            if advisory:
                decision = RoutingDecision.ADVISORY
                decision_receipts = ["omega_router_advisory"]
            else:
                decision = RoutingDecision.ADMIT
                decision_receipts = ["omega_router_admit"]
            error = None

        all_receipts.extend(decision_receipts)
        self._receipts.extend(all_receipts)

        return OmegaRoutingResult(
            request_id=request.request_id,
            decision=decision,
            objectives=objectives,
            receipts=all_receipts,
            trace=trace,
            tick=tick,
            error=error,
            projected_coordinate=proj_result.projected_coordinate,
            g2_phi_parallel=g2_pass,
            spin7_phi_parallel=spin7_pass,
            projection_success=proj_pass,
        )

    def receipts(self) -> list[str]:
        """I2/I10: append-only snapshot of all receipts emitted."""
        return list(self._receipts)
