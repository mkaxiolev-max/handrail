import json
from typing import Dict,Any,List
from datetime import datetime
from enum import Enum
class NeverEvent(Enum):
 DECISION_NULL="decision.allowed is None"
 EXECUTION_NULL="execution.all_ok is None"
 OUTPUT_NULL="result.output_ok is None"
 VIOLATIONS_NULL="violations is None"
 VIOLATIONS_NOT_LIST="violations is not list"
 LEDGER_TAMPER="merkle chain broken"
 QUORUM_FAIL="yubikey quorum not satisfied"
class DignityKernel:
 def __init__(self):self.never_events=[];self.constitutional_state="ACTIVE"
 def validate_never_event(self,rb:Dict[str,Any])->tuple:
  if rb.get('decision',{}).get('allowed')is None:return False,NeverEvent.DECISION_NULL
  if rb.get('execution',{}).get('all_ok')is None:return False,NeverEvent.EXECUTION_NULL
  if rb.get('result',{}).get('output_ok')is None:return False,NeverEvent.OUTPUT_NULL
  if rb.get('violations')is None:return False,NeverEvent.VIOLATIONS_NULL
  if not isinstance(rb.get('violations'),list):return False,NeverEvent.VIOLATIONS_NOT_LIST
  return True,None
 def enforce_dignity_invariants(self,rb:Dict[str,Any])->tuple:
  valid,never=self.validate_never_event(rb)
  if not valid:self.never_events.append({"timestamp":datetime.utcnow().isoformat()+"Z","violation":never.value if never else "UNKNOWN"});return False,f"DIGNITY_VIOLATION:{never.value if never else 'UNKNOWN'}"
  return True,"DIGNITY_ENFORCED"
 def audit_trail(self)->List[Dict[str,Any]]:return self.never_events
