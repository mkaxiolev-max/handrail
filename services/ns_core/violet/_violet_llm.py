"""_violet_llm — 6-provider fallback chain.

Chain: Groq → Grok → Ollama → Anthropic → OpenAI → canned.
Each provider ≤5s timeout, fail to next on timeout or non-200.
canned responds from static corpus — never fabricates.
Secrets: env-var presence check only, NEVER logged.
Emits ReturnBlock.v2 with artifacts[{provider, tokens}].
"""
from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

log = logging.getLogger("violet.llm")

_PROVIDERS = ["groq", "grok", "ollama", "anthropic", "openai", "canned"]
_TIMEOUT = 5.0


def _rb(ok: bool, provider: str, text: str, tokens: int, errors: List[str]) -> Dict[str, Any]:
    return {
        "return_block_version": 2,
        "ok": ok,
        "rc": 0 if ok else 1,
        "operation": "violet.llm",
        "failure_reason": None if ok else "all_providers_failed",
        "artifacts": [{"provider": provider, "tokens": tokens, "text": text}],
        "checks": [{"provider_errors": errors}],
        "state_change": None,
        "warnings": [],
        "receipt_id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "dignity_banner": "AXIOLEV HOLDINGS LLC — DIGNITY PRESERVED",
    }


class VioletLLM:
    async def complete(self, prompt: str) -> Dict[str, Any]:
        errors: List[str] = []
        for name in _PROVIDERS:
            try:
                mod = __import__(f"violet.providers.{name}", fromlist=["call"])
                text, tokens = await asyncio.wait_for(mod.call(prompt), timeout=_TIMEOUT)
                log.info("violet.llm: provider=%s tokens=%d", name, tokens)
                return _rb(True, name, text, tokens, errors)
            except Exception as e:
                log.warning("violet.llm: provider=%s failed: %s", name, type(e).__name__)
                errors.append(f"{name}: {type(e).__name__}")
        return _rb(False, "none", "", 0, errors)
