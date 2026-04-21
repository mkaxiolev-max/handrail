"""Ω-Logos runtime core — receipt-chained orchestration.
AXIOLEV Holdings LLC © 2026. (Implements knowing-doing symmetry, I₆.C3.)"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Any, Callable, Dict, List, Optional
import hashlib, json, time, uuid
from .autonomy import Tier, gate, DEFAULT_CEILING
from .failures import Class as F, COUNTER

@dataclass
class Receipt:
    id: str
    ts: float
    stage: str          # perception | inquiry | adjudication | execution | lineage | governance | autonomy
    intent_hash: str
    payload: Dict[str, Any]
    parent_id: Optional[str] = None
    signature: Optional[str] = None  # SHA-256 over (parent_id || payload_json)

    @staticmethod
    def make(stage: str, intent_hash: str, payload: Dict[str, Any], parent_id: Optional[str] = None) -> "Receipt":
        rid = str(uuid.uuid4())
        body = json.dumps({"parent": parent_id or "", "payload": payload}, sort_keys=True).encode()
        sig = hashlib.sha256(body).hexdigest()
        return Receipt(id=rid, ts=time.time(), stage=stage, intent_hash=intent_hash,
                       payload=payload, parent_id=parent_id, signature=sig)

@dataclass
class RunState:
    run_id: str
    intent: str
    intent_hash: str
    tier: Tier
    receipts: List[Receipt] = field(default_factory=list)
    ended: bool = False

def intent_hash(intent: str) -> str:
    return hashlib.sha256(intent.encode("utf-8")).hexdigest()

class Orchestrator:
    """Perception → Inquiry → Adjudication → Execution → Lineage → Governance → Autonomy."""
    def __init__(self, tier: Tier = DEFAULT_CEILING):
        self.tier = gate(tier)
        self.runs: Dict[str, RunState] = {}

    def begin(self, intent: str, tier: Optional[Tier] = None) -> RunState:
        t = gate(tier or self.tier)
        rid = str(uuid.uuid4())
        st = RunState(run_id=rid, intent=intent, intent_hash=intent_hash(intent), tier=t)
        self.runs[rid] = st
        st.receipts.append(Receipt.make("perception", st.intent_hash, {"intent": intent, "tier": int(t)}))
        return st

    def step(self, st: RunState, stage: str, payload: Dict[str, Any]) -> Receipt:
        parent = st.receipts[-1].id if st.receipts else None
        r = Receipt.make(stage, st.intent_hash, payload, parent_id=parent)
        st.receipts.append(r)
        return r

    def end(self, st: RunState, result: Dict[str, Any]) -> Receipt:
        r = self.step(st, "lineage", {"result": result, "receipt_count": len(st.receipts)})
        st.ended = True
        return r

    def to_dict(self, st: RunState) -> Dict[str, Any]:
        return {
            "run_id": st.run_id,
            "intent": st.intent,
            "intent_hash": st.intent_hash,
            "tier": int(st.tier),
            "ended": st.ended,
            "receipts": [asdict(r) for r in st.receipts],
        }
