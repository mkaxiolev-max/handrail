from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict

@dataclass
class TierState:
    global_tier: int  # 0,2,3
    isolated_domains: Dict[str, bool]

class TierLatch:
    def __init__(self, state_path: Path):
        self.state_path = state_path
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.state_path.exists():
            self._write(TierState(global_tier=0, isolated_domains={}))

    def _read(self) -> TierState:
        d = json.loads(self.state_path.read_text())
        return TierState(global_tier=int(d["global_tier"]), isolated_domains=dict(d.get("isolated_domains", {})))

    def _write(self, s: TierState) -> None:
        self.state_path.write_text(json.dumps({"global_tier": s.global_tier, "isolated_domains": s.isolated_domains}, indent=2))

    def get(self) -> TierState:
        return self._read()

    def set_global_tier(self, tier: int) -> TierState:
        s = self._read()
        if s.global_tier == 3:
            return s
        if tier == 3:
            s.global_tier = 3
        elif tier == 2 and s.global_tier == 0:
            s.global_tier = 2
        self._write(s)
        return s

    def isolate_domain(self, domain_id: str) -> TierState:
        s = self._read()
        s.isolated_domains[domain_id] = True
        if s.global_tier == 0:
            s.global_tier = 2
        self._write(s)
        return s
