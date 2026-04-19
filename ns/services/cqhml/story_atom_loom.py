"""NS∞ CQHML Manifold Engine — Story Atom Loom (E4).

Weaves story atoms across ontology layers using quaternion layer rotations.
Story atoms are the fundamental narrative units of the CQHML manifold.

Ontology alignment:
  L2 (Gradient Field) → atom ingestion
  L4 (The Loom)       → this module; reflector functor toward narrative form
  L10 (Narrative)     → canonical weave target

Invariants enforced:
  I1  Canon precedes Conversion — loom never writes Canon directly
  I2  Append-only — ticks monotonically non-decreasing, receipts never pruned
  I5  Provenance inertness — SHA-256 hash-chain on each atom
  I6  Sentinel Gate soundness — L1 atoms with phi_parallel=False are blocked
  I10 Supersession monotone — lineage_refs only grow, never shrink

Tag: cqhml-story-atom-loom-v2
AXIOLEV Holdings LLC © 2026
"""
from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass, field
from typing import Optional

from ns.api.schemas.cqhml import (
    ObserverFrame,
    PolicyMode,
    SemanticMode,
)
from ns.domain.models.g2_invariant import ring6_phi_parallel
from ns.services.cqhml.quaternion import (
    Quaternion,
    compose_layer_path,
    ensure_positive_hemisphere,
    identity,
    layer_rotation,
    phi_coherent,
)

# L10 = Ω-Link Narrative Interface (canonical weave target)
_NARRATIVE_LAYER: int = 10
# L2 = Gradient Field (canonical atom ingestion layer)
_GRADIENT_LAYER: int = 2

# Layer → SemanticMode canonical mapping
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


@dataclass
class StoryAtom:
    """A single narrative unit in the CQHML manifold.

    I5: provenance_hash = SHA-256(content.encode()).  Never mutable.
    I2: lineage_refs grows only forward; never remove entries.
    """

    atom_id: str
    content: str
    semantic_mode: SemanticMode
    layer: int
    tick: int
    provenance_hash: str
    phi_parallel: bool = True
    lineage_refs: list[str] = field(default_factory=list)

    # ------------------------------------------------------------------
    # Provenance
    # ------------------------------------------------------------------

    @staticmethod
    def _hash_content(content: str) -> str:
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def verify_provenance(self) -> bool:
        """I5: confirm hash-chain integrity."""
        return self.provenance_hash == self._hash_content(self.content)

    # ------------------------------------------------------------------
    # Factory
    # ------------------------------------------------------------------

    @classmethod
    def create(
        cls,
        content: str,
        layer: int,
        tick: int,
        semantic_mode: Optional[SemanticMode] = None,
        phi_parallel: bool = True,
        lineage_refs: Optional[list[str]] = None,
        atom_id: Optional[str] = None,
    ) -> "StoryAtom":
        if not (1 <= layer <= 10):
            raise ValueError(f"layer must be in [1, 10]; got {layer}")
        if tick < 0:
            raise ValueError(f"tick must be >= 0; got {tick}")
        mode = semantic_mode if semantic_mode is not None else _LAYER_MODE.get(layer, SemanticMode.GRADIENT)
        return cls(
            atom_id=atom_id or str(uuid.uuid4()),
            content=content,
            semantic_mode=mode,
            layer=layer,
            tick=tick,
            provenance_hash=cls._hash_content(content),
            phi_parallel=phi_parallel,
            lineage_refs=list(lineage_refs) if lineage_refs else [],
        )


@dataclass
class WovenNarrative:
    """Result of weaving story atoms through the CQHML manifold.

    I2:  atoms list is fixed on creation; receipts/trace are append-only.
    I10: receipts monotonically accumulate; no deletion.
    """

    narrative_id: str
    atoms: list[StoryAtom]
    source_layer: int
    target_layer: int
    rotation_quaternion: Quaternion
    g2_phi_parallel: bool
    tick: int
    receipts: list[str] = field(default_factory=list)
    trace: list[str] = field(default_factory=list)

    @property
    def atom_count(self) -> int:
        return len(self.atoms)

    def coherent(self) -> bool:
        """True iff G₂-coherent: unit quaternion in positive hemisphere."""
        return phi_coherent(self.rotation_quaternion) and self.g2_phi_parallel


