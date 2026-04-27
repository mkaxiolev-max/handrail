import pytest
from services.pap.storytime_bridge import render_h_layer
from services.pap.models import HumanSurface


def test_canonical_explanation_renders():
    h = HumanSurface(summary="x", explanation="y",
                     storytime_mode="CANONICAL_EXPLANATION")
    out = render_h_layer(h)
    assert out["mode"] == "CANONICAL_EXPLANATION"


def test_narrative_as_proof_rejected():
    h = HumanSurface(summary="x", explanation="y",
                     storytime_mode="NARRATIVE_AS_PROOF")
    with pytest.raises(ValueError):
        render_h_layer(h)
