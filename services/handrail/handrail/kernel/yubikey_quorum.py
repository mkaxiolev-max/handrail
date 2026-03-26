import hashlib,json
from typing import Dict,Any,List
from datetime import datetime
from enum import Enum
class YubiKeySlot(Enum):
 SLOT_1="yubikey_1"
 SLOT_2="yubikey_2"
 SLOT_3="yubikey_3"
class QuorumState:
 def __init__(self):self.armed_slots=[];self.signatures=[]
 def arm_slot(self,slot:YubiKeySlot,signature:str)->bool:
  if slot not in self.armed_slots:self.armed_slots.append(slot);self.signatures.append({"slot":slot.value,"sig":signature,"timestamp":datetime.utcnow().isoformat()+"Z"});return True
  return False
 def check_2of3(self)->tuple:return len(self.armed_slots)>=2,f"{len(self.armed_slots)}/3_SATISFIED"
 def reset(self):self.armed_slots=[];self.signatures=[]
class YubiKeyQuorum:
 def __init__(self):self.state=QuorumState();self.boot_history=[]
 def dispatch_with_quorum(self,intent:Dict[str,Any])->Dict[str,Any]:
  if not self.state.check_2of3()[0]:return{"status":"QUORUM_FAILED","reason":"insufficient_yubikeys","timestamp":datetime.utcnow().isoformat()+"Z"}
  intent_hash=hashlib.sha256(json.dumps(intent,sort_keys=True,default=str).encode()).hexdigest()
  kdr={"intent_hash":intent_hash,"receipt_id":f"kdr_{datetime.utcnow().timestamp()}","allowed":True,"signatures":self.state.signatures,"timestamp":datetime.utcnow().isoformat()+"Z"}
  self.boot_history.append(kdr);self.state.reset()
  return kdr
