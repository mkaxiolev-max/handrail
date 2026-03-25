"""Receipt generation and merkle chaining."""
import hashlib
import json
from typing import Optional
class ReceiptEngine:
    def __init__(self):
        self.chain = []
        self.last_hash = '0' * 64
    def generate_receipt(self, action: str, ok: bool, result: dict, error: Optional[str] = None) -> dict:
        payload = json.dumps({'action': action, 'ok': ok, 'result': result, 'error': error}, sort_keys=True)
        merkle = hashlib.sha256(payload.encode()).hexdigest()
        receipt = {
            'merkle_hash': merkle,
            'parent_hash': self.last_hash,
            'action': action,
            'ok': ok,
            'timestamp': self._timestamp(),
        }
        self.chain.append(receipt)
        self.last_hash = merkle
        return receipt
    def _timestamp(self) -> str:
        from datetime import datetime
        return datetime.utcnow().isoformat()
    def verify_chain(self) -> bool:
        prev = '0' * 64
        for r in self.chain:
            if r['parent_hash'] != prev:
                return False
            prev = r['merkle_hash']
        return True
