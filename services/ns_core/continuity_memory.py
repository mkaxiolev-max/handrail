"""Continuity Memory — bounded thread awareness"""
from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class ContinuityMemory:
    thread_id: str
    thread_topic: str
    unresolved_issues: list
    recent_receipts: list
    prior_advice: Optional[str]
    prior_clarifications: dict
    effective_response_shapes: list
    interruption_points: list
    created_at: str
    updated_at: str

    def add_receipt(self, receipt_ref: str):
        self.recent_receipts = [receipt_ref] + self.recent_receipts[:4]
        self.updated_at = datetime.utcnow().isoformat()

    def mark_resolved(self, issue: str):
        if issue in self.unresolved_issues:
            self.unresolved_issues.remove(issue)
        self.updated_at = datetime.utcnow().isoformat()
