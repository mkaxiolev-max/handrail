"""CQHML Manifold Engine — E2 dimensions/schemas tests.

Tag: cqhml-dimensions-v2
"""
import pytest
from pydantic import ValidationError

from ns.api.schemas.cqhml import (
    DimensionalCoordinate,
    SemanticMode,
    PolicyMode,
    ObserverFrame,
    DimensionalEnvelope,
    ProjectionRequest,
    ProjectionResult,
)


# ---------------------------------------------------------------------------
# Module surface
# ---------------------------------------------------------------------------

def test_importable_surface():
    import ns.api.schemas.cqhml as m
    for name in (
        "DimensionalCoordinate", "SemanticMode", "PolicyMode",
        "ObserverFrame", "DimensionalEnvelope",
        "ProjectionRequest", "ProjectionResult",
    ):
        assert hasattr(m, name)


# ---------------------------------------------------------------------------
# SemanticMode
# ---------------------------------------------------------------------------

def test_semantic_mode_values():
    expected = {
        "GRADIENT", "INTAKE", "CONVERSION", "LEXICAL",
        "STATE", "MEMORY", "LINEAGE", "NARRATIVE",
        "CONSTITUTIONAL", "ERROR",
    }
    assert {m.value for m in SemanticMode} == expected


def test_semantic_mode_is_str_enum():
    assert isinstance(SemanticMode.GRADIENT, str)


def test_semantic_mode_ontology_layers_covered():
    # L1 Constitutional, L2 Gradient, L3 Intake, L4 Conversion,
    # L5 Lexical, L6 State, L7 Memory, L8 Lineage, L10 Narrative
    assert SemanticMode.CONSTITUTIONAL == "CONSTITUTIONAL"
    assert SemanticMode.GRADIENT == "GRADIENT"
    assert SemanticMode.LINEAGE == "LINEAGE"
    assert SemanticMode.NARRATIVE == "NARRATIVE"


# ---------------------------------------------------------------------------
# PolicyMode
# ---------------------------------------------------------------------------

def test_policy_mode_values():
    assert set(PolicyMode) == {
        PolicyMode.ENFORCE,
        PolicyMode.ADVISORY,
        PolicyMode.AUDIT,
        PolicyMode.CONSTITUTIONAL_BLOCK,
    }


def test_policy_mode_is_str_enum():
    assert isinstance(PolicyMode.ENFORCE, str)


def test_policy_mode_no_bypass():
    # auth.bypass is a never-event — must not exist in PolicyMode
    values = [m.value for m in PolicyMode]
    assert "BYPASS" not in values
    assert "AUTH_BYPASS" not in values


# ---------------------------------------------------------------------------
# DimensionalCoordinate
# ---------------------------------------------------------------------------

def test_dimensional_coordinate_minimal():
    coord = DimensionalCoordinate(layer=1)
    assert coord.layer == 1
    assert coord.tick == 0
    assert coord.phi_parallel is True
    assert coord.magnitude == 1.0
    assert coord.axis == "canonical"


def test_dimensional_coordinate_all_fields():
    coord = DimensionalCoordinate(
        layer=6, axis="state_shard", tick=42,
        phi_parallel=True, magnitude=0.9,
    )
    assert coord.layer == 6
    assert coord.axis == "state_shard"
    assert coord.tick == 42


def test_dimensional_coordinate_layer_bounds():
    DimensionalCoordinate(layer=1)
    DimensionalCoordinate(layer=10)
    with pytest.raises(ValidationError):
        DimensionalCoordinate(layer=0)
    with pytest.raises(ValidationError):
        DimensionalCoordinate(layer=11)


def test_dimensional_coordinate_tick_non_negative():
    with pytest.raises(ValidationError):
        DimensionalCoordinate(layer=1, tick=-1)


def test_dimensional_coordinate_magnitude_non_negative():
    with pytest.raises(ValidationError):
        DimensionalCoordinate(layer=1, magnitude=-0.1)


def test_dimensional_coordinate_extra_forbidden():
    with pytest.raises(ValidationError):
        DimensionalCoordinate(layer=1, unknown_field="x")


