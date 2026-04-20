"""Q4 — Three-Realities reconstruction tests."""
from services.three_realities import ThreeRealityState

def _state():
    return ThreeRealityState(
        lexicon    = {"id": "A", "tier": "canon"},
        alexandria = {"id": "A", "ts": 1.0},
        san        = {"tier": "canon", "ts": 1.0},
    )

def test_reconstruction_sound():
    assert _state().is_reconstruction_sound()

def test_disjointness_high():
    assert _state().disjointness_score() > 0.5

def test_tampered_breaks_soundness():
    s = _state()
    s.lexicon["tier"] = "not-canon"
    assert not s.is_reconstruction_sound()
