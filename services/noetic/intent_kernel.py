"""Noetic Intent Kernel — maps observed signals to constitutional intent."""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum


class IntentClass(str, Enum):
    QUERY = "query"
    ACTION = "action"
    REFLECTION = "reflection"
    CONSTITUTION = "constitution"
    UNKNOWN = "unknown"


@dataclass
class IntentSignal:
    raw: str
    intent_class: IntentClass
    confidence: float
    constituents: list[str]


KEYWORDS: dict[str, IntentClass] = {
    "what": IntentClass.QUERY, "how": IntentClass.QUERY, "why": IntentClass.QUERY,
    "do": IntentClass.ACTION, "run": IntentClass.ACTION, "execute": IntentClass.ACTION,
    "think": IntentClass.REFLECTION, "reflect": IntentClass.REFLECTION,
    "rights": IntentClass.CONSTITUTION, "dignity": IntentClass.CONSTITUTION,
}


class IntentKernel:
    def __init__(self):
        self._history: list[IntentSignal] = []

    def classify(self, raw: str) -> IntentSignal:
        words = raw.lower().split()
        hits: dict[IntentClass, int] = {}
        for w in words:
            ic = KEYWORDS.get(w)
            if ic:
                hits[ic] = hits.get(ic, 0) + 1
        if hits:
            dominant = max(hits, key=lambda k: hits[k])
            confidence = min(1.0, hits[dominant] / max(len(words), 1) * 3)
        else:
            dominant = IntentClass.UNKNOWN
            confidence = 0.3
        sig = IntentSignal(raw=raw, intent_class=dominant, confidence=round(confidence, 3), constituents=words)
        self._history.append(sig)
        return sig

    def history(self) -> list[IntentSignal]:
        return list(self._history)
