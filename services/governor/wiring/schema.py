from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict
import hashlib, json, time

@dataclass
class AxiolevReceipt:
    entry_id: str; parent_hash: str; zone: str; score: float
    delta: Optional[float]=None; drift_ewma: Optional[float]=None
    drift_sigma: Optional[float]=None; instrument_id: str="MASTER"
    timestamp: float=field(default_factory=time.time)

    def hash(self) -> str:
        return hashlib.sha256(json.dumps(asdict(self),sort_keys=True).encode()).hexdigest()

    def to_ledger_entry(self) -> Dict:
        return {"entry_id":self.entry_id,"parent":self.parent_hash,
                "axiolev.zone":self.zone,"axiolev.score":self.score,
                "axiolev.delta":self.delta,"axiolev.drift_ewma":self.drift_ewma,
                "axiolev.drift_sigma":self.drift_sigma,"axiolev.instrument_id":self.instrument_id,
                "axiolev.receipt_hash":self.hash(),"timestamp":self.timestamp}