class StoryAtomLoom:
    """Weaves story atoms across ontology layers via quaternion rotations.

    The Loom is a reflector functor L : GradientField → Narrative.
    It never writes to Canon directly (I1, I3).

    Digest flow:
      ingest atoms → validate provenance (I5) → check tick monotonicity (I2)
      → sentinel gate (I6) → compute rotation quaternion → emit WovenNarrative
    """

    NARRATIVE_LAYER: int = _NARRATIVE_LAYER
    GRADIENT_LAYER: int = _GRADIENT_LAYER

    def __init__(self) -> None:
        # I10: receipt list grows monotonically, never pruned
        self._receipts: list[str] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def weave(
        self,
        atoms: list[StoryAtom],
        observer: ObserverFrame,
        target_layer: int = _NARRATIVE_LAYER,
    ) -> WovenNarrative:
        """Weave atoms into a dimensional narrative.

        Raises ValueError on I2 tick violation or I5 provenance failure.
        Returns a blocked narrative (with receipt) on I6 sentinel violation.
        """
        if not atoms:
            raise ValueError("Cannot weave an empty atom list")
        if not (1 <= target_layer <= 10):
            raise ValueError(f"target_layer must be in [1, 10]; got {target_layer}")

        # I5: verify all provenance hashes before any computation
        for atom in atoms:
            if not atom.verify_provenance():
                raise ValueError(f"Provenance (I5) violation on atom {atom.atom_id}")

        # I2: ticks must be monotonically non-decreasing
        self._assert_tick_monotonicity(atoms)

        source_layer = atoms[0].layer

        # I6: Sentinel Gate — L1 atoms with phi_parallel=False are blocked
        for atom in atoms:
            if atom.layer == 1 and not atom.phi_parallel:
                blocked = WovenNarrative(
                    narrative_id=str(uuid.uuid4()),
                    atoms=list(atoms),
                    source_layer=source_layer,
                    target_layer=target_layer,
                    rotation_quaternion=layer_rotation(source_layer, target_layer),
                    g2_phi_parallel=False,
                    tick=atoms[-1].tick,
                    receipts=["cqhml_story_atom_constitutional_block"],
                    trace=[f"sentinel_gate: phi_parallel=False on L1 atom {atom.atom_id} → blocked"],
                )
                self._receipts.append("cqhml_story_atom_constitutional_block")
                return blocked

        rotation = self._compute_rotation(atoms, target_layer)
        g2 = phi_coherent(rotation) and ring6_phi_parallel(rotation)

        receipts: list[str] = ["cqhml_story_atom_woven"]
        trace: list[str] = [
            f"woven {len(atoms)} atom(s)",
            f"layer_path: {source_layer} → {target_layer}",
            f"g2_phi_parallel: {g2}",
        ]
        if g2:
            receipts.append("ring6_g2_invariant_checked")
        if observer.policy_mode == PolicyMode.AUDIT:
            receipts.append("cqhml_audit_trace_emitted")
            trace.append(f"observer_frame: {observer.frame_id}")

        self._receipts.extend(receipts)

        return WovenNarrative(
            narrative_id=str(uuid.uuid4()),
            atoms=list(atoms),
            source_layer=source_layer,
            target_layer=target_layer,
            rotation_quaternion=rotation,
            g2_phi_parallel=g2,
            tick=atoms[-1].tick,
            receipts=receipts,
            trace=trace,
        )

    def project_atom(self, atom: StoryAtom, target_layer: int) -> StoryAtom:
        """Project a single story atom to a target layer.

        I5: provenance_hash re-derived from original content.
        I2: tick preserved from source atom.
        I10: lineage_refs extended with source atom_id (monotone growth).
        """
        if not (1 <= target_layer <= 10):
            raise ValueError(f"target_layer must be in [1, 10]; got {target_layer}")
        if not atom.verify_provenance():
            raise ValueError(f"Provenance (I5) violation on atom {atom.atom_id}")

        rotation = layer_rotation(atom.layer, target_layer)
        phi = phi_coherent(ensure_positive_hemisphere(rotation))
        return StoryAtom.create(
            content=atom.content,
            layer=target_layer,
            tick=atom.tick,
            semantic_mode=_LAYER_MODE.get(target_layer, SemanticMode.STATE),
            phi_parallel=phi,
            lineage_refs=list(atom.lineage_refs) + [atom.atom_id],
        )

    def coherence_check(self, narrative: WovenNarrative) -> bool:
        """True iff the narrative passes G₂ + phi coherence (ring6_phi_parallel)."""
        return narrative.coherent() and ring6_phi_parallel(narrative.rotation_quaternion)

    def receipts(self) -> list[str]:
        """I2/I10: return append-only snapshot of all receipts emitted."""
        return list(self._receipts)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _assert_tick_monotonicity(atoms: list[StoryAtom]) -> None:
        for i in range(1, len(atoms)):
            if atoms[i].tick < atoms[i - 1].tick:
                raise ValueError(
                    f"I2 (append-only) violation: tick regression at index {i}: "
                    f"{atoms[i - 1].tick} → {atoms[i].tick}"
                )

    @staticmethod
    def _compute_rotation(atoms: list[StoryAtom], target_layer: int) -> Quaternion:
        """Compose inter-layer quaternion for atom-sequence → target layer path."""
        layers = [a.layer for a in atoms] + [target_layer]
        # Deduplicate consecutive equal layers to form a minimal step sequence
        steps: list[int] = [layers[0]]
        for layer in layers[1:]:
            if layer != steps[-1]:
                steps.append(layer)
        if len(steps) < 2:
            # All atoms and target are on the same layer → identity rotation
            return identity()
        return ensure_positive_hemisphere(compose_layer_path(steps))
