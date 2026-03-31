import json,hashlib,threading
from datetime import datetime
from pathlib import Path
from typing import Dict,Any,Tuple
class LedgerAtomicity:
 def __init__(self,ledger_path:str="/Volumes/NSExternal/ether/alexandria_ledger.jsonl"):self.ledger_path=Path(ledger_path);self.lock=threading.RLock();self.last_hash=None;self.ledger_path.parent.mkdir(parents=True,exist_ok=True);self._load_last_hash()
 def _load_last_hash(self):
  if not self.ledger_path.exists():self.last_hash=None;return
  try:
   with open(self.ledger_path,'r')as f:
    lines=f.readlines()
    if lines:entry=json.loads(lines[-1].strip());self.last_hash=entry.get('entry_hash')
  except:self.last_hash=None
 def append_atomic(self,rb:Dict[str,Any],cps_id:str,prev_hash:str=None)->Tuple[bool,str]:
  with self.lock:
   try:
    if rb.get('version')!="3":return False,"RB version must be 3"
    if rb.get('decision',{}).get('allowed')is None:return False,"decision.allowed is None"
    if rb.get('execution',{}).get('all_ok')is None:return False,"execution.all_ok is None"
    if rb.get('result',{}).get('output_ok')is None:return False,"result.output_ok is None"
    prev_to_use=prev_hash if prev_hash is not None else self.last_hash
    rb_hash=hashlib.sha256(json.dumps(rb,sort_keys=True,default=str).encode()).hexdigest()
    entry_data={"timestamp":datetime.utcnow().isoformat()+"Z","cps_id":cps_id,"rb_version":rb.get('version'),"rb_hash":rb_hash,"prev_hash":prev_to_use,"rb_status":rb.get('status'),"rb_full":rb}
    entry_json=json.dumps(entry_data,default=str)
    entry_hash=hashlib.sha256(entry_json.encode()).hexdigest()
    entry_data["entry_hash"]=entry_hash
    with open(self.ledger_path,'a')as f:f.write(json.dumps(entry_data,default=str)+'\n');f.flush()
    self.last_hash=entry_hash
    return True,entry_hash
   except Exception as e:return False,str(e)
