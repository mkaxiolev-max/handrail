from pydantic import BaseModel
from typing import List


class MissionGraph(BaseModel):
    """Signed workflow DAG."""
    mission_id: str
    name: str
    steps: List[dict]
    checkpoints: List[dict]
    signature: str
    created_at: str
    target_outcome: str
