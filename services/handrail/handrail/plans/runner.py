
import sys,json,time
sys.path.insert(0,'.')
from pathlib import Path
from services.handrail.handrail.plans.schema import PlanSpec
from services.handrail.handrail.kernel.CPS_BLOCK_2_RETURNBLOCK_BUILDER_V3 import ReturnBlockBuilderV3
from services.alexandria.ledger_atomic import LedgerAtomicity
from services.handrail.handrail.adapters.ops_adapters import get_adapter

class PlanRunner:
    def __init__(self,ledger_path):
        self.ledger_path=ledger_path
        self.ledger=LedgerAtomicity(ledger_path)
        self.builder=ReturnBlockBuilderV3()
    
    def run(self,plan: PlanSpec)->dict:
        plan_id=plan.plan_id
        session_id=f"plan_{int(time.time()*1000)}"
        results={"plan_id":plan_id,"session_id":session_id,"steps":{},"ok":True}
        
        for step in plan.steps:
            step_id=step.id
            op_name=step.op
            
            # Get adapter
            adapter=get_adapter(op_name)
            if not adapter:
                results['steps'][step_id]={"status":"FAILED","ok":False,"error":f"unknown op: {op_name}"}
                results['ok']=False
                continue
            
            # Execute adapter
            try:
                result=adapter(step.input)
            except Exception as e:
                result={"ok":False,"output_ok":False,"output":str(e),"status":"error"}
            
            # Build ReturnBlock
            if result.get('output_ok'):
                kdr={"allowed":True,"receipt_id":f"kdr_{step_id}"}
                execution={"all_ok":result.get('ok',False)}
                rb_result={"ok":True,"output_ok":result.get('output_ok',False)}
                
                try:
                    rb=self.builder.from_kernel_decision(kdr,execution,rb_result)
                    success,eh=self.ledger.append_atomic(rb,f"{plan_id}_{step_id}")
                    results['steps'][step_id]={"status":"SUCCESS","ok":True,"return_block":rb}
                except Exception as e:
                    results['steps'][step_id]={"status":"FAILED","ok":False,"error":str(e)}
                    results['ok']=False
            else:
                results['steps'][step_id]={"status":"FAILED","ok":False,"error":"adapter returned output_ok=False"}
                results['ok']=False
        
        return results
