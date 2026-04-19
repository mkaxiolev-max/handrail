"""NS∞ CQHML Manifold Engine — Dimensional Projection Service (E6).

Projects dimensional envelopes across ontology layers using the Story Atom
Loom and Dimensional Contradiction Engine.

Ontology alignment (locked — no deprecated names):
  Gradient Field      = L2
  Alexandrian Lexicon = L5
  State Manifold      = L6
  Alexandrian Archive = L7
  Lineage Fabric      = L8
  Narrative           = L10

Invariants enforced:
  I1  Canon precedes Conversion — service never writes to Canon
  I2  Append-only — receipts only grow; ticks respected
  I5  Provenance inertness — all atoms verified before projection
  I6  Sentinel Gate soundness — L1 phi_parallel=False → constitutional block
  I7  Bisimulation with replay — contradiction engine checks replay consistency
  I10 Supersession monotone — lineage_refs extend, never shrink

Tag: cqhml-projection-service-v2
AXIOLEV Holdings LLC © 2026
"""
from __future__ import annotations

from ns.api.schemas.cqhml import (
    DimensionalCoordinate,
    PolicyMode,
    ProjectionRequest,
    ProjectionResult,
    SemanticMode,
)
from ns.services.cqhml.contradiction_engine import (
    ContradictionSeverity,
    DimensionalContradictionEngine,
)
from ns.services.cqhml.story_atom_loom import StoryAtom, StoryAtomLoom

# Layer → canonical SemanticMode (mirrors story_atom_loom / contradiction_engine)
_LAYER_MODE: dict[int, SemanticMode] = {
    1: SemanticMode.CONSTITUTIONAL,
    2: SemanticMode.GRADIENT,
    3: SemanticMode.INTAKE,
    4: SemanticMode.CONVERSION,
    5: SemanticMode.LEXICAL,
    6: SemanticMode.STATE,
    7: SemanticMode.MEMORY,
    8: SemanticMode.LINEAGE,
    9: SemanticMode.ERROR,
    10: SemanticMode.NARRATIVE,
}


class DimensionalProjectionService:
    """Projects DimensionalEnvelopes across ontology layers.

    Pipeline per request:
      1. Scan envelope for contradictions (I5, I6, I7).
      2. CLASS_1 contradictions block the projection immediately.
      3. Build synthetic StoryAtom from envelope coordinate.
      4. I6 Sentinel Gate — L1 atom with phi_parallel=False → constitutional block.
      5. Loom.project_atom() → projected StoryAtom on target layer.
      6. Derive projected DimensionalCoordinate + G₂ coherence flag.
      7. Emit receipts; return ProjectionResult.

    I1: never writes to Canon.
    I2: _receipts list grows monotonically; never pruned.
    """

    def __init__(self) -> None:
        self._loom = StoryAtomLoom()
        self._contradiction_engine = DimensionalContradictionEngine()
        self._receipts: list[str] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def project(self, request: ProjectionRequest) -> ProjectionResult:
        """Execute a dimensional projection request.

        Returns ProjectionResult with success=False if CLASS_1 contradictions
        are found or I6 Sentinel Gate fires.
        """
        envelope = request.envelope
        source_layer = envelope.coordinate.layer
        target_layer = request.target_layer
        tick = request.tick if request.tick else envelope.tick

        # Step 1: contradiction scan of envelope
        contradiction_report = self._contradiction_engine.scan_envelope(envelope)

        trace: list[str] = []
        receipts: list[str] = []

        # Step 2: CLASS_1 blocks
        if contradiction_report.blocking:
            msg = (
                f"CLASS_1 contradiction blocks projection: "
                f"{contradiction_report.blocking[0].contradiction_type.value}"
            )
            receipts.append("cqhml_projection_blocked_class1_contradiction")
            receipts.extend(contradiction_report.receipts)
            self._receipts.extend(receipts)
            return ProjectionResult(
                request_id=request.request_id,
                success=False,
                source_layer=source_layer,
                target_layer=target_layer,
                g2_phi_parallel=False,
                receipts_emitted=receipts,
                trace=trace + [f"blocked: {msg}"],
                tick=tick,
                error=msg,
            )

        # Step 3: build synthetic atom from envelope coordinate
        semantic_mode = (
            request.semantic_mode
            or _LAYER_MODE.get(source_layer, SemanticMode.GRADIENT)
        )
        content = f"projection:{request.request_id}:{source_layer}:{tick}"
        atom = StoryAtom.create(
            content=content,
            layer=source_layer,
            tick=tick,
            semantic_mode=semantic_mode,
            phi_parallel=envelope.coordinate.phi_parallel,
        )

        # Step 4: I6 Sentinel Gate — L1 with phi_parallel=False
        if atom.layer == 1 and not atom.phi_parallel:
            receipts.append("cqhml_projection_constitutional_block")
            self._receipts.extend(receipts)
            return ProjectionResult(
                request_id=request.request_id,
                success=False,
                source_layer=source_layer,
                target_layer=target_layer,
                g2_phi_parallel=False,
                receipts_emitted=receipts,
                trace=["I6: Sentinel Gate — phi_parallel=False on L1 constitutional block"],
                tick=tick,
                error="I6: Sentinel Gate blocks L1 atom with phi_parallel=False",
            )

        # Step 5: loom projection
        projected_atom = self._loom.project_atom(atom, target_layer)

        # Step 6: projected coordinate + G₂ coherence
        projected_coord = DimensionalCoordinate(
            layer=target_layer,
            axis=envelope.coordinate.axis,
            tick=tick,
            phi_parallel=projected_atom.phi_parallel,
            magnitude=envelope.coordinate.magnitude,
        )

        g2 = projected_atom.phi_parallel and envelope.g2_phi_parallel

        # Step 7: emit receipts
        receipts.append("cqhml_projection_success")
        if g2:
            receipts.append("ring6_g2_invariant_checked")
        if contradiction_report.contradictions:
            receipts.append("cqhml_projection_advisory_contradictions")
        receipts.extend(contradiction_report.receipts)
        if envelope.observer.policy_mode == PolicyMode.AUDIT:
            receipts.append("cqhml_audit_trace_emitted")

        trace.append(f"layer_path: {source_layer} → {target_layer}")
        trace.append(f"semantic_mode: {semantic_mode.value}")
        trace.append(f"g2_phi_parallel: {g2}")
        if envelope.observer.policy_mode == PolicyMode.AUDIT:
            trace.append(f"observer_frame: {envelope.observer.frame_id}")

        self._receipts.extend(receipts)

        return ProjectionResult(
            request_id=request.request_id,
            success=True,
            projected_coordinate=projected_coord,
            source_layer=source_layer,
            target_layer=target_layer,
            g2_phi_parallel=g2,
            receipts_emitted=receipts,
            trace=trace,
            tick=tick,
            error=None,
        )

    def receipts(self) -> list[str]:
        """I2/I10: append-only snapshot of all receipts emitted."""
        return list(self._receipts)
