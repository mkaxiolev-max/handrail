"""Q19 — replay soundness tests."""
from services.replay import apply_events, replay_fingerprint, replay_sound

def test_same_events_same_fingerprint():
    evs = [{"type":"inc","by":3},{"type":"set","k":"x","v":1}]
    assert replay_fingerprint(evs) == replay_fingerprint(list(evs))

def test_reordered_events_different_fingerprint():
    a = [{"type":"set","k":"x","v":1},{"type":"set","k":"x","v":2}]
    b = [{"type":"set","k":"x","v":2},{"type":"set","k":"x","v":1}]
    assert replay_fingerprint(a) != replay_fingerprint(b)

def test_supersession_is_monotone():
    s = apply_events([{"type":"set","k":"x","v":7},{"type":"del","k":"x"}])
    assert "x" in s["keys"] and s["keys"]["x"] is None

def test_replay_sound_round_trip():
    evs = [{"type":"inc"},{"type":"inc","by":2},{"type":"set","k":"a","v":"v"}]
    assert replay_sound(evs, list(evs))
