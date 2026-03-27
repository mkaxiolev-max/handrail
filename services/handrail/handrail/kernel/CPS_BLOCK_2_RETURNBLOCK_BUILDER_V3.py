import json,hashlib
from typing import Dict,Any
class ABIViolation(Exception):pass
class ReturnBlockBuilderV3:
 def from_kernel_decision(self,kdr:Dict[str,Any],execution:Dict[str,Any],result:Dict[str,Any])->Dict[str,Any]:
  if kdr.get('allowed')is None:raise ABIViolation("[L2] L2_002: decision.allowed cannot be None")
  if execution.get('all_ok')is None:raise ABIViolation("[L2] L2_002: execution.all_ok cannot be None")
  if result.get('output_ok')is None:raise ABIViolation("[L2] L2_002: result.output_ok cannot be None")
  kdr_hash=hashlib.sha256(json.dumps(kdr,sort_keys=True,default=str).encode()).hexdigest()
  intent_json=json.dumps({"kdr":kdr,"execution":execution,"result":result},sort_keys=True,default=str)
  deterministic_hash=hashlib.sha256(intent_json.encode()).hexdigest()
  deterministic_run_id=deterministic_hash[:12]
  deterministic_timestamp=hashlib.sha256(deterministic_hash.encode()).hexdigest()[:19]
  rb={"version":"3","run_id":deterministic_run_id,"timestamp":deterministic_timestamp,"status":"SUCCESS","decision":{"allowed":kdr.get('allowed')},"execution":execution,"result":result,"violations":[],"kdr_hash":kdr_hash}
  return rb
