# Copyright © 2026 Axiolev. All rights reserved.
"""
Model Router — intent-class → model selection + arbitration.
Writes ModelOutcomeReceipt to Alexandria ledger.
"""
from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from nss.models.registry import MODEL_REGISTRY, get_registry_with_status

# ---------------------------------------------------------------------------
# Intent → model routing table
# ---------------------------------------------------------------------------

INTENT_ROUTES: dict[str, list[str]] = {
    "voice_quick":  ["analyst"],
    "voice_action": ["analyst", "critic"],   # critic graceful skip if disabled
    "strategy":     ["analyst", "forge", "critic"],
    "high_risk":    ["guardian", "analyst", "forge", "critic", "generalist"],
    "default":      ["analyst"],
}

# ---------------------------------------------------------------------------
# Veil gate — strip context based on model privacy_class
# ---------------------------------------------------------------------------

def _apply_veil(context: str, privacy_class: str) -> str:
    """For full-privacy models (guardian/local), strip cloud-sensitive context."""
    if privacy_class == "full":
        # Strip anything that looks like API keys, phone numbers, or SIDs
        import re
        context = re.sub(r'(?i)(key|token|secret|sid|password)\s*[:=]\s*\S+', '[REDACTED]', context)
    return context

# ---------------------------------------------------------------------------
# Model callers
# ---------------------------------------------------------------------------

def _call_anthropic(prompt: str, context: str, model_id: str, max_tokens: int = 400) -> str:
    import anthropic
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    client = anthropic.Anthropic(api_key=api_key)
    system = "You are NS, the executive intelligence of AXIOLEV Holdings. Respond precisely and concisely."
    if context:
        system += f"\n\nCONTEXT:\n{context}"
    resp = client.messages.create(
        model=model_id,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.content[0].text.strip()


def _call_ollama(prompt: str, context: str, model_id: str) -> str | None:
    """Call local Ollama — graceful skip if not running."""
    try:
        import httpx
        endpoint = MODEL_REGISTRY["guardian"]["endpoint"]
        payload = {"model": model_id, "prompt": prompt, "stream": False}
        resp = httpx.post(endpoint, json=payload, timeout=8)
        if resp.status_code == 200:
            return resp.json().get("response", "").strip()
    except Exception:
        pass
    return None


def _call_stub(model_key: str, prompt: str) -> str | None:
    """Stub for unconfigured external models — returns None (graceful skip)."""
    return None

# ---------------------------------------------------------------------------
# Outcome receipt writer
# ---------------------------------------------------------------------------

_MODEL_DECISIONS_SSD      = Path("/Volumes/NSExternal/ALEXANDRIA/ledger/model_decisions.jsonl")
_MODEL_DECISIONS_FALLBACK = Path.home() / "ALEXANDRIA" / "ledger" / "model_decisions.jsonl"

def _write_outcome_receipt(intent_class: str, model_used: str, latency_ms: float,
                            prompt_len: int, response_len: int) -> None:
    entry = {
        "intent_class": intent_class,
        "model_used": model_used,
        "latency_ms": round(latency_ms, 1),
        "prompt_len": prompt_len,
        "response_len": response_len,
        "ts": datetime.now(timezone.utc).isoformat(),
    }
    try:
        p = (_MODEL_DECISIONS_SSD
             if Path("/Volumes/NSExternal/ALEXANDRIA/ledger").exists()
             else _MODEL_DECISIONS_FALLBACK)
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass

# ---------------------------------------------------------------------------
# ModelRouter
# ---------------------------------------------------------------------------

class ModelRouter:
    def select_models(self, intent_class: str) -> list[str]:
        return INTENT_ROUTES.get(intent_class, INTENT_ROUTES["default"])

    def _is_enabled(self, model_key: str) -> bool:
        m = MODEL_REGISTRY.get(model_key, {})
        env_key = m.get("_enable_env")
        if env_key is None:
            return os.environ.get("OLLAMA_ENABLED", "true").lower() != "false"
        return bool(os.environ.get(env_key, ""))

    def route_sync(self, prompt: str, context: str = "", intent_class: str = "default") -> dict:
        """Synchronous route — call selected models, arbitrate, return result."""
        selected = self.select_models(intent_class)
        start = time.monotonic()
        response: str | None = None
        model_used = "none"
        errors: list[dict] = []

        for model_key in selected:
            m = MODEL_REGISTRY.get(model_key, {})
            if not self._is_enabled(model_key):
                if m.get("graceful_skip", True):
                    continue
                errors.append({"model": model_key, "error": "not configured"})
                continue

            privacy_class = m.get("privacy_class", "private_cloud")
            safe_context = _apply_veil(context, privacy_class)

            try:
                provider = m.get("provider", "")
                if provider == "anthropic":
                    response = _call_anthropic(prompt, safe_context, m["model_id"])
                elif provider == "local_ollama":
                    response = _call_ollama(prompt, safe_context, m["model_id"])
                else:
                    response = _call_stub(model_key, prompt)

                if response:
                    model_used = model_key
                    break  # analyst response wins; critic/forge only used if analyst fails
            except Exception as e:
                errors.append({"model": model_key, "error": str(e)[:200]})
                if not m.get("graceful_skip", True):
                    raise

        latency_ms = (time.monotonic() - start) * 1000
        _write_outcome_receipt(intent_class, model_used, latency_ms,
                               len(prompt), len(response or ""))

        return {
            "ok": response is not None,
            "response": response or "Intelligence layer unavailable.",
            "model_used": model_used,
            "intent_class": intent_class,
            "latency_ms": round(latency_ms, 1),
            "errors": errors,
        }


# Module-level singleton
_router: ModelRouter | None = None

def get_router() -> ModelRouter:
    global _router
    if _router is None:
        _router = ModelRouter()
    return _router
