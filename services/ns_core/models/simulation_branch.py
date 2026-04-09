from pydantic import BaseModel
from typing import List


class SimulationBranch(BaseModel):
    """Alternative future outcome of an action."""
    branch_id: str
    intent_id: str
    outcome_description: str
    confidence_score: float  # 0.0–1.0
    veto_gates: List[str]
    side_effects: List[str]
    timestamp: str
