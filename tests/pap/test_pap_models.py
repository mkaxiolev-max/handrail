from services.pap.models import (
    AletheiaPAPResource, EpistemicType, PAPAction,
)


def test_pap_resource_round_trip(clean_resource):
    d = clean_resource.dict()
    r2 = AletheiaPAPResource(**d)
    assert r2.resource_id == clean_resource.resource_id
    assert r2.merkle_root == clean_resource.merkle_root


def test_epistemic_type_enum_complete():
    assert {t.value for t in EpistemicType} == {
        "observed_fact","reported_claim","derived_inference",
        "speculation","legal_status_event","narrative_frame",
    }


def test_action_handrail_required_default_true():
    a = PAPAction(action_id="x", endpoint="/y", method="POST",
                  reversibility_score=0.5)
    assert a.handrail_required is True


def test_storytime_mode_narrative_as_proof_typed_but_validator_rejects(make_resource):
    # Type system allows the value (it's in the Literal); validator rejects it.
    r = make_resource(storytime_mode="NARRATIVE_AS_PROOF")
    assert r.H.storytime_mode == "NARRATIVE_AS_PROOF"
    from services.pap.validator import validate_pap_resource
    ok, reasons = validate_pap_resource(r)
    assert not ok
    assert any("NARRATIVE_AS_PROOF" in r_ for r_ in reasons)
