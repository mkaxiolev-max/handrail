import json,hashlib
from typing import Dict,Any,List
from datetime import datetime
class PolicyObject:
 def __init__(self,domain:str,rules:List[str],version:str="1.0"):self.domain=domain;self.rules=rules;self.version=version;self.timestamp=datetime.utcnow().isoformat()+"Z";self.content_hash=self._compute_hash()
 def _compute_hash(self)->str:content=json.dumps({"domain":self.domain,"rules":self.rules,"version":self.version},sort_keys=True);return hashlib.sha256(content.encode()).hexdigest()
 def to_dict(self)->Dict[str,Any]:return{"domain":self.domain,"rules":self.rules,"version":self.version,"timestamp":self.timestamp,"content_hash":self.content_hash}
class PolicyLedger:
 def __init__(self,ledger_path:str="/Volumes/NSExternal/ether/policy_ledger.jsonl"):self.ledger_path=ledger_path;self.policies={}
 def append_policy(self,policy:PolicyObject)->tuple:
  try:
   entry={"policy_hash":policy.content_hash,"domain":policy.domain,"version":policy.version,"timestamp":policy.timestamp,"rules_count":len(policy.rules)}
   with open(self.ledger_path,'a')as f:f.write(json.dumps(entry)+'\n');f.flush()
   self.policies[policy.content_hash]=policy
   return True,policy.content_hash
  except Exception as e:return False,str(e)
 def get_policy_by_hash(self,policy_hash:str)->PolicyObject:return self.policies.get(policy_hash)
 def get_latest_domain_policy(self,domain:str)->PolicyObject:matching=[p for p in self.policies.values()if p.domain==domain];return matching[-1]if matching else None
