from pydantic import BaseModel
from typing import Literal


class IntelligenceJob(BaseModel):
    """Continuous intelligence production unit."""
    job_id: str
    job_type: str  # refinery, synthesis, proactive
    budget_tokens: int
    expiry_seconds: int
    zone: str  # ether, loom, canon
    created_at: str
    status: Literal["pending", "running", "complete", "failed"]
