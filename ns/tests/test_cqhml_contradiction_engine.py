"""NS∞ cqhml-P5: DimensionalContradictionEngine — 7 detectors.

Tag: cqhml-contradiction-engine-v2
AXIOLEV Holdings LLC © 2026

Locked ontology:
  Gradient Field (L2), Alexandrian Lexicon (L5), State Manifold (L6),
  Alexandrian Archive (L7), Lineage Fabric (L8), Narrative (L10).
  No deprecated names (Ether, CTF, Storytime-as-layer, Alexandria alone, etc.).
"""
from __future__ import annotations

import hashlib

import pytest

from ns.api.schemas.cqhml import (
    DimensionalCoordinate,
    DimensionalEnvelope,
    ObserverFrame,
    PolicyMode,
    SemanticMode,
)
from ns.services.cqhml.contradiction_engine import (
    ContradictionSeverity,
    ContradictionType,
    DimensionalContradictionEngine,
)
from ns.services.cqhml.story_atom_loom import StoryAtom


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _atom(content: str, layer: int, tick: int, **kw) -> StoryAtom:
    """Create a valid StoryAtom using the factory (provenance computed)."""
    return StoryAtom.create(content=content, layer=layer, tick=tick, **kw)


def _observer(layer: int = 6, mode: SemanticMode = SemanticMode.STATE) -> ObserverFrame:
    return ObserverFrame(
        frame_id="test-frame",
        layer=layer,
        semantic_mode=mode,
        policy_mode=PolicyMode.ENFORCE,
        tick=0,
    )


def _envelope(
    layer: int = 6,
    g2: bool = True,
    observer_mode: SemanticMode = SemanticMode.STATE,
) -> DimensionalEnvelope:
    coord = DimensionalCoordinate(layer=layer, tick=0, phi_parallel=True)
    return DimensionalEnvelope(
        coordinate=coord,
        observer=_observer(layer=layer, mode=observer_mode),
        g2_phi_parallel=g2,
        spin7_coherent=True,
        tick=0,
    )


# ---------------------------------------------------------------------------
# Detector 1 — Tick Regression (I2)
# ---------------------------------------------------------------------------

class TestDetector1TickRegression:
    def test_clean_sequence(self):
        atoms = [_atom("a", 2, 0), _atom("b", 2, 1), _atom("c", 2, 2)]
        engine = DimensionalContradictionEngine()
        report = engine.scan(atoms)
        regressions = [c for c in report.contradictions if c.contradiction_type == ContradictionType.TICK_REGRESSION]
        assert regressions == []

    def test_single_regression(self):
        atoms = [_atom("a", 2, 5), _atom("b", 2, 3)]
        engine = DimensionalContradictionEngine()
        report = engine.scan(atoms)
        regressions = [c for c in report.contradictions if c.contradiction_type == ContradictionType.TICK_REGRESSION]
        assert len(regressions) == 1
        assert regressions[0].severity == ContradictionSeverity.CLASS_1

    def test_multiple_regressions(self):
        atoms = [_atom("a", 2, 10), _atom("b", 2, 5), _atom("c", 2, 2)]
        engine = DimensionalContradictionEngine()
        report = engine.scan(atoms)
        regressions = [c for c in report.contradictions if c.contradiction_type == ContradictionType.TICK_REGRESSION]
        assert len(regressions) == 2

    def test_equal_tick_is_not_regression(self):
        atoms = [_atom("a", 2, 3), _atom("b", 2, 3)]
        engine = DimensionalContradictionEngine()
        report = engine.scan(atoms)
        regressions = [c for c in report.contradictions if c.contradiction_type == ContradictionType.TICK_REGRESSION]
        assert regressions == []


# ---------------------------------------------------------------------------
# Detector 2 — Provenance Violation (I5)
# ---------------------------------------------------------------------------

