"""Groq provider — primary."""
import os, logging
log = logging.getLogger("violet.groq")

async def call(prompt: str, timeout: float = 5.0):
    import asyncio, httpx
    key = os.environ.get("GROQ_API_KEY", "")
    if not key:
        raise ValueError("GROQ_API_KEY not set")
    async with httpx.AsyncClient(timeout=timeout) as c:
        r = await c.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}"},
            json={"model": "llama3-8b-8192", "messages": [{"role": "user", "content": prompt}]},
        )
        r.raise_for_status()
        d = r.json()
        return d["choices"][0]["message"]["content"], d.get("usage", {}).get("completion_tokens", 0)
