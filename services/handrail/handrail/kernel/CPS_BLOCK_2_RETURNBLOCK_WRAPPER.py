import json, hashlib, uuid
from datetime import datetime
from typing import Dict, Any

class ReturnBlockBuilder:
    def __init__(self, run_id: str = None):
        self.run_id = run_id or str(uuid.uuid4())[:12]
        self.timestamp = datetime.utcnow().isoformat() + "Z"
        self.violations = []
        self.status = "SUCCESS"
    
    def from_kernel_decision(self, kdr: Dict[str, Any], execution_result: Dict = None, output: Any = None):
        if execution_result is None:
            execution_result = {}
        decision_section = {"allowed": kdr.get('allowed', False), "policy_hash": kdr.get('policy_hash'), "decision_id": kdr.get('receipt_id'), "kernel_signature": kdr.get('verifier_signature')}
        if not isinstance(decision_section['allowed'], bool):
            self.status = "REJECTED"
            return self._build_rejection()
        execution_section = {"ops_executed": execution_result.get('ops', []), "all_ok": execution_result.get('all_ok', True), "adapter_path": execution_result.get('adapter_path', []), "duration_ms": execution_result.get('duration_ms', 0)}
        if not isinstance(execution_section['all_ok'], bool):
            self.status = "REJECTED"
            return self._build_rejection()
        result_section = {"summary": output.get('summary', '') if output else '', "detail": output.get('detail', {}) if output else {}, "output_ok": output.get('ok', True) if output else True, "next_action": output.get('next_action')}
        if not isinstance(result_section['output_ok'], bool):
            self.status = "REJECTED"
            return self._build_rejection()
        evidence_section = {"receipts": [kdr.get('receipt_id')], "proof_receipts": [execution_result.get('proof_receipt_id')], "logs": execution_result.get('logs', []), "artifacts": execution_result.get('artifacts', []), "state_hash": self._compute_state_hash(output)}
        replay_section = {"state_hash": evidence_section['state_hash'], "prev_hash": output.get('prev_state_hash') if output else None, "reconstructable": True, "replay_id": f"replay_{self.run_id}"}
        return_block = {"$schema": "https://axiolev.ai/schemas/ReturnBlock.v3.json", "version": "3", "run_id": self.run_id, "timestamp": self.timestamp, "status": self.status, "decision": decision_section, "execution": execution_section, "result": result_section, "evidence": evidence_section, "replay": replay_section, "violations": self.violations, "boot_phase": output.get('boot_phase', 'BOOT_12_READY') if output else 'BOOT_12_READY', "risk_tier": output.get('risk_tier', 'R1') if output else 'R1'}
        return return_block
    
    def _build_rejection(self):
        return {"version": "3", "run_id": self.run_id, "timestamp": self.timestamp, "status": "REJECTED", "decision": {"allowed": False, "policy_hash": None, "decision_id": None, "kernel_signature": None}, "execution": {"ops_executed": [], "all_ok": False, "adapter_path": [], "duration_ms": 0}, "result": {"summary": "ABI validation failed", "detail": {}, "output_ok": False, "next_action": None}, "evidence": {"receipts": [], "proof_receipts": [], "logs": ["ABI violation detected"], "artifacts": [], "state_hash": None}, "replay": {"state_hash": None, "prev_hash": None, "reconstructable": False, "replay_id": f"replay_{self.run_id}"}, "violations": self.violations, "boot_phase": "BOOT_0_SUBSTRATE", "risk_tier": "R0"}
    
    def _compute_state_hash(self, output=None):
        content = json.dumps(output or {}, sort_keys=True, default=str)
        return hashlib.sha256(content.encode()).hexdigest()

def validate_return_block_v3(rb):
    required_fields = ['version', 'status', 'decision', 'execution', 'result', 'evidence', 'replay', 'violations']
    for field in required_fields:
        if field not in rb:
            return False, f"Missing {field}"
    if not isinstance(rb['violations'], list):
        return False, "violations must be array"
    bool_fields = [('decision.allowed', rb.get('decision', {}).get('allowed')), ('execution.all_ok', rb.get('execution', {}).get('all_ok')), ('result.output_ok', rb.get('result', {}).get('output_ok'))]
    for field_name, value in bool_fields:
        if value is None:
            return False, f"{field_name} cannot be None"
        if not isinstance(value, bool):
            return False, f"{field_name} must be bool"
    return True, "ReturnBlock.v3 valid"
