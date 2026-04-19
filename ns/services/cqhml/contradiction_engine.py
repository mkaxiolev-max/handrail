"""NS∞ CQHML Manifold Engine — Dimensional Contradiction Engine (E5).

Seven detectors scan story atoms and dimensional envelopes for structural
contradictions across the 10-layer ontology stack.

Ontology alignment (locked — no deprecated names):
  Gradient Field      = L2
  Alexandrian Lexicon = L5
  State Manifold      = L6
  Alexandrian Archive = L7
  Lineage Fabric      = L8
  Narrative           = L10

Invariants enforced:
  I1  Canon precedes Conversion — engine never writes to Canon
  I2  Append-only — tick regression is a class-1 contradiction
  I5  Provenance inertness — hash mismatch is a class-1 contradiction
  I6  Sentinel Gate — phi_parallel=False on L1 is a class-2 contradiction
  I7  Bisimulation with replay — replay consistency checked by detector 7
  I10 Supersession monotone — lineage shrinkage is a class-2 contradiction

Tag: cqhml-contradiction-engine-v2
AXIOLEV Holdings LLC © 2026
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from ns.api.schemas.cqhml import (
    DimensionalCoordinate,
    DimensionalEnvelope,
    ObserverFrame,
    SemanticMode,
)
from ns.domain.models.g2_invariant import ring6_phi_parallel
from ns.services.cqhml.quaternion import phi_coherent
from ns.services.cqhml.story_atom_loom import StoryAtom

# ---------------------------------------------------------------------------
# Layer → canonical SemanticMode mapping (must match story_atom_loom.py)
# ---------------------------------------------------------------------------
_CANONICAL_MODE: dict[int, SemanticMode] = {
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


# ---------------------------------------------------------------------------
# Contradiction types (7 detectors)
# ---------------------------------------------------------------------------

class ContradictionType(str, Enum):
    TICK_REGRESSION = "TICK_REGRESSION"                   # Detector 1 — I2
    PROVENANCE_VIOLATION = "PROVENANCE_VIOLATION"         # Detector 2 — I5
    PHI_INCOHERENCE = "PHI_INCOHERENCE"                   # Detector 3 — I6, G₂
    SEMANTIC_MODE_CONFLICT = "SEMANTIC_MODE_CONFLICT"     # Detector 4 — layer/mode mismatch
    LAYER_CONFLICT = "LAYER_CONFLICT"                     # Detector 5 — same-tick same-content different-layer
    LINEAGE_SHRINKAGE = "LINEAGE_SHRINKAGE"               # Detector 6 — I10
    REPLAY_INCONSISTENCY = "REPLAY_INCONSISTENCY"         # Detector 7 — I7


class ContradictionSeverity(str, Enum):
    CLASS_1 = "CLASS_1"   # Blocking — must be resolved before Canon promotion
    CLASS_2 = "CLASS_2"   # Structural — weakens manifold coherence
    CLASS_3 = "CLASS_3"   # Advisory — logged but not blocking


@dataclass
class ContradictionResult:
    """A single detected contradiction."""

    contradiction_type: ContradictionType
    severity: ContradictionSeverity
    description: str
    atom_ids: list[str] = field(default_factory=list)
    layer: Optional[int] = None
    receipt: str = ""

    def __post_init__(self) -> None:
        if not self.receipt:
            self.receipt = f"cqhml_contradiction_{self.contradiction_type.value.lower()}"


@dataclass
class ContradictionReport:
    """Aggregate result of all 7 detectors over a sequence of story atoms.

    I2/I10: receipts list is append-only once returned — callers must not mutate.
    """

    contradictions: list[ContradictionResult]
    atom_count: int
    receipts: list[str]
    g2_coherent: bool
    clean: bool  # True iff no CLASS_1 or CLASS_2 contradictions detected

    @property
    def blocking(self) -> list[ContradictionResult]:
        return [c for c in self.contradictions if c.severity == ContradictionSeverity.CLASS_1]

    @property
    def structural(self) -> list[ContradictionResult]:
        return [c for c in self.contradictions if c.severity == ContradictionSeverity.CLASS_2]


# ---------------------------------------------------------------------------
# Detector helpers
# ---------------------------------------------------------------------------

def _sha256(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Contradiction Engine
# ---------------------------------------------------------------------------

class DimensionalContradictionEngine:
    """Seven-detector dimensional contradiction engine for CQHML story atoms.

    Detectors:
      1. TickRegressionDetector    — I2 append-only (CLASS_1)
      2. ProvenanceViolationDetector — I5 hash-chain (CLASS_1)
      3. PhiIncoherenceDetector    — I6 + G₂ 3-form (CLASS_2)
      4. SemanticModeConflictDetector — layer/mode canonical mismatch (CLASS_3)
      5. LayerConflictDetector     — same-tick duplicate-content on different layers (CLASS_2)
      6. LineageShrinkageDetector  — I10 lineage_refs monotone (CLASS_2)
      7. ReplayInconsistencyDetector — I7 bisimulation / tick-hash replay (CLASS_1)

    All detectors are pure / side-effect-free (I5).
    """

    def __init__(self) -> None:
        self._receipts: list[str] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def scan(self, atoms: list[StoryAtom]) -> ContradictionReport:
        """Run all 7 detectors over a sequence of story atoms.

        I1: does not write to Canon.
        I2: _receipts only grows.
        """
        found: list[ContradictionResult] = []

        found.extend(self._detect_tick_regression(atoms))
        found.extend(self._detect_provenance_violations(atoms))
        found.extend(self._detect_phi_incoherence(atoms))
        found.extend(self._detect_semantic_mode_conflicts(atoms))
        found.extend(self._detect_layer_conflicts(atoms))
        found.extend(self._detect_lineage_shrinkage(atoms))
        found.extend(self._detect_replay_inconsistency(atoms))

        receipts_this_scan: list[str] = []
        if found:
            receipts_this_scan.append("cqhml_contradiction_scan_found")
            for c in found:
                receipts_this_scan.append(c.receipt)
        else:
            receipts_this_scan.append("cqhml_contradiction_scan_clean")

        # G₂ coherence — check all atoms' phi_parallel flags
        g2_coherent = all(a.phi_parallel for a in atoms) if atoms else True

        self._receipts.extend(receipts_this_scan)

        clean = not any(
            c.severity in (ContradictionSeverity.CLASS_1, ContradictionSeverity.CLASS_2)
            for c in found
        )

        return ContradictionReport(
            contradictions=found,
            atom_count=len(atoms),
            receipts=list(receipts_this_scan),
            g2_coherent=g2_coherent,
            clean=clean,
        )

    def scan_envelope(self, envelope: DimensionalEnvelope) -> ContradictionReport:
        """Scan a single DimensionalEnvelope for phi and layer integrity.

        Builds a synthetic single-atom sequence for uniform detector routing.
        """
        coord = envelope.coordinate
        observer = envelope.observer

        found: list[ContradictionResult] = []

        # Phi incoherence on envelope
        if not envelope.g2_phi_parallel:
            found.append(ContradictionResult(
                contradiction_type=ContradictionType.PHI_INCOHERENCE,
                severity=ContradictionSeverity.CLASS_2,
                description=(
                    f"DimensionalEnvelope g2_phi_parallel=False on layer {coord.layer}"
                ),
                layer=coord.layer,
                receipt="cqhml_contradiction_phi_incoherence",
            ))

        # Semantic mode conflict on envelope coordinate
        expected = _CANONICAL_MODE.get(coord.layer)
        # For envelope scans, mode is taken from observer.semantic_mode
        if expected is not None and observer.semantic_mode != expected:
            found.append(ContradictionResult(
                contradiction_type=ContradictionType.SEMANTIC_MODE_CONFLICT,
                severity=ContradictionSeverity.CLASS_3,
                description=(
                    f"Observer semantic_mode {observer.semantic_mode!r} does not match "
                    f"canonical mode {expected!r} for layer {coord.layer}"
                ),
                layer=coord.layer,
                receipt="cqhml_contradiction_semantic_mode_conflict",
            ))

        clean = not any(
            c.severity in (ContradictionSeverity.CLASS_1, ContradictionSeverity.CLASS_2)
            for c in found
        )
        receipts: list[str] = (
            ["cqhml_contradiction_scan_found"] + [c.receipt for c in found]
            if found else ["cqhml_contradiction_scan_clean"]
        )
        self._receipts.extend(receipts)

        return ContradictionReport(
            contradictions=found,
            atom_count=0,
            receipts=receipts,
            g2_coherent=envelope.g2_phi_parallel,
            clean=clean,
        )

    def receipts(self) -> list[str]:
        """I2/I10: append-only snapshot of all receipts emitted."""
        return list(self._receipts)

    # ------------------------------------------------------------------
    # Detector 1 — Tick Regression (I2)
    # ------------------------------------------------------------------

    @staticmethod
    def _detect_tick_regression(atoms: list[StoryAtom]) -> list[ContradictionResult]:
        results: list[ContradictionResult] = []
        for i in range(1, len(atoms)):
            if atoms[i].tick < atoms[i - 1].tick:
                results.append(ContradictionResult(
                    contradiction_type=ContradictionType.TICK_REGRESSION,
                    severity=ContradictionSeverity.CLASS_1,
                    description=(
                        f"I2 violation: tick regression at index {i} "
                        f"({atoms[i - 1].tick} → {atoms[i].tick})"
                    ),
                    atom_ids=[atoms[i - 1].atom_id, atoms[i].atom_id],
                    layer=atoms[i].layer,
                ))
        return results

    # ------------------------------------------------------------------
    # Detector 2 — Provenance Violation (I5)
    # ------------------------------------------------------------------

    @staticmethod
    def _detect_provenance_violations(atoms: list[StoryAtom]) -> list[ContradictionResult]:
        results: list[ContradictionResult] = []
        for atom in atoms:
            if not atom.verify_provenance():
                results.append(ContradictionResult(
                    contradiction_type=ContradictionType.PROVENANCE_VIOLATION,
                    severity=ContradictionSeverity.CLASS_1,
                    description=(
                        f"I5 violation: provenance hash mismatch on atom {atom.atom_id} "
                        f"(layer={atom.layer})"
                    ),
                    atom_ids=[atom.atom_id],
                    layer=atom.layer,
                ))
        return results

    # ------------------------------------------------------------------
    # Detector 3 — Phi Incoherence (I6, G₂)
    # ------------------------------------------------------------------

    @staticmethod
    def _detect_phi_incoherence(atoms: list[StoryAtom]) -> list[ContradictionResult]:
        results: list[ContradictionResult] = []
        for atom in atoms:
            if not atom.phi_parallel:
                sev = (
                    ContradictionSeverity.CLASS_1
                    if atom.layer == 1
                    else ContradictionSeverity.CLASS_2
                )
                results.append(ContradictionResult(
                    contradiction_type=ContradictionType.PHI_INCOHERENCE,
                    severity=sev,
                    description=(
                        f"G₂ incoherence: phi_parallel=False on atom {atom.atom_id} "
                        f"(layer={atom.layer})"
                    ),
                    atom_ids=[atom.atom_id],
                    layer=atom.layer,
                ))
        return results

    # ------------------------------------------------------------------
    # Detector 4 — Semantic Mode Conflict
    # ------------------------------------------------------------------

    @staticmethod
    def _detect_semantic_mode_conflicts(atoms: list[StoryAtom]) -> list[ContradictionResult]:
        results: list[ContradictionResult] = []
        for atom in atoms:
            expected = _CANONICAL_MODE.get(atom.layer)
            if expected is not None and atom.semantic_mode != expected:
                results.append(ContradictionResult(
                    contradiction_type=ContradictionType.SEMANTIC_MODE_CONFLICT,
                    severity=ContradictionSeverity.CLASS_3,
                    description=(
                        f"SemanticMode mismatch on atom {atom.atom_id}: "
                        f"expected {expected!r} for layer {atom.layer}, "
                        f"got {atom.semantic_mode!r}"
                    ),
                    atom_ids=[atom.atom_id],
                    layer=atom.layer,
                ))
        return results

    # ------------------------------------------------------------------
    # Detector 5 — Layer Conflict (same tick, same content, different layer)
    # ------------------------------------------------------------------

    @staticmethod
    def _detect_layer_conflicts(atoms: list[StoryAtom]) -> list[ContradictionResult]:
        results: list[ContradictionResult] = []
        # Group by (tick, content_hash) → collect atom_ids and layers
        groups: dict[tuple[int, str], list[StoryAtom]] = {}
        for atom in atoms:
            key = (atom.tick, atom.provenance_hash)
            groups.setdefault(key, []).append(atom)

        for (tick, _phash), group in groups.items():
            layers = {a.layer for a in group}
            if len(layers) > 1:
                ids = [a.atom_id for a in group]
                results.append(ContradictionResult(
                    contradiction_type=ContradictionType.LAYER_CONFLICT,
                    severity=ContradictionSeverity.CLASS_2,
                    description=(
                        f"Layer conflict at tick={tick}: identical content "
                        f"appears on layers {sorted(layers)}"
                    ),
                    atom_ids=ids,
                    layer=None,
                ))
        return results

    # ------------------------------------------------------------------
    # Detector 6 — Lineage Shrinkage (I10)
    # ------------------------------------------------------------------

    @staticmethod
    def _detect_lineage_shrinkage(atoms: list[StoryAtom]) -> list[ContradictionResult]:
        """I10: lineage_refs must be monotonically non-shrinking across ticks.

        For atoms sharing the same atom_id across ticks, lineage_refs must only grow.
        For atoms sharing the same content-hash, lineage set must not lose members.
        """
        results: list[ContradictionResult] = []
        # Track lineage by content hash across ascending ticks
        lineage_by_hash: dict[str, set[str]] = {}
        seen_by_hash: dict[str, StoryAtom] = {}

        for atom in sorted(atoms, key=lambda a: a.tick):
            ph = atom.provenance_hash
            current_refs = set(atom.lineage_refs)

            if ph in lineage_by_hash:
                prev_refs = lineage_by_hash[ph]
                if not prev_refs.issubset(current_refs):
                    lost = prev_refs - current_refs
                    results.append(ContradictionResult(
                        contradiction_type=ContradictionType.LINEAGE_SHRINKAGE,
                        severity=ContradictionSeverity.CLASS_2,
                        description=(
                            f"I10 violation: lineage shrinkage on atom {atom.atom_id} "
                            f"(tick={atom.tick}): lost refs {sorted(lost)}"
                        ),
                        atom_ids=[seen_by_hash[ph].atom_id, atom.atom_id],
                        layer=atom.layer,
                    ))
                # Union — keep all refs seen so far (monotone)
                lineage_by_hash[ph] = prev_refs | current_refs
            else:
                lineage_by_hash[ph] = current_refs
                seen_by_hash[ph] = atom

        return results

    # ------------------------------------------------------------------
    # Detector 7 — Replay Inconsistency (I7)
    # ------------------------------------------------------------------

    @staticmethod
    def _detect_replay_inconsistency(atoms: list[StoryAtom]) -> list[ContradictionResult]:
        """I7 bisimulation with replay: if two atoms share atom_id, content must be identical.

        An atom_id identifies a unique narrative unit.  Replaying the same id
        with different content indicates a non-deterministic or corrupted replay.
        """
        results: list[ContradictionResult] = []
        seen: dict[str, StoryAtom] = {}

        for atom in atoms:
            if atom.atom_id in seen:
                prior = seen[atom.atom_id]
                if prior.provenance_hash != atom.provenance_hash:
                    results.append(ContradictionResult(
                        contradiction_type=ContradictionType.REPLAY_INCONSISTENCY,
                        severity=ContradictionSeverity.CLASS_1,
                        description=(
                            f"I7 violation: replay inconsistency — atom_id {atom.atom_id} "
                            f"has differing content at tick {prior.tick} vs {atom.tick}"
                        ),
                        atom_ids=[atom.atom_id],
                        layer=atom.layer,
                    ))
            else:
                seen[atom.atom_id] = atom

        return results
