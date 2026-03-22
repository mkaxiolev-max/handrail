import hashlib,json,os,time
from datetime import datetime
from pathlib import Path
from fastapi import FastAPI,Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List,Dict,Any,Optional

app=FastAPI(title="Handrail Core")
RUNS_DIR=Path("/app/handrail/.run")
WORKSPACE=Path("/app/handrail/workspace")

class CPSRequest(BaseModel):
    cps_id:str
    objective:str
    ops:List[Dict[str,Any]]
    expect:Optional[Dict[str,Any]]={}

def now_id(): return datetime.utcnow().strftime("%Y%m%d_%H%M%S")

@app.get("/healthz")
def health(): return {"status":"online"}

@app.post("/ops/cps")
def ops_cps(req:CPSRequest):
    from handrail.cps_engine import CPSExecutor
    run_id=now_id()
    run_dir=RUNS_DIR/run_id
    run_dir.mkdir(parents=True,exist_ok=True)
    cps_dict=req.dict()
    result=CPSExecutor.execute(cps_dict,WORKSPACE)
    try:
        _blob=json.dumps(cps_dict,sort_keys=True).encode()
        _h=hashlib.sha256(_blob).hexdigest()
        result["identity"]={"input_hash":_h,"timestamp":datetime.utcnow().isoformat()}
        _lp="/app/handrail/ledger_chain.json"
        _ph="0"*64
        if os.path.exists(_lp):
            with open(_lp,"r") as f: _ph=json.load(f).get("last_hash",_ph)
        _ch=hashlib.sha256((_ph+_h).encode()).hexdigest()
        result["ledger"]={"prev_hash":_ph,"hash":_ch}
        with open(_lp,"w") as f: json.dump({"last_hash":_ch,"run_id":run_id},f)
    except Exception as e: result["bk_error"]=str(e)
    result.update({"run_id":run_id,"run_dir":str(run_dir)})
    return JSONResponse(result)
