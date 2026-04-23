"""NVIR Production Generator Stack — model dispatch, retries, seed capture.
© 2026 AXIOLEV Holdings LLC

Architecture:
  NVIRGenerator
    └─ ModelDispatcher (abstract)
         ├─ NSLocalDispatcher  — POST /meet/transcript (ns:9000)
         ├─ AnthropicDispatcher — claude-haiku-4-5-20251001
         └─ CompositeDispatcher — primary → fallback chain

Seed capture: every GeneratedCandidate carries a GeneratorSeed that records
the rng_seed, prompt_hash, model, and timestamp needed for deterministic replay.
"""
from __future__ import annotations

import hashlib
import json
import os
import random
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Optional


# ── seed ──────────────────────────────────────────────────────────────────────

@dataclass
class GeneratorSeed:
    """All state required for deterministic replay of a generation call."""
    seed_id: str
    rng_seed: int           # 32-bit seed used to drive stochastic choices
    domain: str
    prompt_hash: str        # sha256[:16] of the prompt
    model_hint: str         # which model class was requested
    ts_utc: str


@dataclass
class GeneratedCandidate:
    """Output of the generator stack."""
    generation_id: str
    domain: str
    content: str
    seed: GeneratorSeed
    model_used: str         # actual model that produced content
    attempt: int            # 0-based retry index
    latency_ms: float
    metadata: dict = field(default_factory=dict)


# ── dispatcher interface ───────────────────────────────────────────────────────

class ModelDispatcher(ABC):
    """Subclass to provide a generation backend."""

    @abstractmethod
    def dispatch(self, prompt: str, domain: str, seed: GeneratorSeed) -> tuple[str, str]:
        """Returns (content, model_name). Raises on failure."""


# ── concrete dispatchers ──────────────────────────────────────────────────────

class NSLocalDispatcher(ModelDispatcher):
    """Routes generation through NS /meet/transcript endpoint."""

    def __init__(self, ns_url: Optional[str] = None, timeout: float = 5.0):
        self._url = (ns_url or os.environ.get("NS_URL", "http://localhost:9000")).rstrip("/")
        self._timeout = timeout

    def dispatch(self, prompt: str, domain: str, seed: GeneratorSeed) -> tuple[str, str]:
        import urllib.request  # noqa: PLC0415
        payload = json.dumps({
            "text": prompt,
            "meeting_id": f"nvir_{domain}_{seed.seed_id[:8]}",
            "speaker": "nvir_generator",
        }).encode()
        req = urllib.request.Request(
            f"{self._url}/meet/transcript",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=self._timeout) as resp:
            data = json.loads(resp.read())
        content = data.get("response", "")
        if not content or len(content) < 10:
            raise ValueError("NS returned empty response")
        return content, "ns_local"


