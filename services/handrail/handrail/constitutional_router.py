import json
from typing import Dict,Any
from datetime import datetime
from services.handrail.handrail.kernel.dignity_kernel import DignityKernel
from services.handrail.handrail.kernel.yubikey_quorum import YubiKeyQuorum
from services.handrail.handrail.kernel.algebraic_gates_engine import AlgebraicGatesEngine
from services.handrail.handrail.kernel.CPS_BLOCK_2_RETURNBLOCK_BUILDER_V3 import ReturnBlockBuilderV3
from services.alexandria.ledger_atomic import LedgerAtomicity
class ConstitutionalRouter:
 def __init__(self):self.dignity=DignityKernel();self.quorum=YubiKeyQuorum();self.gates=AlgebraicGatesEngine();self.ledger=LedgerAtomicity();self.routing_log=[]
 def route_intent_to_execution(self,intent:Dict[str,Any],phi_instruction:str)->Dict[str,Any]:
  try:
   kdr=self.quorum.dispatch_with_quorum(intent)
   if kdr.get('status')=="QUORUM_FAILED":return{"status":"REJECTED","reason":"quorum_failed","timestamp":datetime.utcnow().isoformat()+"Z"}
   gates_result=self.gates.execute_all_gates(phi_instruction)
   if gates_result.get('status')!="ACCEPTED":return{"status":"REJECTED","reason":"gates_failed","gates_passed":gates_result.get('gates_passed'),"timestamp":datetime.utcnow().isoformat()+"Z"}
   rb_builder=ReturnBlockBuilderV3()
   rb=rb_builder.from_kernel_decision(kdr,{"all_ok":True,"ops":["ROUTED"]},{"ok":True,"summary":"Constitutional routing complete"})
   dignity_valid,dignity_msg=self.dignity.enforce_dignity_invariants(rb)
   if not dignity_valid:return{"status":"REJECTED","reason":dignity_msg,"timestamp":datetime.utcnow().isoformat()+"Z"}
   success,entry_hash=self.ledger.append_atomic(rb,"constitutional_route")
   if not success:return{"status":"REJECTED","reason":"ledger_append_failed","timestamp":datetime.utcnow().isoformat()+"Z"}
   self.routing_log.append({"intent_id":intent.get('intent_id'),"kdr_id":kdr.get('receipt_id'),"entry_hash":entry_hash,"status":"ROUTED","timestamp":datetime.utcnow().isoformat()+"Z"})
   return{"status":"ACCEPTED","kdr_id":kdr.get('receipt_id'),"entry_hash":entry_hash,"gates_passed":gates_result.get('gates_passed'),"timestamp":datetime.utcnow().isoformat()+"Z"}
  except Exception as e:return{"status":"ERROR","reason":str(e),"timestamp":datetime.utcnow().isoformat()+"Z"}