class TestDetector2ProvenanceViolation:
    def test_clean_atoms(self):
        atoms = [_atom("hello", 5, 0), _atom("world", 7, 1)]
        engine = DimensionalContradictionEngine()
        report = engine.scan(atoms)
        pv = [c for c in report.contradictions if c.contradiction_type == ContradictionType.PROVENANCE_VIOLATION]
        assert pv == []

    def test_tampered_hash(self):
        atom = _atom("original", 6, 0)
        # Tamper the provenance hash directly
        atom.provenance_hash = "deadbeef" * 8
        engine = DimensionalContradictionEngine()
        report = engine.scan([atom])
        pv = [c for c in report.contradictions if c.contradiction_type == ContradictionType.PROVENANCE_VIOLATION]
        assert len(pv) == 1
        assert pv[0].severity == ContradictionSeverity.CLASS_1

    def test_tampered_content(self):
        atom = _atom("original", 6, 0)
        atom.content = "tampered"  # hash no longer matches
        engine = DimensionalContradictionEngine()
        report = engine.scan([atom])
        pv = [c for c in report.contradictions if c.contradiction_type == ContradictionType.PROVENANCE_VIOLATION]
        assert len(pv) == 1


# ---------------------------------------------------------------------------
# Detector 3 — Phi Incoherence (I6, G₂)
# ---------------------------------------------------------------------------

class TestDetector3PhiIncoherence:
    def test_phi_parallel_true_no_contradiction(self):
        atom = _atom("ok", 2, 0, phi_parallel=True)
        engine = DimensionalContradictionEngine()
        report = engine.scan([atom])
        phi = [c for c in report.contradictions if c.contradiction_type == ContradictionType.PHI_INCOHERENCE]
        assert phi == []

    def test_phi_false_on_l1_is_class1(self):
        atom = _atom("constitutional", 1, 0, phi_parallel=False)
        engine = DimensionalContradictionEngine()
        report = engine.scan([atom])
        phi = [c for c in report.contradictions if c.contradiction_type == ContradictionType.PHI_INCOHERENCE]
        assert len(phi) == 1
        assert phi[0].severity == ContradictionSeverity.CLASS_1

    def test_phi_false_on_non_l1_is_class2(self):
        atom = _atom("gradient", 2, 0, phi_parallel=False)
        engine = DimensionalContradictionEngine()
        report = engine.scan([atom])
        phi = [c for c in report.contradictions if c.contradiction_type == ContradictionType.PHI_INCOHERENCE]
        assert len(phi) == 1
        assert phi[0].severity == ContradictionSeverity.CLASS_2

    def test_g2_coherent_false_when_phi_false(self):
        atom = _atom("state", 6, 0, phi_parallel=False)
        engine = DimensionalContradictionEngine()
        report = engine.scan([atom])
        assert not report.g2_coherent


# ---------------------------------------------------------------------------
# Detector 4 — Semantic Mode Conflict
# ---------------------------------------------------------------------------

class TestDetector4SemanticModeConflict:
    def test_canonical_mode_no_conflict(self):
        # L2 = Gradient Field → SemanticMode.GRADIENT
        atom = _atom("test", 2, 0, semantic_mode=SemanticMode.GRADIENT)
        engine = DimensionalContradictionEngine()
        report = engine.scan([atom])
        smc = [c for c in report.contradictions if c.contradiction_type == ContradictionType.SEMANTIC_MODE_CONFLICT]
        assert smc == []

    def test_wrong_mode_for_layer(self):
        # L6 = State Manifold → GRADIENT is wrong
        atom = _atom("test", 6, 0, semantic_mode=SemanticMode.GRADIENT)
        engine = DimensionalContradictionEngine()
        report = engine.scan([atom])
        smc = [c for c in report.contradictions if c.contradiction_type == ContradictionType.SEMANTIC_MODE_CONFLICT]
        assert len(smc) == 1
        assert smc[0].severity == ContradictionSeverity.CLASS_3

    def test_l8_lineage_fabric_mode(self):
        # L8 = Lineage Fabric → SemanticMode.LINEAGE
        atom = _atom("lineage", 8, 0, semantic_mode=SemanticMode.LINEAGE)
        engine = DimensionalContradictionEngine()
        report = engine.scan([atom])
        smc = [c for c in report.contradictions if c.contradiction_type == ContradictionType.SEMANTIC_MODE_CONFLICT]
        assert smc == []

    def test_l5_alexandrian_lexicon_mode(self):
        # L5 = Alexandrian Lexicon → SemanticMode.LEXICAL
        atom = _atom("lexicon", 5, 0, semantic_mode=SemanticMode.LEXICAL)
        engine = DimensionalContradictionEngine()
        report = engine.scan([atom])
        smc = [c for c in report.contradictions if c.contradiction_type == ContradictionType.SEMANTIC_MODE_CONFLICT]
        assert smc == []


