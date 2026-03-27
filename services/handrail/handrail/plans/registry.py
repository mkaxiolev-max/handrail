from datetime import datetime,timezone
from typing import Any,Dict
import uuid
def build_intent_packet(op:str,payload:Dict[str,Any],session_id:str)->Dict[str,Any]:
 return {"version":"1","intent":op,"args":payload,"constraints":{"timeout_ms":payload.get("timeout_ms",300000),"resource_limits":payload.get("resource_limits",{}),"jurisdiction":payload.get("jurisdiction","internal")},"idempotency_key":str(uuid.uuid4()),"caller_id":"nsctl","session_id":session_id,"timestamp":datetime.now(timezone.utc).isoformat(),"signature":None}
def compile_to_cps(intent_packet:Dict[str,Any])->Dict[str,Any]:
 op=intent_packet["intent"]
 args=intent_packet["args"]
 op_map={"ops_apply_patch":{"cps_id":"plan_apply_patch","policy_profile":"repo.inspect","ops":[{"op":"ops_apply_patch","args":args}],"risk_tier":"R2"},"ops_run_tests":{"cps_id":"plan_run_tests","policy_profile":"readonly.local","ops":[{"op":"ops_run_tests","args":args}],"risk_tier":"R1"},"ops_dev_check":{"cps_id":"plan_dev_check","policy_profile":"readonly.local","ops":[{"op":"ops_dev_check","args":args}],"risk_tier":"R1"}}
 if op not in op_map:raise ValueError(f"unsupported op: {op}")
 base=op_map[op]
 return {"version":"1","objective":op,"policy_profile":base["policy_profile"],"ops":base["ops"],"expect":{},"risk_tier":base["risk_tier"],"mission_graph_id":"plan_runner_v1","provenance":{"caller_id":intent_packet["caller_id"],"session_id":intent_packet["session_id"],"idempotency_key":intent_packet["idempotency_key"],"timestamp":intent_packet["timestamp"]}}
def cps_to_phi(cps:Dict[str,Any])->str:
 obj=cps.get("objective","unknown")
 ops=cps.get("ops",[])
 if not ops:return f"φ:handrail:EXECUTE{{op:{obj}}}"
 first_op=ops[0].get("op","unknown")
 sub_ops=",".join([f"{op.get('op','x')}:{op.get('args',{}).get('patch','').replace(' ','_')[:8]if op.get('args',{}).get('patch')else'default'}"for op in ops])
 return f"φ:handrail:EXECUTE{{{first_op}:{sub_ops}}}"
