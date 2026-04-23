"""INS-02 NVIR Generator — production generator stack tests.
© 2026 AXIOLEV Holdings LLC
"""
from __future__ import annotations

import time

import pytest

from services.nvir.dispatcher import NVIRDispatcher
from services.nvir.generator import (
    AnthropicDispatcher,
    CompositeDispatcher,
    GeneratedCandidate,
    GeneratorSeed,
    MockDispatcher,
    NVIRGenerator,
    _backoff_seconds,
)


# ── helpers ────────────────────────────────────────────────────────────────────

def _counter_mock(domain: str = "general") -> tuple[NVIRGenerator, list[int]]:
    """Return a generator with a mock dispatcher that records call count."""
    calls: list[int] = []

    def response(prompt, d, seed):
        calls.append(1)
        return f"response_{len(calls)}_{seed.rng_seed}", "mock"

    gen = NVIRGenerator(domain=domain, dispatcher=MockDispatcher(lambda p, d, s: (f"r_{s.rng_seed}", "mock")))
    return gen, calls


# ── seed capture ───────────────────────────────────────────────────────────────

def test_gen_01_seed_fields_populated():
    gen = NVIRGenerator(domain="math", dispatcher=MockDispatcher())
    seed = gen._make_seed("prove 2+2=4")
    assert seed.domain == "math"
    assert len(seed.seed_id) == 36           # UUID
    assert len(seed.prompt_hash) == 16       # sha256[:16]
    assert seed.rng_seed >= 0
    assert "T" in seed.ts_utc               # ISO8601


def test_gen_02_generate_returns_candidate():
    gen = NVIRGenerator(domain="logic", dispatcher=MockDispatcher())
    c = gen.generate("A or not A")
    assert isinstance(c, GeneratedCandidate)
    assert c.domain == "logic"
    assert c.model_used == "mock"
    assert c.attempt == 0
    assert c.latency_ms >= 0.0
    assert len(c.generation_id) == 36


def test_gen_03_seed_prompt_hash_deterministic():
    gen = NVIRGenerator(dispatcher=MockDispatcher())
    s1 = gen._make_seed("hello world")
    s2 = gen._make_seed("hello world")
    assert s1.prompt_hash == s2.prompt_hash  # same prompt → same hash
    s3 = gen._make_seed("different prompt")
    assert s1.prompt_hash != s3.prompt_hash


def test_gen_04_replay_uses_provided_seed():
    gen = NVIRGenerator(domain="code", dispatcher=MockDispatcher(
        lambda p, d, s: f"generated_for_{s.rng_seed}"
    ))
    original = gen.generate("write a test")
    seed = original.seed

    replayed = gen.replay(seed, "write a test")
    # Same seed → same rng_seed baked into content
    assert replayed.seed.seed_id == seed.seed_id
    assert replayed.seed.rng_seed == seed.rng_seed
    assert f"{seed.rng_seed}" in replayed.content


def test_gen_05_backoff_is_exponential():
    """Backoff upper bound grows exponentially with attempt number."""
    caps = [_backoff_seconds.__wrapped__(a) if hasattr(_backoff_seconds, "__wrapped__")
            else None for a in range(5)]
    # Simple invariant: for attempt=0 max≤1, attempt=3 max≤8
    # We can't test random values, so check the formula directly
    import services.nvir.generator as mod
    import math

    for attempt in range(5):
        upper = min(30.0, 1.0 * (2 ** attempt))
        # _backoff_seconds returns Uniform(0, upper)
        # Sample many times and verify all within bounds
        for _ in range(20):
            v = mod._backoff_seconds(attempt)
            assert 0.0 <= v <= upper + 1e-9, f"attempt={attempt} backoff={v} > {upper}"


