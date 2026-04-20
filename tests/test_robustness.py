"""Q8 — robustness suite tests."""
from services.robustness import stability

def _stable_fn(x: str) -> str:
    return x.strip().lower()

def _unstable_fn(x: str) -> str:
    return x   # raw passthrough — casing / spaces leak through

def test_stable_answer_high_score():
    assert stability(_stable_fn, ["Hello","World"]) > 0.9

def test_unstable_answer_lower_score():
    assert stability(_unstable_fn, ["Hello","World"]) < 0.9
