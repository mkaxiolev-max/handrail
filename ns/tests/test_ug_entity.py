"""axiolev-ug-entity-test-v2"""
from ns.ug.entity import Entity, EntityKind, Identity, Provenance
from ns.ug.registry import branch_to_entity
from ns.ug.temporal import slice_entity, BOHMIAN_PILOT_WAVE_STATUS
from ns.omega.primitives import Branch, ProjectionMode


def test_entity_base_constructs():
    e = Entity(
        id="e-1",
        kind=EntityKind.OTHER,
        identity=Identity(canonical_name="test"),
        provenance=Provenance(origin="test"),
    )
    assert e.id == "e-1"
    assert e.kind == EntityKind.OTHER


def test_branch_specialization():
    b = Branch(id="b-1", title="main", mode=ProjectionMode.CURRENT)
    e = branch_to_entity(b)
    assert e.id == "b-1"
    assert e.kind == EntityKind.BRANCH
    assert e.identity.canonical_name == "main"


def test_temporal_slice_is_pure():
    e = Entity(
        id="e-1",
        kind=EntityKind.OTHER,
        identity=Identity(canonical_name="t"),
        provenance=Provenance(origin="test"),
        state={"x": 1},
    )
    s = slice_entity(e)
    s.state_snapshot["x"] = 999
    assert e.state["x"] == 1


def test_bohmian_quarantined():
    assert "QUARANTINED" in BOHMIAN_PILOT_WAVE_STATUS
