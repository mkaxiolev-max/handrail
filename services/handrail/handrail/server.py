from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Any, Dict, List, Optional
import subprocess

app = FastAPI(title="Handrail Core")


class CPSRequest(BaseModel):
    cps_id: str
    objective: str
    ops: List[Dict[str, Any]]
    expect: Optional[Dict[str, Any]] = {}


@app.get("/healthz")
def health():
    return {"status": "ok"}


@app.post("/ops/cps")
def ops_cps(req: CPSRequest):
    try:
        results = []

        for op in req.ops:
            if op.get("op") == "proc.run_readonly":
                cmd = op.get("args", {}).get("command")

                if cmd == "pwd":
                    cp = subprocess.run(["pwd"], capture_output=True, text=True)
                    results.append({
                        "ok": cp.returncode == 0,
                        "stdout": cp.stdout,
                        "stderr": cp.stderr
                    })
                else:
                    results.append({
                        "ok": False,
                        "error": f"not allowed: {cmd}"
                    })
            else:
                results.append({
                    "ok": False,
                    "error": f"unknown op: {op.get('op')}"
                })

        return JSONResponse({
            "ok": True,
            "cps_id": req.cps_id,
            "results": results
        })

    except Exception as e:
        return JSONResponse({
            "ok": False,
            "error": str(e),
            "class": "server_exception"
        })
