"""Memory + Lineage layer — Alexandria append-only hook.
AXIOLEV Holdings LLC © 2026. (Maps to I₆.C4 — replay_success_rate.)"""
import json, os
from dataclasses import asdict
from typing import List
from ..runtime.core import Receipt

ALEXANDRIA = os.environ.get("ALEXANDRIA", "/Volumes/NSExternal/ALEXANDRIA")
LEDGER = os.path.join(ALEXANDRIA, "omega_logos", "receipts.jsonl")

def persist(r: Receipt) -> bool:
    try:
        os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
        with open(LEDGER, "a") as f: f.write(json.dumps(asdict(r)) + "\n")
        return True
    except Exception:
        return False

def replay() -> List[Receipt]:
    out: List[Receipt] = []
    if not os.path.exists(LEDGER): return out
    with open(LEDGER) as f:
        for ln in f:
            try:
                d = json.loads(ln)
                out.append(Receipt(**d))
            except Exception:
                pass
    return out
