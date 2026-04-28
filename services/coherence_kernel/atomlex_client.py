"""Async httpx client for Atomlex embedding service (port 8080)."""
from __future__ import annotations
import asyncio, hashlib
from typing import Any

try:
    import httpx
    _HAS_HTTPX = True
except ImportError:
    _HAS_HTTPX = False

ATOMLEX_BASE = "http://127.0.0.1:8080"
_EMBED_DIM = 128


def _deterministic_embedding(text: str) -> list[float]:
    """Fallback: deterministic pseudo-embedding from sha256 digest."""
    h = hashlib.sha256(text.encode()).digest()
    return [(b / 127.5) - 1.0 for b in h[:_EMBED_DIM]]


async def get_embedding(text: str) -> list[float]:
    if not _HAS_HTTPX:
        return _deterministic_embedding(text)
    try:
        async with httpx.AsyncClient(timeout=2.0) as c:
            r = await c.post(f"{ATOMLEX_BASE}/embed", json={"text": text})
            r.raise_for_status()
            return r.json()["embedding"]
    except Exception:
        return _deterministic_embedding(text)


async def get_contradiction_edges(node_id: str) -> list[dict[str, Any]]:
    if not _HAS_HTTPX:
        return []
    try:
        async with httpx.AsyncClient(timeout=2.0) as c:
            r = await c.get(f"{ATOMLEX_BASE}/nodes/{node_id}/contradictions")
            r.raise_for_status()
            return r.json().get("edges", [])
    except Exception:
        return []


def embed_sync(text: str) -> list[float]:
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(1) as ex:
                return ex.submit(asyncio.run, get_embedding(text)).result()
        return loop.run_until_complete(get_embedding(text))
    except Exception:
        return _deterministic_embedding(text)
