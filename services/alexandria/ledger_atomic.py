import json, hashlib, threading
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Tuple
class LedgerAtomicity:
    def __init__(self, ledger_path: str = "/Volumes/NSExternal/ether/alexandria_ledger.jsonl"):
        self.ledger_path = Path(ledger_path)
        self.lock = threading.RLock()
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
    def append_atomic(self, rb: Dict[str, Any], cps_id: str, prev_hash: str = None) -> Tuple[bool, str]:
        with self.lock:
            try:
                if rb.get('version') != "3":
                    return False, "RB version must be 3"
                entry_data = {"timestamp": datetime.utcnow().isoformat() + "Z", "cps_id": cps_id, "rb_version": rb.get('version'), "rb_hash": hashlib.sha256(json.dumps(rb, sort_keys=True, default=str).encode()).hexdigest(), "prev_hash": prev_hash, "rb_status": rb.get('status')}
                entry_hash = hashlib.sha256(json.dumps(entry_data).encode()).hexdigest()
                entry_data["entry_hash"] = entry_hash
                with open(self.ledger_path, 'a') as f:
                    f.write(json.dumps(entry_data) + '\n')
                    f.flush()
                return True, entry_hash
            except Exception as e:
                return False, str(e)
