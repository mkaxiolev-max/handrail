"""NER determinism proof — 1000/1000 identical results from identical receipts."""
from isr.ner import compute_ner

_RECEIPTS = [
    {"tokens_output": 100, "grounded": True, "receipt_id": "r1"},
    {"tokens_output": 50,  "grounded": False},
    {"tokens_output": 200, "grounded": True, "receipt_id": "r2"},
    {"narrative_tokens": 30, "grounded": True, "receipt_id": "r3"},
]


def test_ner_determinism_1000():
    first = compute_ner(_RECEIPTS, window_minutes=15)
    for _ in range(999):
        obs = compute_ner(_RECEIPTS, window_minutes=15)
        assert obs.rate == first.rate, f"NER non-deterministic: {obs.rate} != {first.rate}"
        assert obs.threshold_crossed == first.threshold_crossed
        assert obs.trend == first.trend


def test_ner_empty_receipts_zero():
    obs = compute_ner([], window_minutes=15)
    assert obs.rate == 0.0
    assert obs.threshold_crossed is False


def test_ner_threshold_crossed():
    # Many high-token receipts, few grounded actions → high rate
    receipts = [{"tokens_output": 10000, "grounded": False}] * 50
    obs = compute_ner(receipts, window_minutes=1)
    assert obs.threshold_crossed is True


def test_ner_returns_observation_shape():
    obs = compute_ner(_RECEIPTS)
    assert obs.rate >= 0
    assert obs.trend in ("stable", "rising", "falling")
    assert isinstance(obs.threshold_crossed, bool)
    assert obs.receipt_count == len(_RECEIPTS)
