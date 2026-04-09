from pydantic import BaseModel
from typing import Optional
import hashlib, json


class ProofReceipt(BaseModel):
    """Immutable proof that an action was taken and recorded."""
    event: str
    payload: dict
    hash: str
    prev_hash: Optional[str] = None
    timestamp: str
    signature: Optional[str] = None

    def content_hash(self) -> str:
        content = json.dumps({"event": self.event, "payload": self.payload, "prev_hash": self.prev_hash}, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()

    def verify_chain(self, prev_receipt: Optional["ProofReceipt"]) -> bool:
        if prev_receipt is None:
            return self.prev_hash is None
        return self.prev_hash == prev_receipt.hash
