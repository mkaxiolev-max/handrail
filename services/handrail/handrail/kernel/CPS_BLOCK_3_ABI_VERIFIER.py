import json
from datetime import datetime

class ABIViolation:
    class Code(str):
        L1_MISSING_FIELD = "L1_001"
        L2_NONE_WHERE_BOOL = "L2_002"
    def __init__(self, layer, code, reason, surface="unknown"):
        self.layer = layer
        self.code = code
        self.reason = reason
        self.surface = surface
        self.timestamp = datetime.utcnow().isoformat() + "Z"
    def to_dict(self):
        return {"layer": self.layer, "code": self.code, "reason": self.reason, "surface": self.surface, "timestamp": self.timestamp}
    def __str__(self):
        return f"[ABI_VIOLATION] Layer {self.layer} ({self.code}): {self.reason}"

class ABIVerifier:
    def __init__(self):
        self.violations = []
    def verify_return_block_at_boundary(self, candidate):
        self.violations = []
        syntax_result = self._layer1_syntax(candidate)
        if syntax_result != "ACCEPT":
            return syntax_result, self._rejection_result()
        semantic_result = self._layer2_semantic(candidate)
        if semantic_result == "REJECT":
            return "REJECT", self._rejection_result()
        return "ACCEPT", candidate
    def _layer1_syntax(self, obj):
        if not isinstance(obj, dict):
            self.violations.append(ABIViolation(1, ABIViolation.Code.L1_MISSING_FIELD, f"ReturnBlock must be dict, got {type(obj).__name__}"))
            return "REJECT"
        required = ['version', 'status', 'decision', 'execution', 'result', 'evidence', 'replay', 'violations']
        for field in required:
            if field not in obj:
                self.violations.append(ABIViolation(1, ABIViolation.Code.L1_MISSING_FIELD, f"Missing: {field}"))
                return "REJECT"
        if obj.get('violations') is None:
            self.violations.append(ABIViolation(1, ABIViolation.Code.L1_MISSING_FIELD, "violations cannot be None"))
            return "REJECT"
        if not isinstance(obj.get('violations'), list):
            self.violations.append(ABIViolation(1, ABIViolation.Code.L1_MISSING_FIELD, f"violations must be array, got {type(obj.get('violations')).__name__}"))
            return "REJECT"
        return "ACCEPT"
    def _layer2_semantic(self, obj):
        decision_allowed = obj.get('decision', {}).get('allowed')
        if decision_allowed is None:
            self.violations.append(ABIViolation(2, ABIViolation.Code.L2_NONE_WHERE_BOOL, "decision.allowed cannot be None", "decision_allowed"))
            return "REJECT"
        execution_all_ok = obj.get('execution', {}).get('all_ok')
        if execution_all_ok is None:
            self.violations.append(ABIViolation(2, ABIViolation.Code.L2_NONE_WHERE_BOOL, "execution.all_ok cannot be None", "execution_all_ok"))
            return "REJECT"
        result_output_ok = obj.get('result', {}).get('output_ok')
        if result_output_ok is None:
            self.violations.append(ABIViolation(2, ABIViolation.Code.L2_NONE_WHERE_BOOL, "result.output_ok cannot be None", "result_output_ok"))
            return "REJECT"
        if not isinstance(decision_allowed, bool):
            self.violations.append(ABIViolation(2, ABIViolation.Code.L2_NONE_WHERE_BOOL, f"decision.allowed must be bool, got {type(decision_allowed).__name__}"))
            return "REJECT"
        if not isinstance(execution_all_ok, bool):
            self.violations.append(ABIViolation(2, ABIViolation.Code.L2_NONE_WHERE_BOOL, f"execution.all_ok must be bool, got {type(execution_all_ok).__name__}"))
            return "REJECT"
        if not isinstance(result_output_ok, bool):
            self.violations.append(ABIViolation(2, ABIViolation.Code.L2_NONE_WHERE_BOOL, f"result.output_ok must be bool, got {type(result_output_ok).__name__}"))
            return "REJECT"
        return "ACCEPT"
    def _rejection_result(self):
        return {"status": "REJECTED", "reason": "ABI validation failed", "violations": [v.to_dict() for v in self.violations], "action": "request_valid_packet"}
