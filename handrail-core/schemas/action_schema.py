"""Typed action and receipt schemas for Handrail."""
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional
from datetime import datetime
import json
@dataclass
class ActionRequest:
    action: str
    args: Dict[str, Any]
    permissions_required: List[str]
    request_id: str
    timestamp: str
    def to_dict(self) -> Dict:
        return asdict(self)
@dataclass
class ActionResult:
    action: str
    ok: bool
    result: Optional[Dict[str, Any]]
    error: Optional[str]
    error_class: Optional[str]
    duration_ms: float
    request_id: str
    timestamp: str
    def to_dict(self) -> Dict:
        return asdict(self)
@dataclass
class Receipt:
    request_id: str
    action: str
    ok: bool
    merkle_hash: str
    parent_hash: str
    timestamp: str
    result: ActionResult
    def to_json(self) -> str:
        return json.dumps({
            'request_id': self.request_id,
            'action': self.action,
            'ok': self.ok,
            'merkle_hash': self.merkle_hash,
            'parent_hash': self.parent_hash,
            'timestamp': self.timestamp,
            'result': self.result.to_dict(),
        })
