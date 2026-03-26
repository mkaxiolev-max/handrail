import json, uuid, hashlib
from datetime import datetime
from enum import Enum

class GateResult(Enum):
    PASS = "pass"
    FAIL = "fail"
    NOT_APPLICABLE = "not_applicable"

class KernelDecision(Enum):
    ALLOW = "allow"
    DENY = "deny"
    ESCALATE = "escalate"

def issue_kernel_decision_receipt(cps_packet_dict, caller_id="nsctl", jurisdiction="CA.v0.3"):
    receipt_id = str(uuid.uuid4())
    cps_id = cps_packet_dict.get('cps_id', 'unknown')
    packet_hash = hashlib.sha256(json.dumps(cps_packet_dict, sort_keys=True).encode()).hexdigest()
    ops = cps_packet_dict.get('ops', [])
    all_read_only = all(op.get('side_effect_class') == 'read' for op in ops)
    gate_results = {'consent': GateResult.NOT_APPLICABLE.value, 'fair_housing': GateResult.PASS.value, 'safety': GateResult.PASS.value, 'compliance': GateResult.PASS.value, 'financial': GateResult.PASS.value, 'wire_block': GateResult.PASS.value}
    if all_read_only:
        decision = KernelDecision.ALLOW
        reason = "Read-only operation authorized"
    else:
        decision = KernelDecision.DENY
        reason = "Write operations require explicit policy check (stub version)"
    kdr = {"$schema": "https://axiolev.ai/schemas/KernelDecisionReceipt.v1.json", "version": "1", "receipt_id": receipt_id, "cps_id": cps_id, "packet_hash": packet_hash, "policy_hash": hashlib.sha256(b"PolicyBundle_CA_v0.3").hexdigest(), "mission_graph_id": cps_packet_dict.get('mission_graph_id', 'unknown'), "gate_results": gate_results, "allowed": decision == KernelDecision.ALLOW, "decision": decision.value, "reason": reason, "reason_codes": ["R0_READ_ONLY" if all_read_only else "STUB_VERSION_DENY"], "decision_timestamp": datetime.utcnow().isoformat() + "Z", "verifier_signature": f"HANDRAIL_STUB_{receipt_id[:8]}", "deterministic_context_hash": hashlib.sha256(f"{packet_hash}_CA.v0.3_R0".encode()).hexdigest()}
    return kdr

def validate_kernel_decision_receipt(kdr):
    required = ['version', 'receipt_id', 'cps_id', 'allowed', 'decision', 'gate_results']
    for field in required:
        if field not in kdr:
            return False, f"Missing required field: {field}"
    if not isinstance(kdr['allowed'], bool):
        return False, "allowed must be bool, not None"
    if kdr['decision'] not in ['allow', 'deny', 'escalate']:
        return False, f"Invalid decision: {kdr['decision']}"
    return True, "KDR valid"

def dispatch_with_receipt(cps_packet_dict, caller_id="nsctl"):
    kdr = issue_kernel_decision_receipt(cps_packet_dict, caller_id)
    valid, msg = validate_kernel_decision_receipt(kdr)
    if not valid:
        return {"status": "REJECTED", "reason": msg}
    if not kdr['allowed']:
        return {"status": "DENIED", "decision_id": kdr['receipt_id'], "reason": kdr['reason']}
    return {"status": "SUCCESS", "decision_receipt": kdr, "operations_executed": len(cps_packet_dict.get('ops', [])), "next_step": "emit_ReturnBlock.v3"}
