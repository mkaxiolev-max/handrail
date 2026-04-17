"""Anthropic provider."""
import os, logging
log = logging.getLogger("violet.anthropic")

async def call(prompt: str, timeout: float = 5.0):
    import httpx
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not key:
        raise ValueError("ANTHROPIC_API_KEY not set")
    async with httpx.AsyncClient(timeout=timeout) as c:
        r = await c.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": key,
                "anthropic-version": "2023-06-01",
            },
            json={
                "model": "claude-haiku-4-5-20251001",
                "max_tokens": 512,
                "messages": [{"role": "user", "content": prompt}],
            },
        )
        r.raise_for_status()
        d = r.json()
        text = d["content"][0]["text"]
        tokens = d.get("usage", {}).get("output_tokens", 0)
        return text, tokens
