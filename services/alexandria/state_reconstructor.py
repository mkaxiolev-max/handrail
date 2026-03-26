import json, hashlib
from typing import Dict, Any, List, Tuple
from datetime import datetime
class StateReconstructor:
    def __init__(self):
        pass
    def reconstruct_from_ledger(self, ledger_entries: List[Dict[str, Any]]) -> Tuple[bool, Dict[str, Any]]:
        if not ledger_entries:
            return False, {"error": "No ledger entries"}
        final_state = {"timestamp": datetime.utcnow().isoformat() + "Z", "entry_count": len(ledger_entries), "states": []}
        for entry in ledger_entries:
            state_snapshot = {"cps_id": entry.get('cps_id'), "decision_allowed": entry.get('decision_allowed'), "execution_all_ok": entry.get('execution_all_ok'), "result_output_ok": entry.get('result_output_ok'), "entry_hash": entry.get('entry_hash')}
            final_state["states"].append(state_snapshot)
        return True, final_state
    def validate_reconstruction(self, state: Dict[str, Any]) -> Tuple[bool, str]:
        if not state.get("states"):
            return False, "No states"
        for s in state["states"]:
            if s.get("decision_allowed") is None or s.get("execution_all_ok") is None or s.get("result_output_ok") is None:
                return False, "Invalid state"
        return True, f"Valid: {len(state['states'])} states"
