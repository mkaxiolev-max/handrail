"""Ollama provider — local."""
import logging
log = logging.getLogger("violet.ollama")

async def call(prompt: str, timeout: float = 5.0):
    import httpx
    async with httpx.AsyncClient(timeout=timeout) as c:
        r = await c.post(
            "http://host.docker.internal:11434/api/generate",
            json={"model": "llama3", "prompt": prompt, "stream": False},
        )
        r.raise_for_status()
        d = r.json()
        return d["response"], len(d.get("response", "").split())
