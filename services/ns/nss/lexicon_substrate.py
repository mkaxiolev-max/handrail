"""
Gnoseogenic Lexicon Substrate — NS∞ v1
Loads and indexes the Lexicon seed file. Provides intent analysis
against the 30 P1 semantic primitives across 5 tiers.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

# Primary: Alexandria SSD; fallback: local seed file
_SEED_PATHS = [
    Path("/Volumes/NSExternal/.run/lexicon_seeds.jsonl"),
    Path(os.path.expanduser("~/.axiolev/lexicon_seeds.jsonl")),
]

_LEXICON: list[dict] | None = None


def _load() -> list[dict]:
    global _LEXICON
    if _LEXICON is not None:
        return _LEXICON

    for path in _SEED_PATHS:
        if path.exists():
            entries = []
            with open(path) as fh:
                for line in fh:
                    line = line.strip()
                    if line:
                        try:
                            entries.append(json.loads(line))
                        except Exception:
                            pass
            if entries:
                _LEXICON = entries
                return _LEXICON

    _LEXICON = []
    return _LEXICON


def load_lexicon() -> list[dict]:
    """Return all loaded lexicon entries."""
    return _load()


def get_tier(word: str) -> int | None:
    """Return the tier (1-5) for a word, or None if not found."""
    w = word.lower()
    for entry in _load():
        if entry.get("word", "").lower() == w:
            return entry.get("tier")
    return None


def get_engine_component(word: str) -> str | None:
    """Return the engine_component for a word, or None if not found."""
    w = word.lower()
    for entry in _load():
        if entry.get("word", "").lower() == w:
            return entry.get("engine_component")
    return None


def get_failure_mode(word: str) -> str | None:
    """Return the failure_mode string for a word, or None if not found."""
    w = word.lower()
    for entry in _load():
        if entry.get("word", "").lower() == w:
            return entry.get("failure_mode")
    return None


def get_ns_mapping(word: str) -> dict | None:
    """Return the ns_mapping dict for a word, or None if not found."""
    w = word.lower()
    for entry in _load():
        if entry.get("word", "").lower() == w:
            return entry.get("ns_mapping")
    return None


def analyze_intent(text: str) -> dict[str, Any]:
    """
    Scan `text` for known lexicon words. Return:
      words_found              — list of matched words
      tiers_present            — sorted unique tiers hit
      dominant_engine_component — component with most hits (None if no match)
      failure_modes_detected   — failure modes for matched words
      entry_ids                — entry IDs of matched entries
    """
    entries = _load()
    text_lower = text.lower()

    matched: list[dict] = []
    for entry in entries:
        word = entry.get("word", "").lower()
        if word and word in text_lower:
            matched.append(entry)

    if not matched:
        return {
            "words_found": [],
            "tiers_present": [],
            "dominant_engine_component": None,
            "failure_modes_detected": [],
            "entry_ids": [],
        }

    component_counts: dict[str, int] = {}
    for e in matched:
        c = e.get("engine_component", "unknown")
        component_counts[c] = component_counts.get(c, 0) + 1

    dominant = max(component_counts, key=lambda k: component_counts[k])

    return {
        "words_found": [e["word"] for e in matched],
        "tiers_present": sorted({e["tier"] for e in matched if "tier" in e}),
        "dominant_engine_component": dominant,
        "failure_modes_detected": [
            e["failure_mode"] for e in matched if e.get("failure_mode")
        ],
        "entry_ids": [e["entry_id"] for e in matched if "entry_id" in e],
    }


def status_summary() -> dict[str, Any]:
    """Return a compact status dict for the /lexicon/status endpoint."""
    entries = _load()

    by_tier: dict[int, int] = {}
    by_component: dict[str, int] = {}
    for e in entries:
        t = e.get("tier")
        c = e.get("engine_component", "unknown")
        if t:
            by_tier[t] = by_tier.get(t, 0) + 1
        by_component[c] = by_component.get(c, 0) + 1

    seed_path = next((str(p) for p in _SEED_PATHS if p.exists()), None)

    return {
        "loaded": len(entries) > 0,
        "entry_count": len(entries),
        "seed_path": seed_path,
        "by_tier": {str(k): v for k, v in sorted(by_tier.items())},
        "by_engine_component": dict(sorted(by_component.items())),
        "schema": "abi/schemas/LexiconEntry.v1.json",
    }
