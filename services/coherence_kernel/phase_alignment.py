"""Cosine similarity over Atomlex node embeddings for phase alignment check."""
from __future__ import annotations
import math
from services.coherence_kernel.atomlex_client import embed_sync


def cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return max(-1.0, min(1.0, dot / (na * nb)))


def phase_alignment_check(claim_a: str, claim_b: str) -> float:
    """Returns cosine similarity in [-1, 1]. >0.7 = reinforce; <-0.7 = cancel."""
    ea = embed_sync(claim_a)
    eb = embed_sync(claim_b)
    return cosine(ea, eb)
