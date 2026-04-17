"""Grok (xAI) provider."""
import os, logging
log = logging.getLogger("violet.grok")

async def call(prompt: str, timeout: float = 5.0):
    import httpx
    key = os.environ.get("XAI_API_KEY", "")
    if not key:
        raise ValueError("XAI_API_KEY not set")
    async with httpx.AsyncClient(timeout=timeout) as c:
        r = await c.post(
            "https://api.x.ai/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}"},
            json={"model": "grok-beta", "messages": [{"role": "user", "content": prompt}]},
        )
        r.raise_for_status()
        d = r.json()
        return d["choices"][0]["message"]["content"], d.get("usage", {}).get("completion_tokens", 0)
