import json, hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
class MerkleEntry:
    def __init__(self, rb: Dict[str, Any], cps_id: str, prev_hash: Optional[str] = None):
        self.timestamp = datetime.utcnow().isoformat() + "Z"
        self.cps_id = cps_id
        self.rb_version = rb.get('version')
        self.rb_run_id = rb.get('run_id')
        self.status = rb.get('status')
        self.decision_allowed = rb.get('decision', {}).get('allowed')
        self.execution_all_ok = rb.get('execution', {}).get('all_ok')
        self.result_output_ok = rb.get('result', {}).get('output_ok')
        self.violations = rb.get('violations', [])
        self.rb_hash = hashlib.sha256(json.dumps(rb, sort_keys=True, default=str).encode()).hexdigest()
        entry_content = {"timestamp": self.timestamp, "cps_id": self.cps_id, "rb_hash": self.rb_hash, "prev_hash": prev_hash}
        self.entry_hash = hashlib.sha256(json.dumps(entry_content, sort_keys=True).encode()).hexdigest()
        self.prev_hash = prev_hash
    def to_jsonl(self) -> str:
        return json.dumps({"timestamp": self.timestamp, "cps_id": self.cps_id, "rb_version": self.rb_version, "rb_run_id": self.rb_run_id, "rb_status": self.status, "decision_allowed": self.decision_allowed, "execution_all_ok": self.execution_all_ok, "result_output_ok": self.result_output_ok, "violation_count": len(self.violations), "rb_hash": self.rb_hash, "entry_hash": self.entry_hash, "prev_hash": self.prev_hash})
class AlexandriaLedger:
    def __init__(self, ledger_path: str = "/Volumes/NSExternal/ether/alexandria_ledger.jsonl"):
        self.ledger_path = Path(ledger_path)
        self.last_hash = None
        self._load_last_hash()
    def _load_last_hash(self):
        if not self.ledger_path.exists():
            self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
            self.last_hash = None
            return
        try:
            with open(self.ledger_path, 'r') as f:
                lines = f.readlines()
                if lines:
                    last_entry = json.loads(lines[-1].strip())
                    self.last_hash = last_entry.get('entry_hash')
        except Exception:
            self.last_hash = None
    def append(self, rb: Dict[str, Any], cps_id: str) -> str:
        if rb.get('version') != "3":
            raise ValueError("Only ReturnBlock.v3 accepted")
        if rb.get('decision', {}).get('allowed') is None:
            raise ValueError("RB missing decision.allowed")
        if rb.get('execution', {}).get('all_ok') is None:
            raise ValueError("RB missing execution.all_ok")
        if rb.get('result', {}).get('output_ok') is None:
            raise ValueError("RB missing result.output_ok")
        entry = MerkleEntry(rb, cps_id, prev_hash=self.last_hash)
        with open(self.ledger_path, 'a') as f:
            f.write(entry.to_jsonl() + '\n')
        self.last_hash = entry.entry_hash
        return entry.entry_hash
class LedgerVerifier:
    def __init__(self, ledger_path: str = "/Volumes/NSExternal/ether/alexandria_ledger.jsonl"):
        self.ledger_path = Path(ledger_path)
    def verify_chain(self) -> bool:
        if not self.ledger_path.exists():
            return True
        prev_hash = None
        with open(self.ledger_path, 'r') as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    if entry.get('prev_hash') != prev_hash:
                        return False
                    prev_hash = entry.get('entry_hash')
                except:
                    return False
        return True
    def get_statistics(self) -> Dict:
        if not self.ledger_path.exists():
            return {"entries": 0}
        stats = {"entries": 0, "successes": 0, "failures": 0}
        with open(self.ledger_path, 'r') as f:
            for line in f:
                entry = json.loads(line.strip())
                stats["entries"] += 1
                if entry.get('rb_status') == "SUCCESS":
                    stats["successes"] += 1
                else:
                    stats["failures"] += 1
        return stats