# ---------------------------------------------------------------------------
# Detector 5 — Layer Conflict
# ---------------------------------------------------------------------------

class TestDetector5LayerConflict:
    def test_unique_content_per_tick_no_conflict(self):
        atoms = [_atom("alpha", 2, 0), _atom("beta", 5, 0)]
        engine = DimensionalContradictionEngine()
        report = engine.scan(atoms)
        lc = [c for c in report.contradictions if c.contradiction_type == ContradictionType.LAYER_CONFLICT]
        assert lc == []

    def test_same_content_different_layers_same_tick(self):
        content = "shared narrative unit"
        a1 = _atom(content, 2, 5)
        a2 = _atom(content, 7, 5)
        engine = DimensionalContradictionEngine()
        report = engine.scan([a1, a2])
        lc = [c for c in report.contradictions if c.contradiction_type == ContradictionType.LAYER_CONFLICT]
        assert len(lc) == 1
        assert lc[0].severity == ContradictionSeverity.CLASS_2
        assert a1.atom_id in lc[0].atom_ids
        assert a2.atom_id in lc[0].atom_ids

    def test_same_content_different_ticks_not_conflict(self):
        content = "repeated content"
        a1 = _atom(content, 2, 0)
        a2 = _atom(content, 7, 1)  # different tick → allowed
        engine = DimensionalContradictionEngine()
        report = engine.scan([a1, a2])
        lc = [c for c in report.contradictions if c.contradiction_type == ContradictionType.LAYER_CONFLICT]
        assert lc == []


# ---------------------------------------------------------------------------
# Detector 6 — Lineage Shrinkage (I10)
# ---------------------------------------------------------------------------

class TestDetector6LineageShrinkage:
    def test_monotone_lineage_no_contradiction(self):
        a1 = _atom("root", 6, 0)
        a2 = _atom("root", 6, 1, lineage_refs=[a1.atom_id])
        engine = DimensionalContradictionEngine()
        report = engine.scan([a1, a2])
        ls = [c for c in report.contradictions if c.contradiction_type == ContradictionType.LINEAGE_SHRINKAGE]
        assert ls == []

    def test_lineage_shrinks_is_class2(self):
        ref_id = "some-ref-abc"
        a1 = _atom("root", 6, 0, lineage_refs=[ref_id])
        # a2 has same content (same tick=1) but fewer refs
        a2 = _atom("root", 6, 1, lineage_refs=[])  # lost ref_id
        engine = DimensionalContradictionEngine()
        report = engine.scan([a1, a2])
        ls = [c for c in report.contradictions if c.contradiction_type == ContradictionType.LINEAGE_SHRINKAGE]
        assert len(ls) == 1
        assert ls[0].severity == ContradictionSeverity.CLASS_2


# ---------------------------------------------------------------------------
# Detector 7 — Replay Inconsistency (I7)
# ---------------------------------------------------------------------------

