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
    try:
        results = []

        for op in req.ops:
            name = op.get("op")
            args = op.get("args", {})

            if name == "proc.run_readonly":
                cmd = args.get("command")

                if cmd == "pwd":
                    results.append(run(["pwd"]))
                elif cmd == "ls":
                    results.append(run(["ls"]))
                else:
                    results.append({"ok": False, "error": f"not allowed: {cmd}"})

            elif name == "pytest.run":
                results.append(run(["pytest", "-q"]))

            elif name == "docker.ps":
                results.append(run(["docker", "ps"]))

            elif name == "logs.tail":
                results.append(run(["docker", "logs", "--tail", "50", "axiolev_runtime-handrail-1"]))

            else:
                results.append({"ok": False, "error": f"unknown op: {name}"})

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