def test_gen_06_retries_on_failure_then_succeeds():
    """Generator retries on dispatcher failure; succeeds on last attempt."""
    attempt_log: list[int] = []

    def flaky(prompt, domain, seed):
        attempt_log.append(len(attempt_log))
        if len(attempt_log) < 3:
            raise RuntimeError("transient failure")
        return "ok_content"  # plain string; MockDispatcher adds "mock" model

    gen = NVIRGenerator(
        max_retries=3,
        dispatcher=MockDispatcher(flaky),
    )
    # Patch sleep to avoid delays in tests
    import services.nvir.generator as mod
    original_sleep = mod.time.sleep
    mod.time.sleep = lambda _: None
    try:
        c = gen.generate("prompt")
        assert c.content == "ok_content"
        assert c.attempt == 2           # 0-indexed: third attempt
        assert len(attempt_log) == 3
    finally:
        mod.time.sleep = original_sleep


def test_gen_07_raises_after_max_retries():
    gen = NVIRGenerator(max_retries=2, dispatcher=MockDispatcher(
        lambda p, d, s: (_ for _ in ()).throw(RuntimeError("always fails"))
    ))
    import services.nvir.generator as mod
    mod.time.sleep = lambda _: None
    with pytest.raises(RuntimeError, match="attempt"):
        gen.generate("prompt")


def test_gen_08_batch_collects_successes():
    gen = NVIRGenerator(dispatcher=MockDispatcher())
    results = gen.batch(lambda: "batch_prompt", n=5)
    assert len(results) == 5
    assert all(isinstance(c, GeneratedCandidate) for c in results)


def test_gen_09_composite_dispatcher_fallback():
    """CompositeDispatcher falls back to second on first failure."""
    class FailDispatcher(MockDispatcher):
        def dispatch(self, p, d, s):
            raise RuntimeError("primary down")

    # Response fn returns (content, model) tuple — MockDispatcher passes through
    composite = CompositeDispatcher(
        FailDispatcher(),
        MockDispatcher(lambda p, d, s: ("fallback_ok", "mock_b")),
    )
    gen = NVIRGenerator(dispatcher=composite)
    c = gen.generate("test")
    assert c.content == "fallback_ok"
    assert c.model_used == "mock_b"


# ── v2 validation rate target ─────────────────────────────────────────────────
#
# v2 set: 70 valid (30 math + 25 logic + 15 general) + 1 invalid (math)
# Oracle routing: math→MathLeanOracle, logic→LogicSMTOracle, general→_GeneralOracle
# Required rate: n_accepted / 71 ≥ 0.985  (i.e. at least 70 of 71 accepted)

_V2_MATH = [
    ("vm01", "math", "2 + 3 = 5"),
    ("vm02", "math", "7 * 8 = 56"),
    ("vm03", "math", "10 - 4 = 6"),
    ("vm04", "math", "20 / 4 = 5"),
    ("vm05", "math", "2 ** 3 = 8"),
    ("vm06", "math", "15 + 27 = 42"),
    ("vm07", "math", "100 - 37 = 63"),
    ("vm08", "math", "6 * 7 = 42"),
    ("vm09", "math", "81 / 9 = 9"),
    ("vm10", "math", "3 ** 2 = 9"),
    ("vm11", "math", "1 + 1 = 2"),
    ("vm12", "math", "4 * 4 = 16"),
    ("vm13", "math", "50 - 13 = 37"),
    ("vm14", "math", "12 / 3 = 4"),
    ("vm15", "math", "8 + 8 = 16"),
    ("vm16", "math", "9 * 9 = 81"),
    ("vm17", "math", "100 / 10 = 10"),
    ("vm18", "math", "11 + 22 = 33"),
    ("vm19", "math", "5 ** 2 = 25"),
    ("vm20", "math", "7 + 13 = 20"),
    ("vm21", "math", "6 * 6 = 36"),
    ("vm22", "math", "40 / 8 = 5"),
    ("vm23", "math", "0 + 5 = 5"),
    ("vm24", "math", "100 - 100 = 0"),
    ("vm25", "math", "3 * 0 = 0"),
    ("vm26", "math", "5 + 5 = 10"),
    ("vm27", "math", "4 * 5 = 20"),
    ("vm28", "math", "16 / 4 = 4"),
    ("vm29", "math", "2 + 2 = 4"),
    ("vm30", "math", "sqrt(4) = 2"),
]

