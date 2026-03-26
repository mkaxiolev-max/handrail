import json, hashlib, uuid
from datetime import datetime
from typing import Dict, Any
class ABIViolation(Exception):
    def __init__(self, layer: str, code: str, reason: str):
        super().__init__(f"[{layer}] {code}: {reason}")
class ReturnBlockBuilderV3:
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
            raise ABIViolation("L2", "L2_002", "decision.allowed must be bool")
        kdr_hash = hashlib.sha256(json.dumps(kdr, sort_keys=True, default=str).encode()).hexdigest()
        execution_all_ok = execution_result.get('all_ok', True)
        if execution_all_ok is None:
            raise ABIViolation("L2", "L2_002", "execution.all_ok cannot be None")
        result_output_ok = output.get('ok', True) if output else True
        if result_output_ok is None:
            raise ABIViolation("L2", "L2_002", "result.output_ok cannot be None")
        return {"version": "3", "run_id": self.run_id, "timestamp": self.timestamp, "status": self.status, "decision": {"allowed": decision_allowed}, "execution": {"all_ok": execution_all_ok}, "result": {"output_ok": result_output_ok}, "violations": self.violations, "kdr_hash": kdr_hash}
ReturnBlockBuilder = ReturnBlockBuilderV3
