import json
from pathlib import Path
from typing import List, Dict, Any
class LedgerReader:
    def __init__(self, ledger_path: str = "/Volumes/NSExternal/ether/alexandria_ledger.jsonl"):
        self.ledger_path = Path(ledger_path)
    def read_all_entries(self) -> List[Dict[str, Any]]:
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
    def verify_chain_integrity(self) -> tuple:
        entries = self.read_all_entries()
        if not entries:
            return True, "Empty ledger"
        prev_hash = None
        for i, entry in enumerate(entries):
            if entry.get('prev_hash') != prev_hash:
                return False, f"Chain broken at {i+1}"
            prev_hash = entry.get('entry_hash')
        return True, f"Chain verified: {len(entries)} entries"
