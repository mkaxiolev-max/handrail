"""force_ground lane determinism proof — 1000/1000 identical triggers."""
from cps.lanes.force_ground import ForceGroundLane


def test_force_ground_determinism_1000():
    lane = ForceGroundLane()
    first = lane.activate(5.0)
    for i in range(1, 1000):
        lane2 = ForceGroundLane()
        result = lane2.activate(5.0)
        assert result["activated"] == first["activated"], f"non-deterministic at {i}"
        assert result["advisory"] == first["advisory"]
        assert result["ner_rate"] == first["ner_rate"]


def test_force_ground_inactive_by_default():
    lane = ForceGroundLane()
    assert lane.state()["active"] is False


def test_force_ground_check_passes_without_activation():
    lane = ForceGroundLane()
    result = lane.check({"op": "read.healthz"})
    assert result["pass"] is True
    assert result["force_ground_active"] is False


def test_force_ground_requires_anchor_when_active():
    lane = ForceGroundLane()
    lane.activate(10.0)
    # No anchor → advisory fail
    result = lane.check({"op": "execute.thing"})
    assert result["force_ground_active"] is True
    assert result["missing_anchor"] is True
    # With anchor → pass
    result2 = lane.check({"op": "execute.thing", "receipt_id": "abc123"})
    assert result2["pass"] is True
