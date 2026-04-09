from pydantic import BaseModel
from typing import List, Optional


class CPSPacket(BaseModel):
    """Intent compiled to typed, executable form."""
    packet_id: str
    intent_id: str
    intent: str
    mode: str
    compiled_ops: List[dict]
    signature: Optional[str] = None
    compiled_at: str
    valid_until: str
