"""INS-02 NVIR Generator — production generator stack tests.
© 2026 AXIOLEV Holdings LLC
"""
from __future__ import annotations

import time

import pytest

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
