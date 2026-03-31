import json,hashlib
from datetime import datetime,timezone
from pathlib import Path
from typing import Dict,Any,Optional
class SnapshotManager:
 def __init__(self,ledger_path:str,snapshots_dir:str="/tmp/alexandria_snapshots"):
  self.ledger_path=Path(ledger_path)
  self.snapshots_dir=Path(snapshots_dir)
  self.snapshots_dir.mkdir(parents=True,exist_ok=True)
 def snapshot(self,tag:str)->Dict[str,Any]:
  if not self.ledger_path.exists():return {"status":"FAILED","reason":"ledger not found"}
  entries=[]
  with open(self.ledger_path,'r')as f:entries=[json.loads(line.strip())for line in f.readlines()]
  snapshot_data={"tag":tag,"timestamp":datetime.now(timezone.utc).isoformat(),"entry_count":len(entries),"entries":entries}
  snapshot_hash=hashlib.sha256(json.dumps(snapshot_data,sort_keys=True,default=str).encode()).hexdigest()
  snapshot_data["snapshot_hash"]=snapshot_hash
  snapshot_file=self.snapshots_dir/f"snapshot_{tag}_{snapshot_hash[:8]}.json"
  with open(snapshot_file,'w')as f:json.dump(snapshot_data,f)
  return {"status":"SUCCESS","tag":tag,"snapshot_hash":snapshot_hash,"entry_count":len(entries),"file":str(snapshot_file)}
 def restore(self,snapshot_hash:str)->Optional[list]:
  snapshots=[f for f in self.snapshots_dir.glob("*.json")if snapshot_hash in f.name]
  if not snapshots:return None
  with open(snapshots[0],'r')as f:data=json.load(f)
  return data.get("entries",[])
