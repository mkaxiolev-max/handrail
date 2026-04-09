from pydantic import BaseModel
from typing import Optional


class IntentPacket(BaseModel):
    """Founder intention, normalized and routing-ready."""
    intent: str
    mode: str  # founder_strategic, founder_command, monitoring, reflective
    context: Optional[str] = None
    program: Optional[str] = None
    timestamp: str
    intent_id: str
