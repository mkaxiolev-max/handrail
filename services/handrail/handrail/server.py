from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Any, Dict, List, Optional
import subprocess
import hashlib
import json
import os
from pathlib import Path
from datetime import datetime

app = FastAPI(title="Handrail Core")

RUNS_DIR = Path(os.environ.get("HR_WORKSPACE", "/app")) / ".runs"
WORKSPACE = Path(os.environ.get("HR_WORKSPACE", "/app"))


def now_id() -> str:
    return datetime.utcnow().strftime("%Y%m%dT%H%M%S%f")


class CPSRequest(BaseModel):
    cps_id: str
    objective: str
    ops: List[Dict[str, Any]]
    expect: Optional[Dict[str, Any]] = {}
    policy_profile: Optional[str] = None


@app.get("/healthz")
def health():
    return {"status": "ok"}


def run(cmd):
    try:
        cp = subprocess.run(cmd, capture_output=True, text=True)
        return {
            "ok": cp.returncode == 0,
            "stdout": cp.stdout,
            "stderr": cp.stderr,
            "code": cp.returncode
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.post("/ops/cps")
def ops_cps(req: CPSRequest):
    from handrail.cps_engine import CPSExecutor
    run_id = now_id()
    run_dir = RUNS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    cps_dict = {"cps_id": req.cps_id, "ops": req.ops, "expect": req.expect or {}, "policy_profile": req.policy_profile}
    result = CPSExecutor.execute(cps_dict, WORKSPACE)
    try:
        _h = hashlib.sha256(json.dumps(cps_dict, sort_keys=True).encode()).hexdigest()
        result["identity"] = {"input_hash": _h, "timestamp": datetime.utcnow().isoformat()}
        _lp = str(RUNS_DIR / "ledger_chain.json")
        _ph = "0" * 64
        if os.path.exists(_lp):
            try:
                with open(_lp, "r") as f:
                    _ph = json.load(f).get("last_hash", _ph)
            except Exception:
                pass
        _ch = hashlib.sha256((_ph + _h).encode()).hexdigest()
        result["ledger"] = {"prev_hash": _ph, "hash": _ch}
        with open(_lp, "w") as f:
            json.dump({"last_hash": _ch, "run_id": run_id}, f)
    except Exception as e:
        result["bk_error"] = str(e)
    result.update({"run_id": run_id, "run_dir": str(run_dir)})
    return JSONResponse(result)
