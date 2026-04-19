"""NS∞ CQHML Manifold Engine — E4 Story Atom Loom tests.

Tag: cqhml-story-atom-loom-v2
AXIOLEV Holdings LLC © 2026
"""
import hashlib
import pytest

from ns.api.schemas.cqhml import (
    ObserverFrame,
    PolicyMode,
    SemanticMode,
)
from ns.services.cqhml.quaternion import identity, phi_coherent
from ns.services.cqhml.story_atom_loom import (
    StoryAtom,
    StoryAtomLoom,
    WovenNarrative,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _atom(content="hello", layer=2, tick=0, phi_parallel=True, semantic_mode=None, lineage_refs=None):
    return StoryAtom.create(
        content=content,
        layer=layer,
        tick=tick,
        semantic_mode=semantic_mode,
        phi_parallel=phi_parallel,
        lineage_refs=lineage_refs,
    )


def _observer(frame_id="obs-1", layer=10, policy_mode=PolicyMode.ENFORCE):
    return ObserverFrame(frame_id=frame_id, layer=layer, policy_mode=policy_mode)


def _loom():
    return StoryAtomLoom()


# ---------------------------------------------------------------------------
# Module surface
# ---------------------------------------------------------------------------

def test_importable_surface():
    import ns.services.cqhml.story_atom_loom as m
    for name in ("StoryAtom", "WovenNarrative", "StoryAtomLoom"):
        assert hasattr(m, name), f"Missing: {name}"


def test_loom_constants():
    assert StoryAtomLoom.NARRATIVE_LAYER == 10
    assert StoryAtomLoom.GRADIENT_LAYER == 2


# ---------------------------------------------------------------------------
# StoryAtom — construction and validation
# ---------------------------------------------------------------------------

def test_story_atom_create_minimal():
    atom = _atom()
    assert atom.layer == 2
    assert atom.tick == 0
    assert atom.phi_parallel is True
    assert atom.content == "hello"
    assert atom.atom_id is not None
    assert len(atom.atom_id) > 0


def test_story_atom_provenance_hash_computed():
    atom = _atom(content="test content")
    expected = hashlib.sha256(b"test content").hexdigest()
    assert atom.provenance_hash == expected


def test_story_atom_verify_provenance_valid():
    atom = _atom(content="authentic")
    assert atom.verify_provenance() is True


def test_story_atom_verify_provenance_tampered():
    atom = _atom(content="authentic")
    atom.provenance_hash = "deadbeef" * 8  # tampered
    assert atom.verify_provenance() is False


def test_story_atom_layer_out_of_range_raises():
    with pytest.raises(ValueError):
        _atom(layer=0)
    with pytest.raises(ValueError):
        _atom(layer=11)


def test_story_atom_negative_tick_raises():
    with pytest.raises(ValueError):
        StoryAtom.create(content="x", layer=2, tick=-1)


def test_story_atom_all_layers_valid():
    for layer in range(1, 11):
        atom = StoryAtom.create(content=f"layer{layer}", layer=layer, tick=0)
        assert atom.layer == layer
        assert atom.verify_provenance()


def test_story_atom_semantic_mode_defaults_to_layer_mode():
    atom = StoryAtom.create(content="x", layer=10, tick=0)
    assert atom.semantic_mode == SemanticMode.NARRATIVE

    atom2 = StoryAtom.create(content="x", layer=1, tick=0)
    assert atom2.semantic_mode == SemanticMode.CONSTITUTIONAL


def test_story_atom_lineage_refs_copied():
    atom = StoryAtom.create(content="x", layer=2, tick=0, lineage_refs=["ref-1"])
    assert "ref-1" in atom.lineage_refs
    atom.lineage_refs.append("ref-2")  # mutation on copy, not original list
    atom2 = StoryAtom.create(content="x", layer=2, tick=0, lineage_refs=["ref-1"])
    assert "ref-2" not in atom2.lineage_refs


def test_story_atom_explicit_mode_overrides_layer_default():
    atom = StoryAtom.create(content="x", layer=2, tick=0, semantic_mode=SemanticMode.MEMORY)
    assert atom.semantic_mode == SemanticMode.MEMORY


# ---------------------------------------------------------------------------
# WovenNarrative
# ---------------------------------------------------------------------------

def test_woven_narrative_coherent_with_unit_quaternion():
    atom = _atom()
    loom = _loom()
    narrative = loom.weave([atom], _observer(), target_layer=10)
    assert narrative.atom_count == 1
    assert narrative.g2_phi_parallel is True
    assert narrative.coherent() is True


def test_woven_narrative_atom_count():
    atoms = [_atom(content=f"atom{i}", tick=i) for i in range(5)]
    loom = _loom()
    narrative = loom.weave(atoms, _observer(), target_layer=10)
    assert narrative.atom_count == 5


def test_woven_narrative_source_target_layers():
    atom = _atom(layer=3)
    narrative = _loom().weave([atom], _observer(), target_layer=7)
    assert narrative.source_layer == 3
    assert narrative.target_layer == 7


def test_woven_narrative_receipts_non_empty():
    atom = _atom()
    narrative = _loom().weave([atom], _observer(), target_layer=10)
    assert len(narrative.receipts) > 0
    assert "cqhml_story_atom_woven" in narrative.receipts


def test_woven_narrative_ring6_receipt_when_g2_coherent():
    atom = _atom()
    narrative = _loom().weave([atom], _observer(), target_layer=10)
    assert "ring6_g2_invariant_checked" in narrative.receipts


def test_woven_narrative_trace_non_empty():
    atom = _atom()
    narrative = _loom().weave([atom], _observer(), target_layer=10)
    assert len(narrative.trace) >= 1


def test_woven_narrative_tick_equals_last_atom_tick():
    atoms = [_atom(tick=0), _atom(tick=3), _atom(tick=7)]
    narrative = _loom().weave(atoms, _observer(), target_layer=10)
    assert narrative.tick == 7


# ---------------------------------------------------------------------------
# StoryAtomLoom — weave
# ---------------------------------------------------------------------------

def test_weave_empty_atoms_raises():
    with pytest.raises(ValueError, match="empty"):
        _loom().weave([], _observer())


def test_weave_invalid_target_layer_raises():
    atom = _atom()
    with pytest.raises(ValueError):
        _loom().weave([atom], _observer(), target_layer=0)
    with pytest.raises(ValueError):
        _loom().weave([atom], _observer(), target_layer=11)


def test_weave_provenance_violation_raises():
    atom = _atom()
    atom.provenance_hash = "bad"
    with pytest.raises(ValueError, match="Provenance"):
        _loom().weave([atom], _observer())


def test_weave_audit_policy_adds_receipt():
    atom = _atom()
    observer = _observer(policy_mode=PolicyMode.AUDIT)
    narrative = _loom().weave([atom], observer, target_layer=10)
    assert "cqhml_audit_trace_emitted" in narrative.receipts


def test_weave_audit_policy_adds_observer_to_trace():
    atom = _atom()
    observer = _observer(frame_id="founder-audit", policy_mode=PolicyMode.AUDIT)
    narrative = _loom().weave([atom], observer, target_layer=10)
    assert any("founder-audit" in t for t in narrative.trace)


def test_weave_same_layer_produces_identity_rotation():
    atom = _atom(layer=5)
    narrative = _loom().weave([atom], _observer(), target_layer=5)
    assert narrative.rotation_quaternion == identity()


def test_weave_multiple_atoms_different_layers():
    atoms = [
        _atom(content="a", layer=2, tick=0),
        _atom(content="b", layer=5, tick=1),
        _atom(content="c", layer=8, tick=2),
    ]
    narrative = _loom().weave(atoms, _observer(), target_layer=10)
    assert narrative.source_layer == 2
    assert narrative.target_layer == 10
    assert "cqhml_story_atom_woven" in narrative.receipts


def test_weave_narrative_id_is_unique():
    atom = _atom()
    n1 = _loom().weave([atom], _observer())
    n2 = _loom().weave([atom], _observer())
    assert n1.narrative_id != n2.narrative_id


# ---------------------------------------------------------------------------
# I2 — tick monotonicity
# ---------------------------------------------------------------------------

def test_i2_monotone_tick_passes():
    atoms = [_atom(tick=0), _atom(tick=0), _atom(tick=1), _atom(tick=5)]
    narrative = _loom().weave(atoms, _observer())
    assert narrative.tick == 5


def test_i2_tick_regression_raises():
    atoms = [_atom(tick=5), _atom(tick=3)]
    with pytest.raises(ValueError, match="I2"):
        _loom().weave(atoms, _observer())


def test_i2_single_atom_always_monotone():
    atom = _atom(tick=99)
    narrative = _loom().weave([atom], _observer())
    assert narrative.tick == 99


# ---------------------------------------------------------------------------
# I6 — Sentinel Gate (L1 phi_parallel=False)
# ---------------------------------------------------------------------------

def test_i6_l1_phi_parallel_false_blocked():
    atom = _atom(layer=1, phi_parallel=False)
    narrative = _loom().weave([atom], _observer(), target_layer=10)
    assert "cqhml_story_atom_constitutional_block" in narrative.receipts
    assert narrative.g2_phi_parallel is False


def test_i6_l1_phi_parallel_true_passes():
    atom = _atom(layer=1, phi_parallel=True)
    narrative = _loom().weave([atom], _observer(), target_layer=10)
    assert "cqhml_story_atom_constitutional_block" not in narrative.receipts
    assert "cqhml_story_atom_woven" in narrative.receipts


def test_i6_non_l1_phi_parallel_false_not_blocked():
    # phi_parallel=False on non-constitutional layer should not trigger sentinel
    atom = _atom(layer=5, phi_parallel=False)
    narrative = _loom().weave([atom], _observer(), target_layer=10)
    assert "cqhml_story_atom_constitutional_block" not in narrative.receipts
    assert "cqhml_story_atom_woven" in narrative.receipts


# ---------------------------------------------------------------------------
# project_atom
# ---------------------------------------------------------------------------

def test_project_atom_changes_layer():
    atom = _atom(layer=2, tick=5)
    loom = _loom()
    projected = loom.project_atom(atom, target_layer=10)
    assert projected.layer == 10
    assert projected.tick == 5


def test_project_atom_preserves_content_and_provenance():
    atom = _atom(content="original text", layer=2)
    projected = _loom().project_atom(atom, target_layer=8)
    assert projected.content == "original text"
    assert projected.verify_provenance() is True


def test_project_atom_extends_lineage_refs():
    atom = _atom(layer=2)
    projected = _loom().project_atom(atom, target_layer=10)
    assert atom.atom_id in projected.lineage_refs


def test_project_atom_lineage_chain():
    a1 = _atom(layer=2, tick=0)
    a2 = _loom().project_atom(a1, target_layer=5)
    a3 = _loom().project_atom(a2, target_layer=10)
    assert a1.atom_id in a2.lineage_refs
    assert a2.atom_id in a3.lineage_refs


def test_project_atom_canonical_semantic_mode():
    atom = _atom(layer=2)
    projected = _loom().project_atom(atom, target_layer=10)
    assert projected.semantic_mode == SemanticMode.NARRATIVE

    projected5 = _loom().project_atom(atom, target_layer=5)
    assert projected5.semantic_mode == SemanticMode.LEXICAL


def test_project_atom_invalid_target_layer_raises():
    atom = _atom()
    with pytest.raises(ValueError):
        _loom().project_atom(atom, target_layer=0)
    with pytest.raises(ValueError):
        _loom().project_atom(atom, target_layer=11)


def test_project_atom_provenance_violation_raises():
    atom = _atom()
    atom.provenance_hash = "tampered"
    with pytest.raises(ValueError, match="Provenance"):
        _loom().project_atom(atom, target_layer=10)


def test_project_atom_same_layer_preserves_atom():
    atom = _atom(layer=5, content="same layer")
    projected = _loom().project_atom(atom, target_layer=5)
    assert projected.layer == 5
    assert projected.content == "same layer"


# ---------------------------------------------------------------------------
# coherence_check
# ---------------------------------------------------------------------------

def test_coherence_check_coherent_narrative():
    atom = _atom()
    narrative = _loom().weave([atom], _observer(), target_layer=10)
    assert _loom().coherence_check(narrative) is True


def test_coherence_check_blocked_narrative_fails():
    atom = _atom(layer=1, phi_parallel=False)
    narrative = _loom().weave([atom], _observer(), target_layer=10)
    assert narrative.coherent() is False


# ---------------------------------------------------------------------------
# receipts (I2/I10 — append-only)
# ---------------------------------------------------------------------------

def test_receipts_accumulate_across_weaves():
    loom = _loom()
    atom = _atom()
    loom.weave([atom], _observer())
    loom.weave([atom], _observer())
    receipts = loom.receipts()
    assert receipts.count("cqhml_story_atom_woven") == 2


def test_receipts_returns_copy():
    loom = _loom()
    loom.weave([_atom()], _observer())
    r1 = loom.receipts()
    r1.append("injected")
    r2 = loom.receipts()
    assert "injected" not in r2


def test_receipts_empty_before_weave():
    loom = _loom()
    assert loom.receipts() == []


# ---------------------------------------------------------------------------
# Locked ontology — deprecated names must not appear
# ---------------------------------------------------------------------------

def test_no_deprecated_names_in_module():
    import ns.services.cqhml.story_atom_loom as m
    deprecated = {"Ether", "Lexicon", "Manifold", "Alexandria", "CTF", "Storytime"}
    public = {name for name in dir(m) if not name.startswith("_")}
    assert not deprecated.intersection(public), f"Deprecated: {deprecated & public}"


def test_semantic_mode_no_deprecated_names():
    deprecated = {"ETHER", "LEXICON", "MANIFOLD", "ALEXANDRIA", "CTF", "STORYTIME"}
    values = {m.value for m in SemanticMode}
    assert not deprecated.intersection(values)


# ---------------------------------------------------------------------------
# I1 — Canon precedes Conversion (loom does not write Canon)
# ---------------------------------------------------------------------------

def test_i1_loom_does_not_write_canon():
    # The loom module must not import or call any canon write function
    import ns.services.cqhml.story_atom_loom as m
    import inspect
    src = inspect.getsource(m)
    assert "canon.write" not in src
    assert "promote_to_canon" not in src


# ---------------------------------------------------------------------------
# I5 — Provenance inertness
# ---------------------------------------------------------------------------

def test_i5_all_projected_atoms_valid_provenance():
    atom = _atom(content="provenance test", layer=3, tick=1)
    loom = _loom()
    for tgt in range(1, 11):
        projected = loom.project_atom(atom, target_layer=tgt)
        assert projected.verify_provenance(), f"Failed for target_layer={tgt}"


def test_i5_all_woven_atoms_valid_provenance():
    atoms = [_atom(content=f"content-{i}", layer=i % 9 + 1, tick=i) for i in range(5)]
    narrative = _loom().weave(atoms, _observer(), target_layer=10)
    for atom in narrative.atoms:
        assert atom.verify_provenance()


# ---------------------------------------------------------------------------
# G₂ coherence — quaternion rotation
# ---------------------------------------------------------------------------

def test_rotation_quaternion_is_unit():
    atom = _atom(layer=2)
    narrative = _loom().weave([atom], _observer(), target_layer=10)
    import math
    assert abs(narrative.rotation_quaternion.norm() - 1.0) < 1e-10


def test_rotation_quaternion_positive_hemisphere():
    atom = _atom(layer=1)
    narrative = _loom().weave([atom], _observer(), target_layer=10)
    assert narrative.rotation_quaternion.w >= 0.0
