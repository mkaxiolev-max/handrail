from pydantic import BaseModel
from typing import Optional


class ComputeReceipt(BaseModel):
    """Tracks cost, latency, and tokens used in a computation."""
    event_id: str
    tokens_input: int
    tokens_output: int
    latency_ms: float
    cost_usd: float
    model: str
    timestamp: str
    budget_remaining: Optional[float] = None

    def total_tokens(self) -> int:
        return self.tokens_input + self.tokens_output