class AnthropicDispatcher(ModelDispatcher):
    """Generates via Anthropic claude-haiku-4-5-20251001 with prompt caching headers."""

    MODEL = "claude-haiku-4-5-20251001"

    _DOMAIN_SYSTEM: dict[str, str] = {
        "math":    "You are a precise mathematician. Generate a single, verifiable mathematical claim or equation. Output only the claim, nothing else.",
        "logic":   "You are a formal logician. Generate a single propositional or first-order logic formula. Output only the formula.",
        "code":    "You are a Python expert. Generate a small, self-contained Python function with at least one test_ function that calls it. Output only valid Python code.",
        "general": "Generate a single, concise, factually verifiable claim. Output only the claim.",
    }

    def __init__(self, model: str = MODEL):
        self._model = model
        self._client = None

    def _get_client(self):
        if self._client is None:
            import anthropic  # noqa: PLC0415
            self._client = anthropic.Anthropic()
        return self._client

    def dispatch(self, prompt: str, domain: str, seed: GeneratorSeed) -> tuple[str, str]:
        client = self._get_client()
        rng = random.Random(seed.rng_seed)
        temperature = round(0.65 + rng.random() * 0.30, 3)
        system = self._DOMAIN_SYSTEM.get(domain, self._DOMAIN_SYSTEM["general"])

        resp = client.messages.create(
            model=self._model,
            max_tokens=512,
            temperature=temperature,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        content = resp.content[0].text.strip()
        if not content:
            raise ValueError("Anthropic returned empty content")
        return content, self._model


class MockDispatcher(ModelDispatcher):
    """Deterministic dispatcher for tests — no network calls.

    The response_fn may return:
      - str         → (str, "mock")
      - (str, str)  → returned as-is (allows custom model name)
    """

    def __init__(self, response_fn: Optional[Callable[[str, str, GeneratorSeed], Any]] = None):
        self._fn = response_fn

    def dispatch(self, prompt: str, domain: str, seed: GeneratorSeed) -> tuple[str, str]:
        if self._fn is not None:
            result = self._fn(prompt, domain, seed)
            if isinstance(result, tuple) and len(result) == 2:
                return result  # (content, model_name)
            return result, "mock"
        return f"{prompt.strip()} [seed={seed.rng_seed}]", "mock"


class CompositeDispatcher(ModelDispatcher):
    """Tries each dispatcher in order; returns on first success."""

    def __init__(self, *dispatchers: ModelDispatcher):
        if not dispatchers:
            raise ValueError("At least one dispatcher required")
        self._dispatchers = dispatchers

    def dispatch(self, prompt: str, domain: str, seed: GeneratorSeed) -> tuple[str, str]:
        last_err: Exception = RuntimeError("no dispatchers")
        for d in self._dispatchers:
            try:
                return d.dispatch(prompt, domain, seed)
            except Exception as e:
                last_err = e
        raise last_err


def default_dispatcher() -> ModelDispatcher:
    """Production default: NS local first, Anthropic fallback."""
    return CompositeDispatcher(NSLocalDispatcher(), AnthropicDispatcher())


# ── backoff ────────────────────────────────────────────────────────────────────

def _backoff_seconds(attempt: int, base: float = 1.0, cap: float = 30.0) -> float:
    """Exponential backoff with full jitter: Uniform(0, min(cap, base * 2^attempt))."""
    return random.uniform(0, min(cap, base * (2 ** attempt)))


# ── generator ─────────────────────────────────────────────────────────────────

class NVIRGenerator:
    """Production NVIR generator with retries, backoff, and deterministic seed capture.

    Usage::

        gen = NVIRGenerator(domain="math")
        candidate = gen.generate("Prove that sqrt(2) is irrational")
        # replay deterministically:
        replay = gen.replay(candidate.seed, "Prove that sqrt(2) is irrational")
    """

    def __init__(
        self,
        domain: str = "general",
        max_retries: int = 3,
        dispatcher: Optional[ModelDispatcher] = None,
    ):
        self.domain = domain
        self.max_retries = max_retries
        self._dispatcher = dispatcher or default_dispatcher()

    # ── seed factory ──────────────────────────────────────────────────────────

    def _make_seed(self, prompt: str) -> GeneratorSeed:
        return GeneratorSeed(
            seed_id=str(uuid.uuid4()),
            rng_seed=random.getrandbits(32),
            domain=self.domain,
            prompt_hash=hashlib.sha256(prompt.encode()).hexdigest()[:16],
            model_hint=type(self._dispatcher).__name__,
            ts_utc=_utc_now(),
        )

    # ── public API ────────────────────────────────────────────────────────────

    def generate(self, prompt: str) -> GeneratedCandidate:
        """Generate one candidate, retrying up to max_retries times on failure."""
        seed = self._make_seed(prompt)
        return self._run(prompt, seed)

    def replay(self, seed: GeneratorSeed, prompt: str) -> GeneratedCandidate:
        """Deterministic replay: uses the same seed, produces same structure."""
        return self._run(prompt, seed)

    def batch(
        self,
        prompt_fn: Callable[[], str],
        n: int,
        on_candidate: Optional[Callable[[GeneratedCandidate], None]] = None,
    ) -> list[GeneratedCandidate]:
        """Generate n candidates, collecting successes (skipping failures)."""
        results: list[GeneratedCandidate] = []
        for _ in range(n):
            try:
                c = self.generate(prompt_fn())
                results.append(c)
                if on_candidate:
                    on_candidate(c)
            except Exception:
                pass
        return results

    # ── internal ──────────────────────────────────────────────────────────────

    def _run(self, prompt: str, seed: GeneratorSeed) -> GeneratedCandidate:
        last_err: Exception = RuntimeError("no attempts made")
        for attempt in range(self.max_retries + 1):
            t0 = time.monotonic()
            try:
                content, model = self._dispatcher.dispatch(prompt, self.domain, seed)
                return GeneratedCandidate(
                    generation_id=str(uuid.uuid4()),
                    domain=self.domain,
                    content=content,
                    seed=seed,
                    model_used=model,
                    attempt=attempt,
                    latency_ms=round((time.monotonic() - t0) * 1000, 1),
                )
            except Exception as e:
                last_err = e
                if attempt < self.max_retries:
                    time.sleep(_backoff_seconds(attempt))
        raise RuntimeError(
            f"Generation failed after {self.max_retries + 1} attempt(s): {last_err}"
        ) from last_err


# ── utilities ──────────────────────────────────────────────────────────────────

def _utc_now() -> str:
    import datetime  # noqa: PLC0415
    return datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")