class TestDetector7ReplayInconsistency:
    def test_consistent_replay(self):
        atom = _atom("hello", 6, 0)
        # Replay the same atom — same id, same content
        import copy
        replay = copy.copy(atom)
        engine = DimensionalContradictionEngine()
        report = engine.scan([atom, replay])
        ri = [c for c in report.contradictions if c.contradiction_type == ContradictionType.REPLAY_INCONSISTENCY]
        assert ri == []

    def test_inconsistent_replay(self):
        atom = _atom("original", 6, 0)
        tampered = _atom("different content", 6, 1)
        tampered.atom_id = atom.atom_id  # same id, different content
        engine = DimensionalContradictionEngine()
        report = engine.scan([atom, tampered])
        ri = [c for c in report.contradictions if c.contradiction_type == ContradictionType.REPLAY_INCONSISTENCY]
        assert len(ri) == 1
        assert ri[0].severity == ContradictionSeverity.CLASS_1

    def test_no_replay_no_contradiction(self):
        atoms = [_atom(f"content-{i}", 6, i) for i in range(5)]
        engine = DimensionalContradictionEngine()
        report = engine.scan(atoms)
        ri = [c for c in report.contradictions if c.contradiction_type == ContradictionType.REPLAY_INCONSISTENCY]
        assert ri == []


# ---------------------------------------------------------------------------
# Aggregate / multi-detector tests
# ---------------------------------------------------------------------------

class TestAggregateAndCleanReport:
    def test_clean_report_no_contradictions(self):
        atoms = [
            _atom("gradient input", 2, 0, semantic_mode=SemanticMode.GRADIENT),
            _atom("lexical entry", 5, 1, semantic_mode=SemanticMode.LEXICAL),
            _atom("state delta", 6, 2, semantic_mode=SemanticMode.STATE),
            _atom("archive event", 7, 3, semantic_mode=SemanticMode.MEMORY),
        ]
        engine = DimensionalContradictionEngine()
        report = engine.scan(atoms)
        assert report.clean is True
        assert report.contradictions == []
        assert report.g2_coherent is True
        assert "cqhml_contradiction_scan_clean" in report.receipts

    def test_class1_makes_report_not_clean(self):
        a1 = _atom("a", 2, 5)
        a2 = _atom("b", 2, 3)  # tick regression → CLASS_1
        engine = DimensionalContradictionEngine()
        report = engine.scan([a1, a2])
        assert report.clean is False
        assert len(report.blocking) >= 1

    def test_class2_makes_report_not_clean(self):
        atom = _atom("x", 2, 0, phi_parallel=False)  # phi=False on non-L1 → CLASS_2
        engine = DimensionalContradictionEngine()
        report = engine.scan([atom])
        assert report.clean is False

    def test_class3_only_report_is_clean(self):
        # SemanticMode mismatch → CLASS_3 only
        atom = _atom("x", 6, 0, semantic_mode=SemanticMode.GRADIENT)
        engine = DimensionalContradictionEngine()
        report = engine.scan([atom])
        assert report.clean is True  # CLASS_3 does not block

    def test_receipts_accumulate_across_scans(self):
        engine = DimensionalContradictionEngine()
        engine.scan([_atom("a", 2, 0)])
        engine.scan([_atom("b", 5, 1)])
        receipts = engine.receipts()
        assert len(receipts) >= 2

    def test_scan_envelope_clean(self):
        env = _envelope(layer=6, g2=True, observer_mode=SemanticMode.STATE)
        engine = DimensionalContradictionEngine()
        report = engine.scan_envelope(env)
        assert report.clean is True

    def test_scan_envelope_phi_incoherence(self):
        env = _envelope(layer=6, g2=False, observer_mode=SemanticMode.STATE)
        engine = DimensionalContradictionEngine()
        report = engine.scan_envelope(env)
        phi = [c for c in report.contradictions if c.contradiction_type == ContradictionType.PHI_INCOHERENCE]
        assert len(phi) == 1

    def test_locked_ontology_layer_names(self):
        # Verify canonical SemanticMode values match locked ontology
        assert SemanticMode.GRADIENT == "GRADIENT"           # L2 Gradient Field
        assert SemanticMode.LEXICAL == "LEXICAL"             # L5 Alexandrian Lexicon
        assert SemanticMode.STATE == "STATE"                 # L6 State Manifold
        assert SemanticMode.MEMORY == "MEMORY"               # L7 Alexandrian Archive
        assert SemanticMode.LINEAGE == "LINEAGE"             # L8 Lineage Fabric
        assert SemanticMode.NARRATIVE == "NARRATIVE"         # L10 Narrative
