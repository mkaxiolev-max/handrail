"""Global Efficiency Ledger — tracks computational cost vs outcome across operations."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class LedgerEntry:
    op_id: str
    cost: float
    outcome_score: float
    ts: str
    tags: list[str] = field(default_factory=list)

    @property
    def efficiency(self) -> float:
        return self.outcome_score / self.cost if self.cost > 0 else 0.0


class GlobalEfficiencyLedger:
    def __init__(self):
        self._entries: list[LedgerEntry] = []

    def record(self, op_id: str, cost: float, outcome_score: float,
               tags: list[str] | None = None) -> LedgerEntry:
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        entry = LedgerEntry(op_id, cost, outcome_score, ts, tags or [])
        self._entries.append(entry)
        return entry

    def efficiency_ratio(self) -> float:
        if not self._entries:
            return 0.0
        total_cost = sum(e.cost for e in self._entries)
        total_outcome = sum(e.outcome_score for e in self._entries)
        return total_outcome / total_cost if total_cost > 0 else 0.0

    def summary(self) -> dict:
        n = len(self._entries)
        return {
            "total_ops": n,
            "total_cost": sum(e.cost for e in self._entries),
            "total_outcome": sum(e.outcome_score for e in self._entries),
            "efficiency_ratio": self.efficiency_ratio(),
            "avg_efficiency": (sum(e.efficiency for e in self._entries) / n) if n else 0.0,
        }

    def top_n_efficient(self, n: int = 5) -> list[LedgerEntry]:
        return sorted(self._entries, key=lambda e: e.efficiency, reverse=True)[:n]

    def entries_by_tag(self, tag: str) -> list[LedgerEntry]:
        return [e for e in self._entries if tag in e.tags]
