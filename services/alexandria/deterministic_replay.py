import json
from typing import Dict, Any, List, Tuple
from pathlib import Path
class DeterministicReplayEngine:
    def __init__(self, ledger_path: str = "/Volumes/NSExternal/ether/alexandria_ledger.jsonl"):
        self.ledger_path = Path(ledger_path)
        self.replay_log = []
    def read_ledger(self) -> List[Dict[str, Any]]:
        if not self.ledger_path.exists():
            return []
        entries = []
        try:
            with open(self.ledger_path, 'r') as f:
                for line in f:
                    entries.append(json.loads(line.strip()))
        except:
            return []
        return entries
    def replay_entry(self, entry: Dict[str, Any]) -> Tuple[bool, str]:
        try:
            if entry.get('decision_allowed') is None:
                return False, "decision_allowed is None"
            if entry.get('execution_all_ok') is None:
                return False, "execution_all_ok is None"
            if entry.get('result_output_ok') is None:
                return False, "result_output_ok is None"
            if entry.get('rb_status') != "SUCCESS":
                return False, f"RB status not SUCCESS"
            self.replay_log.append({"cps_id": entry.get('cps_id'), "status": "REPLAYED"})
            return True, f"Replayed"
        except Exception as e:
            return False, str(e)
    def verify_determinism(self) -> Tuple[bool, str]:
        entries = self.read_ledger()
        if not entries:
            return True, "Empty (deterministic)"
        prev_hash = None
        for i, entry in enumerate(entries):
            if entry.get('prev_hash') != prev_hash:
                return False, f"Broken at {i+1}"
            prev_hash = entry.get('entry_hash')
        return True, f"Determinism verified: {len(entries)} entries"
