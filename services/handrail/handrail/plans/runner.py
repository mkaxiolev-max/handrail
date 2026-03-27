from datetime import datetime,timezone
from pathlib import Path
from typing import Any,Dict
import json,time
from .schema import PlanSpec
from .conditions import should_run
from .registry import build_intent_packet,compile_to_cps,cps_to_phi
from services.handrail.handrail.kernel.algebraic_gates_engine import AlgebraicGatesEngine
from services.handrail.handrail.kernel.CPS_BLOCK_2_RETURNBLOCK_BUILDER_V3 import ReturnBlockBuilderV3
from services.alexandria.ledger_atomic import LedgerAtomicity
class PlanRunner:
 def __init__(self,ledger_path:str="/tmp/plan_runner_ledger.jsonl")->None:self.gates=AlgebraicGatesEngine();self.rb_builder=ReturnBlockBuilderV3();self.ledger=LedgerAtomicity(ledger_path);self.session_id=f"plan_{int(time.time())}"
 def run(self,plan:PlanSpec)->Dict[str,Any]:
  plan.validate()
  context:Dict[str,Any]={"plan_id":plan.plan_id,"session_id":self.session_id,"steps":{},"started_at":self._now()}
  for step in plan.steps:
   if not should_run(step.condition,context):context["steps"][step.id]={"status":"SKIPPED","ok":True,"attempts":0,"reason":"condition_false"};continue
   attempts=0;step_result:Dict[str,Any]|None=None
   while attempts<step.retry.max_attempts:
    attempts+=1
    try:
     intent_packet=build_intent_packet(step.op,step.input,self.session_id)
     cps_packet=compile_to_cps(intent_packet)
     phi_instruction=cps_to_phi(cps_packet)
     gates_result=self.gates.execute_all_gates(phi_instruction)
     if gates_result.get("status")!="ACCEPTED":raise ValueError(f"gates rejected: {gates_result}")
     kdr={"allowed":True,"receipt_id":f"kdr_{self.session_id}_{step.id}"}
     rb=self.rb_builder.from_kernel_decision(kdr,{"all_ok":True,"ops":[step.op]},{"ok":True,"summary":f"{step.op} completed"})
     success,entry_hash=self.ledger.append_atomic(rb,f"{plan.plan_id}_{step.id}")
     if not success:raise ValueError(f"ledger append failed: {entry_hash}")
     step_result={"status":"SUCCESS","ok":True,"attempts":attempts,"phi_instruction":phi_instruction,"gates_result":gates_result,"return_block":rb,"entry_hash":entry_hash}
    except Exception as e:step_result={"status":"FAILED","ok":False,"attempts":attempts,"error":str(e)}
    if step_result["ok"]:break
    if attempts<step.retry.max_attempts and step.retry.backoff_seconds>0:time.sleep(step.retry.backoff_seconds)
   assert step_result is not None;context["steps"][step.id]=step_result
   if not step_result["ok"]and step.halt_on_fail:context["ended_at"]=self._now();context["ok"]=False;return context
  context["ended_at"]=self._now();context["ok"]=all(step.get("ok",False)for step in context["steps"].values());return context
 @staticmethod
 def _now()->str:return datetime.now(timezone.utc).isoformat()
