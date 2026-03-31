import json,hashlib
from pathlib import Path
from typing import Dict,Any,Tuple
class CrashRecovery:
 def __init__(self,ledger_path:str,recovery_log:str="/tmp/alexandria_recovery.log"):
  self.ledger_path=Path(ledger_path)
  self.recovery_log=Path(recovery_log)
 def verify_ledger_integrity(self)->Tuple[bool,str]:
  if not self.ledger_path.exists():return True,"ledger not yet created"
  try:
   with open(self.ledger_path,'r')as f:lines=f.readlines()
   prev_hash=None
   for i,line in enumerate(lines):
    entry=json.loads(line.strip())
    if prev_hash is None:prev_hash=entry.get('entry_hash')
    else:
     expected_prev=prev_hash
     actual_prev=entry.get('prev_hash')
     if expected_prev!=actual_prev:return False,f"chain broken at entry {i}"
     prev_hash=entry.get('entry_hash')
   return True,"ledger integrity verified"
  except Exception as e:return False,f"recovery error: {str(e)}"
 def log_recovery_event(self,event:str)->None:
  with open(self.recovery_log,'a')as f:f.write(f"{event}\n")
