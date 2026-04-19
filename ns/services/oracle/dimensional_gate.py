"""NS∞ CQHML Oracle Dimensional Gate (E9).

Bridges the CQHML Ω-manifold router with the Oracle v2 adjudicator.

Pipeline per request:
  1. OmegaManifoldRouter.route(projection_request) → RoutingDecision
  2. Map RoutingDecision → IntegrityRouteEffect + ConstitutionalContext
  3. OracleAdjudicator.adjudicate(oracle_req) → OracleAdjudicationResponse
  4. Emit combined receipts; return DimensionalGateResult.

Routing → IntegrityRouteEffect mapping:
  ADMIT    → PASS  → OracleDecision.ALLOW
  ADVISORY → WARN  → OracleDecision.DEFER
  BLOCK    → BLOCK → OracleDecision.DENY

Ontology alignment (locked — no deprecated names):
  Gradient Field      = L2
  Alexandrian Lexicon = L5
  State Manifold      = L6
  Alexandrian Archive = L7
  Lineage Fabric      = L8
  Narrative           = L10

Invariants enforced:
  I1  Never writes to Canon
  I2  _receipts grows monotonically, never pruned
  I5  Pure evaluation — no side effects on domain state
  I6  G₂ failure → routing BLOCK → oracle DENY
  I7  Deterministic — same request always yields same decision
  I10 receipts() returns a copy, never the mutable internal list

Tag: cqhml-oracle-dim-gate-v2
AXIOLEV Holdings LLC © 2026
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from ns.api.schemas.common import IntegrityRouteEffect
from ns.api.schemas.cqhml import DimensionalCoordinate, ProjectionRequest
from ns.api.schemas.oracle import (
    ConstitutionalContext,
    HandrailExecutionEnvelope,
    OracleAdjudicationRequest,
    OracleAdjudicationResponse,
    OracleDecision,
    OracleSeverity,
)
from ns.services.omega.manifold_router import (
    OmegaManifoldRouter,
    OmegaRoutingResult,
    RoutingDecision,
)
from ns.services.oracle import adjudicator as oracle_adjudicator


@dataclass
class DimensionalGateResult:
    """Combined result from the dimensional gate pipeline."""

    request_id: str
    routing_decision: RoutingDecision
    oracle_decision: OracleDecision
    oracle_severity: OracleSeverity
    g2_phi_parallel: bool
    spin7_phi_parallel: bool
    projection_success: bool
    receipts: list[str]
    trace: list[str]
    tick: int
    routing_result: OmegaRoutingResult = field(repr=False)
    adjudication_response: OracleAdjudicationResponse = field(repr=False)
    error: Optional[str] = None
    projected_coordinate: Optional[DimensionalCoordinate] = None


# ---------------------------------------------------------------------------
# Routing → RIL route effect mapping
# ---------------------------------------------------------------------------

_ROUTING_TO_RIL: dict[RoutingDecision, IntegrityRouteEffect] = {
    RoutingDecision.ADMIT: IntegrityRouteEffect.PASS,
    RoutingDecision.ADVISORY: IntegrityRouteEffect.WARN,
    RoutingDecision.BLOCK: IntegrityRouteEffect.BLOCK,
}


class OracleDimensionalGate:
    """Oracle dimensional gate — joins Ω-router with Oracle v2 adjudicator.

    I1: never writes to Canon.
    I2: _receipts grows monotonically, never pruned.
    """

    def __init__(self) -> None:
        self._router = OmegaManifoldRouter()
        self._receipts: list[str] = []

    def evaluate(
        self,
        projection_request: ProjectionRequest,
        handrail_envelope: Optional[HandrailExecutionEnvelope] = None,
        oracle_context: Optional[dict] = None,
    ) -> DimensionalGateResult:
        """Evaluate a dimensional projection through the full gate pipeline."""
        request_id = projection_request.request_id
        tick = projection_request.tick or projection_request.envelope.tick
        all_receipts: list[str] = []
        trace: list[str] = []

        # Step 1: route through OmegaManifoldRouter
        routing_result = self._router.route(projection_request)
        all_receipts.extend(routing_result.receipts)
        trace.extend(routing_result.trace)
        trace.append(
            f"dim_gate_routing_decision: {routing_result.decision.value}"
        )

        # Step 2: build oracle adjudication request
        ril_effect = _ROUTING_TO_RIL[routing_result.decision]

        constitutional_ctx = ConstitutionalContext(
            invariants_checked=["I1", "I2", "I5", "I6", "I7", "I10"],
            never_events_screened=[],
            dignity_kernel_invoked=True,
            g2_phi_parallel=routing_result.g2_phi_parallel,
        )

        if handrail_envelope is None:
            handrail_envelope = HandrailExecutionEnvelope(
                scope="LOCAL",
                risk_tier="R0",
                yubikey_verified=False,
            )

        oracle_req = OracleAdjudicationRequest(
            request_id=request_id,
            tick=tick,
            envelope=handrail_envelope,
            constitutional_context=constitutional_ctx,
            ril_route_effect=ril_effect,
            ril_aggregate_score=1.0 if routing_result.decision == RoutingDecision.ADMIT else 0.0,
            context=oracle_context or {},
        )

        # Step 3: oracle adjudication
        oracle_response = oracle_adjudicator.adjudicate(oracle_req)
        all_receipts.extend(oracle_response.receipts_emitted)
        all_receipts.append(
            f"dim_gate_oracle_decision_{oracle_response.decision.value.lower()}"
        )
        trace.extend(oracle_response.trace)
        trace.append(
            f"dim_gate_oracle_severity: {oracle_response.severity.value}"
        )

        # Step 4: combined receipt
        gate_receipt = (
            "dim_gate_pass"
            if oracle_response.decision == OracleDecision.ALLOW
            else "dim_gate_block"
            if oracle_response.decision == OracleDecision.DENY
            else "dim_gate_defer"
        )
        all_receipts.append(gate_receipt)
        self._receipts.extend(all_receipts)

        return DimensionalGateResult(
            request_id=request_id,
            routing_decision=routing_result.decision,
            oracle_decision=oracle_response.decision,
            oracle_severity=oracle_response.severity,
            g2_phi_parallel=routing_result.g2_phi_parallel,
            spin7_phi_parallel=routing_result.spin7_phi_parallel,
            projection_success=routing_result.projection_success,
            receipts=list(all_receipts),
            trace=trace,
            tick=tick,
            routing_result=routing_result,
            adjudication_response=oracle_response,
            error=routing_result.error,
            projected_coordinate=routing_result.projected_coordinate,
        )

    def receipts(self) -> list[str]:
        """I2/I10: append-only snapshot of all receipts emitted."""
        return list(self._receipts)
