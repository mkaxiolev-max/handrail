"""Never-event corpus loader."""
from __future__ import annotations

import json
import os
from typing import Dict, List

def _find_corpus_dir() -> str:
    if os.environ.get("NEVER_EVENTS_DIR"):
        return os.environ["NEVER_EVENTS_DIR"]
    path = os.path.abspath(os.getcwd())
    for _ in range(6):
        candidate = os.path.join(path, "tests/pi/never_events")
        if os.path.isdir(candidate):
            return candidate
        path = os.path.dirname(path)
    return os.path.join(os.path.dirname(__file__), "../../../../tests/pi/never_events")


_DEFAULT_CORPUS_DIR = _find_corpus_dir()


def load_never_events(corpus_dir: str = _DEFAULT_CORPUS_DIR) -> List[Dict]:
    events = []
    if not os.path.isdir(corpus_dir):
        return events
    for fname in sorted(os.listdir(corpus_dir)):
        if fname.endswith(".json"):
            with open(os.path.join(corpus_dir, fname)) as f:
                try:
                    events.append(json.load(f))
                except Exception:
                    pass
    return events
