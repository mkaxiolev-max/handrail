import json, hashlib, uuid
from datetime import datetime
from typing import Dict, Any
class ABIViolation(Exception):
    def __init__(self, layer: str, code: str, reason: str):
        self.layer = layer
        self.code = code
        self.reason = reason
        super().__init__(f"[{layer}] {code}: {reason}")
class ReturnBlockBuilderV2:
    def __init__(self, run_id: str = None):
        self.run_id = run_id or str(uuid.uuid4())[:12]
        self.timestamp = datetime.utcnow().isoformat() + "Z"
        self.violations = []
        self.status = "SUCCESS"
    def from_kernel_decision(self, kdr: Dict[str, Any], execution_result: Dict = None, output: Any = None):
        if execution_result is None:
            execution_result = {}
        decision_allowed = kdr.get('allowed', False)
        if decision_allowed is None:
            raise ABIViolation("L2", "L2_002", "decision.allowed cannot be None")
        if not isinstance(decision_allowed, bool):
            raise ABIViolation("L2", "L2_002", f"decision.allowed must be bool")
        decision_section = {"allowed": decision_allowed, "policy_hash": kdr.get('policy_hash'), "decision_id": kdr.get('receipt_id'), "kernel_signature": kdr.get('verifier_signature')}
        execution_all_ok = execution_result.get('all_ok', True)
        if execution_all_ok is None:
            raise ABIViolation("L2", "L2_002", "execution.all_ok cannot be None")
        if not isinstance(execution_all_ok, bool):
            raise ABIViolation("L2", "L2_002", f"execution.all_ok must be bool")
        execution_section = {"ops_executed": execution_result.get('ops', []), "all_ok": execution_all_ok, "adapter_path": execution_result.get('adapter_path', []), "duration_ms": execution_result.get('duration_ms', 0)}
        result_output_ok = output.get('ok', True) if output else True
        if result_output_ok is None:
            raise ABIViolation("L2", "L2_002", "result.output_ok cannot be None")
        if not isinstance(result_output_ok, bool):
            raise ABIViolation("L2", "L2_002", f"result.output_ok must be bool")
        result_section = {"summary": output.get('summary', '') if output else '', "detail": output.get('detail', {}) if output else {}, "output_ok": result_output_ok, "next_action": output.get('next_action') if output else None}
        evidence_section = {"receipts": [kdr.get('receipt_id')], "proof_receipts": [execution_result.get('proof_receipt_id')], "logs": execution_result.get('logs', []), "artifacts": execution_result.get('artifacts', []), "state_hash": self._compute_state_hash(output)}
        replay_section = {"state_hash": evidence_section['state_hash'], "prev_hash": output.get('prev_state_hash') if output else None, "reconstructable": True, "replay_id": f"replay_{self.run_id}"}
        if self.violations is None:
            raise ABIViolation("L1", "L1_001", "violations cannot be None")
        if not isinstance(self.violations, list):
            raise ABIViolation("L1", "L1_001", f"violations must be array")
        return_block = {"$schema": "https://axiolev.ai/schemas/ReturnBlock.v3.json", "version": "3", "run_id": self.run_id, "timestamp": self.timestamp, "status": self.status, "decision": decision_section, "execution": execution_section, "result": result_section, "evidence": evidence_section, "replay": replay_section, "violations": self.violations, "boot_phase": output.get('boot_phase', 'BOOT_12_READY') if output else 'BOOT_12_READY', "risk_tier": output.get('risk_tier', 'R1') if output else 'R1'}
        return return_block
    def _compute_state_hash(self, output=None):
        content = json.dumps(output or {}, sort_keys=True, default=str)
        return hashlib.sha256(content.encode()).hexdigest()
ReturnBlockBuilder = ReturnBlockBuilderV2