def test_dimensional_coordinate_phi_parallel_false():
    coord = DimensionalCoordinate(layer=1, phi_parallel=False)
    assert coord.phi_parallel is False


# ---------------------------------------------------------------------------
# ObserverFrame
# ---------------------------------------------------------------------------

def test_observer_frame_minimal():
    obs = ObserverFrame(frame_id="f1", layer=5)
    assert obs.frame_id == "f1"
    assert obs.layer == 5
    assert obs.semantic_mode == SemanticMode.STATE
    assert obs.policy_mode == PolicyMode.ENFORCE
    assert obs.tick == 0
    assert obs.quorum_verified is False


def test_observer_frame_all_fields():
    obs = ObserverFrame(
        frame_id="f2", layer=1,
        semantic_mode=SemanticMode.CONSTITUTIONAL,
        policy_mode=PolicyMode.CONSTITUTIONAL_BLOCK,
        tick=10, quorum_verified=True,
    )
    assert obs.quorum_verified is True
    assert obs.semantic_mode == SemanticMode.CONSTITUTIONAL


def test_observer_frame_layer_bounds():
    ObserverFrame(frame_id="x", layer=1)
    ObserverFrame(frame_id="x", layer=10)
    with pytest.raises(ValidationError):
        ObserverFrame(frame_id="x", layer=0)
    with pytest.raises(ValidationError):
        ObserverFrame(frame_id="x", layer=11)


def test_observer_frame_extra_forbidden():
    with pytest.raises(ValidationError):
        ObserverFrame(frame_id="x", layer=1, bad_field=True)


# ---------------------------------------------------------------------------
# DimensionalEnvelope
# ---------------------------------------------------------------------------

def _make_coord(layer=5):
    return DimensionalCoordinate(layer=layer)


def _make_observer(layer=5):
    return ObserverFrame(frame_id="obs-1", layer=layer)


def test_dimensional_envelope_minimal():
    env = DimensionalEnvelope(
        coordinate=_make_coord(),
        observer=_make_observer(),
    )
    assert env.g2_phi_parallel is True
    assert env.spin7_coherent is True
    assert env.tick == 0
    assert env.receipts_attached == []


def test_dimensional_envelope_receipts():
    env = DimensionalEnvelope(
        coordinate=_make_coord(),
        observer=_make_observer(),
        receipts_attached=["ring6_g2_invariant_checked"],
    )
    assert "ring6_g2_invariant_checked" in env.receipts_attached


def test_dimensional_envelope_phi_flag():
    env = DimensionalEnvelope(
        coordinate=_make_coord(),
        observer=_make_observer(),
        g2_phi_parallel=False,
    )
    assert env.g2_phi_parallel is False


def test_dimensional_envelope_extra_forbidden():
    with pytest.raises(ValidationError):
        DimensionalEnvelope(
            coordinate=_make_coord(),
            observer=_make_observer(),
            bad_key="x",
        )


# ---------------------------------------------------------------------------
# ProjectionRequest
# ---------------------------------------------------------------------------

def _make_envelope():
    return DimensionalEnvelope(coordinate=_make_coord(), observer=_make_observer())


def test_projection_request_minimal():
    req = ProjectionRequest(
        request_id="req-1",
        envelope=_make_envelope(),
        target_layer=8,
    )
    assert req.request_id == "req-1"
    assert req.target_layer == 8
    assert req.context == {}
    assert req.tick == 0


def test_projection_request_with_modes():
    req = ProjectionRequest(
        request_id="req-2",
        envelope=_make_envelope(),
        target_layer=3,
        semantic_mode=SemanticMode.INTAKE,
        policy_mode=PolicyMode.ADVISORY,
    )
    assert req.semantic_mode == SemanticMode.INTAKE
    assert req.policy_mode == PolicyMode.ADVISORY


def test_projection_request_target_layer_bounds():
    ProjectionRequest(request_id="r", envelope=_make_envelope(), target_layer=1)
    ProjectionRequest(request_id="r", envelope=_make_envelope(), target_layer=10)
    with pytest.raises(ValidationError):
        ProjectionRequest(request_id="r", envelope=_make_envelope(), target_layer=0)
    with pytest.raises(ValidationError):
        ProjectionRequest(request_id="r", envelope=_make_envelope(), target_layer=11)


