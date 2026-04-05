import json, logging
from pathlib import Path
from typing import Dict, List, Optional, Any
import os

_log = logging.getLogger("lexicon_substrate")
_LEXICON_PATH = Path("/Volumes/NSExternal/.run/lexicon_seeds.jsonl")
_FALLBACK_PATH = Path(os.environ.get("HR_WORKSPACE", "/app")) / ".run" / "lexicon_seeds.jsonl"

_LEXICON_CACHE: Optional[Dict[str, dict]] = None

def load_lexicon() -> Dict[str, dict]:
    global _LEXICON_CACHE
    if _LEXICON_CACHE is not None:
        return _LEXICON_CACHE
    for path in (_LEXICON_PATH, _FALLBACK_PATH):
        if path.exists():
            try:
                entries = {}
                for line in path.read_text().splitlines():
                    if not line.strip(): continue
                    e = json.loads(line)
                    entries[e["word"].lower()] = e
                _LEXICON_CACHE = entries
                _log.info("Lexicon loaded: %d entries from %s", len(entries), path)
                return entries
            except Exception as ex:
                _log.warning("load_lexicon: %s", ex)
    _LEXICON_CACHE = {}
    return {}

def get_tier(word: str) -> Optional[int]:
    return load_lexicon().get(word.lower(), {}).get("tier")

def get_engine_component(word: str) -> Optional[str]:
    return load_lexicon().get(word.lower(), {}).get("engine_component")

def get_failure_mode(word: str) -> Optional[str]:
    return load_lexicon().get(word.lower(), {}).get("failure_mode")

def get_ns_mapping(word: str) -> Optional[str]:
    return load_lexicon().get(word.lower(), {}).get("ns_mapping")

def analyze_intent(text: str) -> Dict[str, Any]:
    """Scan text for lexicon words. Returns constitutional vocabulary analysis."""
    lexicon = load_lexicon()
    text_lower = text.lower()
    words_found = []
    tiers_present = set()
    engine_components = []
    failure_modes = []
    for word, entry in lexicon.items():
        if word in text_lower:
            words_found.append({
                "word": word,
                "tier": entry.get("tier"),
                "engine_component": entry.get("engine_component"),
                "failure_mode": entry.get("failure_mode"),
                "ns_mapping": entry.get("ns_mapping", "")[:80],
            })
            tiers_present.add(entry.get("tier"))
            engine_components.append(entry.get("engine_component"))
            failure_modes.append(entry.get("failure_mode"))
    from collections import Counter
    dominant_component = Counter(engine_components).most_common(1)[0][0] if engine_components else None
    dominant_failure = Counter(failure_modes).most_common(1)[0][0] if failure_modes else None
    max_tier = max(tiers_present) if tiers_present else 0
    constitutional_weight = sum(1 for w in words_found if w["tier"] >= 4)
    return {
        "words_found": words_found,
        "word_count": len(words_found),
        "tiers_present": sorted(tiers_present),
        "max_tier": max_tier,
        "dominant_engine_component": dominant_component,
        "dominant_failure_mode": dominant_failure,
        "constitutional_weight": constitutional_weight,
        "is_constitutional_intent": constitutional_weight >= 2 or max_tier == 5,
    }

def get_status() -> Dict[str, Any]:
    lexicon = load_lexicon()
    from collections import Counter
    tier_dist = dict(Counter(e.get("tier") for e in lexicon.values()))
    priority_p1 = sum(1 for e in lexicon.values() if e.get("priority") == "P1")
    return {
        "loaded": len(lexicon) > 0,
        "entry_count": len(lexicon),
        "tier_distribution": {str(k): v for k, v in sorted(tier_dist.items()) if k},
        "priority_p1_count": priority_p1,
        "path": str(_LEXICON_PATH if _LEXICON_PATH.exists() else _FALLBACK_PATH),
    }
