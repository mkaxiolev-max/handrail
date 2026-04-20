"""Q13 — TLA+ bridge tests."""
from services.tla_bridge import artifact_witness

def test_nsinvariants_present():
    a = artifact_witness("tla/NSInvariants.tla")
    assert a.status == "green"
    assert a.checker == "artifact-witness"
    assert len(a.sha256) == 64