def test_projection_request_context_passthrough():
    req = ProjectionRequest(
        request_id="r3",
        envelope=_make_envelope(),
        target_layer=2,
        context={"key": "val"},
    )
    assert req.context["key"] == "val"


def test_projection_request_extra_forbidden():
    with pytest.raises(ValidationError):
        ProjectionRequest(
            request_id="r4",
            envelope=_make_envelope(),
            target_layer=2,
            unknown="x",
        )


# ---------------------------------------------------------------------------
# ProjectionResult
# ---------------------------------------------------------------------------

def test_projection_result_success():
    result = ProjectionResult(
        request_id="req-1",
        success=True,
        projected_coordinate=DimensionalCoordinate(layer=8),
        source_layer=5,
        target_layer=8,
        receipts_emitted=["cqhml_projection_success"],
    )
    assert result.success is True
    assert result.projected_coordinate.layer == 8
    assert "cqhml_projection_success" in result.receipts_emitted


def test_projection_result_failure():
    result = ProjectionResult(
        request_id="req-2",
        success=False,
        source_layer=1,
        target_layer=10,
        error="constitutional_block",
    )
    assert result.success is False
    assert result.error == "constitutional_block"
    assert result.projected_coordinate is None


def test_projection_result_defaults():
    result = ProjectionResult(request_id="r", success=True, source_layer=1, target_layer=1)
    assert result.g2_phi_parallel is True
    assert result.receipts_emitted == []
    assert result.trace == []
    assert result.tick == 0
    assert result.error is None


def test_projection_result_trace():
    result = ProjectionResult(
        request_id="r",
        success=True,
        source_layer=2,
        target_layer=5,
        trace=["step1", "step2", "step3"],
    )
    assert len(result.trace) == 3


def test_projection_result_layer_bounds():
    with pytest.raises(ValidationError):
        ProjectionResult(request_id="r", success=True, source_layer=0, target_layer=1)
    with pytest.raises(ValidationError):
        ProjectionResult(request_id="r", success=True, source_layer=1, target_layer=11)


def test_projection_result_extra_forbidden():
    with pytest.raises(ValidationError):
        ProjectionResult(request_id="r", success=True, source_layer=1, target_layer=1, bad="x")


# ---------------------------------------------------------------------------
# Cross-model coherence
# ---------------------------------------------------------------------------

def test_full_round_trip_projection():
    coord = DimensionalCoordinate(layer=5, axis="semantic_shard", tick=7, phi_parallel=True)
    observer = ObserverFrame(
        frame_id="founder-1", layer=5,
        semantic_mode=SemanticMode.STATE,
        policy_mode=PolicyMode.ENFORCE,
        tick=7, quorum_verified=True,
    )
    envelope = DimensionalEnvelope(
        coordinate=coord, observer=observer,
        g2_phi_parallel=True, tick=7,
        receipts_attached=["ring6_g2_invariant_checked"],
    )
    req = ProjectionRequest(
        request_id="proj-001",
        envelope=envelope,
        target_layer=8,
        semantic_mode=SemanticMode.MEMORY,
        context={"source": "test"},
        tick=7,
    )
    result = ProjectionResult(
        request_id=req.request_id,
        success=True,
        projected_coordinate=DimensionalCoordinate(layer=8, tick=7),
        source_layer=req.envelope.coordinate.layer,
        target_layer=req.target_layer,
        g2_phi_parallel=req.envelope.g2_phi_parallel,
        receipts_emitted=["cqhml_projection_success"],
        tick=7,
    )
    assert result.request_id == "proj-001"
    assert result.source_layer == 5
    assert result.target_layer == 8
    assert result.g2_phi_parallel is True


def test_ontology_names_locked():
    # Verify deprecated names do NOT appear in SemanticMode values
    deprecated = {"ETHER", "LEXICON", "MANIFOLD", "ALEXANDRIA", "CTF", "STORYTIME"}
    values = {m.value for m in SemanticMode}
    assert not deprecated.intersection(values), f"Deprecated names found: {deprecated & values}"
