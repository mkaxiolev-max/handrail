"""Action-Outcome Loop — records actions with their measured outcomes."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class ActionRecord:
    action_id: str
    action: str
    input_summary: str
    output_summary: str
    outcome_score: float   # 0.0–1.0
    success: bool


class ActionOutcomeLoop:
    def __init__(self):
        self._records: list[ActionRecord] = []

    def record_action(self, action: str, input_data: Any, fn: Callable,
                      score_fn: Callable | None = None) -> ActionRecord:
        output = fn(input_data)
        score = score_fn(input_data, output) if score_fn else (1.0 if output is not None else 0.0)
        rid = f"act_{len(self._records):04d}"
        r = ActionRecord(rid, action, str(input_data)[:80], str(output)[:80],
                         round(float(score), 4), score > 0.5)
        self._records.append(r)
        return r

    def analyze(self) -> dict:
        if not self._records:
            return {"total": 0, "success_rate": 0.0, "avg_score": 0.0}
        total = len(self._records)
        successes = sum(1 for r in self._records if r.success)
        return {
            "total": total,
            "success_rate": round(successes / total, 4),
            "avg_score": round(sum(r.outcome_score for r in self._records) / total, 4),
        }

    def records(self) -> list[ActionRecord]:
        return list(self._records)