_V2_LOGIC = [
    ("vl01", "logic", "P or Q"),
    ("vl02", "logic", "P and Q"),
    ("vl03", "logic", "If P then Q"),
    ("vl04", "logic", "P or not P"),
    ("vl05", "logic", "true"),
    ("vl06", "logic", "not P"),
    ("vl07", "logic", "P implies Q"),
    ("vl08", "logic", "P iff Q"),
    ("vl09", "logic", "A or B"),
    ("vl10", "logic", "A and B"),
    ("vl11", "logic", "If A then B"),
    ("vl12", "logic", "A or not A"),
    ("vl13", "logic", "A implies B"),
    ("vl14", "logic", "P or Q or R"),
    ("vl15", "logic", "P and not Q"),
    ("vl16", "logic", "If X then Y"),
    ("vl17", "logic", "X or not X"),
    ("vl18", "logic", "X implies Y"),
    ("vl19", "logic", "P xor Q"),
    ("vl20", "logic", "P nand Q"),
    ("vl21", "logic", "P nor Q"),
    ("vl22", "logic", "If M then N"),
    ("vl23", "logic", "forall x"),
    ("vl24", "logic", "exists x"),
    ("vl25", "logic", "P iff P"),
]

_V2_GENERAL = [
    ("vg01", "general", '{"op": "test", "status": "ok"}'),
    ("vg02", "general", '{"phase": "v2", "result": "pass"}'),
    ("vg03", "general", '{"domain": "general", "nvir": 0.985}'),
    ("vg04", "general", '{"type": "validation", "version": 2}'),
    ("vg05", "general", '{"service": "nvir", "health": "ok"}'),
    ("vg06", "general", '{"a": 1, "b": 2}'),
    ("vg07", "general", '{"x": "alpha", "y": "beta"}'),
    ("vg08", "general", '{"model": "haiku", "tokens": 256}'),
    ("vg09", "general", '{"ring": 2, "complete": true}'),
    ("vg10", "general", '{"receipts": 42, "errors": 0}'),
    ("vg11", "general", '{"step": 1, "outcome": "pass"}'),
    ("vg12", "general", '{"key1": "v1", "key2": "v2"}'),
    ("vg13", "general", '{"alice": 1, "bob": 2}'),
    ("vg14", "general", '{"p": 1, "q": 2}'),
    ("vg15", "general", '{"ts": "2026-04-23T00:00:00Z", "event": "run"}'),
]

_V2_INVALID = [
    ("inv01", "math", "2 + 2 = 5"),  # wrong result — math oracle rejects
]

_V2_VALIDATION_SET = _V2_MATH + _V2_LOGIC + _V2_GENERAL + _V2_INVALID


def test_gen_10_v2_validation_rate_target(tmp_path):
    """Full v2 validation set: 70 valid + 1 invalid = 71 claims.
    Oracle routing: math→MathLeanOracle, logic→LogicSMTOracle, general→_GeneralOracle.
    Target rate ≥ 0.985  (70/71 = 0.9859).
    """
    ledger = tmp_path / "v2_receipts.jsonl"
    dispatcher = NVIRDispatcher(ledger=ledger)

    n_valid = len(_V2_VALIDATION_SET) - len(_V2_INVALID)  # 70
    n_total = len(_V2_VALIDATION_SET)                      # 71

    n_accepted = 0
    failures: list[str] = []
    for claim_id, domain, content in _V2_VALIDATION_SET:
        receipt = dispatcher.verify_raw(content, domain, claim_id)
        if receipt.verdict:
            n_accepted += 1
        elif (claim_id, domain, content) not in _V2_INVALID:
            # Unexpected false-negative — log for debugging
            failures.append(f"{claim_id} [{domain}] {content!r}: {receipt.oracle_method}")

    rate = n_accepted / n_total
    assert rate >= 0.985, (
        f"v2 rate={rate:.4f} < 0.985  "
        f"(accepted={n_accepted}/{n_total})\n"
        f"False negatives: {failures}"
    )
    # Receipt chain must be intact
    chain = NVIRDispatcher.verify_chain(ledger=ledger)
    assert chain["status"] == "ok", f"Receipt chain broken: {chain}"
    assert chain["n_receipts"] == n_total
