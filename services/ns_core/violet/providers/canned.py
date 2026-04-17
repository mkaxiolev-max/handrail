"""Canned provider — static corpus, never fabricates."""
import hashlib

_CORPUS = [
    "NS∞ is operating. Dignity preserved.",
    "Alexandria receipts confirm operational state.",
    "Canonical axioms enforced. No violations detected.",
    "Π engine reports admissible.",
    "Ring 6 constitutional core active.",
]


async def call(prompt: str, timeout: float = 5.0):
    idx = int(hashlib.md5(prompt.encode()).hexdigest(), 16) % len(_CORPUS)
    return _CORPUS[idx], 0
