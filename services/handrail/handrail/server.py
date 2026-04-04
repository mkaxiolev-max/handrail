# Copyright © 2026 Axiolev. All rights reserved.
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Any, Dict, List, Optional
import re
import subprocess
import hashlib
import json
import logging
import os
import sys
from pathlib import Path
from datetime import datetime, timezone

app = FastAPI(title="Handrail Core")

RUNS_DIR = Path(os.environ.get("HR_WORKSPACE", "/app")) / ".runs"
WORKSPACE = Path(os.environ.get("HR_WORKSPACE", "/app"))

# Ensure project root is on path so abi package resolves in Docker (WORKDIR=/app, project root at HR_WORKSPACE)
if str(WORKSPACE) not in sys.path:
    sys.path.insert(0, str(WORKSPACE))
from abi.validators import abi_validator as _abi  # noqa: E402

_log = logging.getLogger("handrail")


def now_id() -> str:
    return datetime.utcnow().strftime("%Y%m%dT%H%M%S%f")


class CPSRequest(BaseModel):
    cps_id: str
    objective: str
    ops: List[Dict[str, Any]]
    expect: Optional[Dict[str, Any]] = {}
    policy_profile: Optional[str] = None
    risk_tier: Optional[str] = "R0"          # R0-R4; R3/R4 require yubikey_verified
    yubikey_verified: Optional[bool] = False  # set true after /kernel/yubikey/verify


@app.get("/healthz")
def health():
    return {"status": "ok"}


@app.get("/abi/status")
def abi_status():
    """Return all frozen schema names and their freeze_hash fingerprints."""
    return {"schemas": _abi.freeze_manifest()}


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


_NEVER_EVENT_OPS = {"dignity.never_event", "sys.self_destruct", "auth.bypass", "policy.override"}
_YSK_TOKEN_RE = re.compile(r'^ysk_[0-9a-f]{32}$')

def _validate_ysk_token(token: str) -> bool:
    return bool(token and _YSK_TOKEN_RE.match(token))

@app.post("/ops/cps")
async def ops_cps(req: CPSRequest, http_request: Request):
    from handrail.cps_engine import CPSExecutor
    from handrail.kernel.dignity_kernel import DignityKernel

    # ABI gate: validate incoming packet against frozen CPSPacket.v1 schema.
    # Synthesize envelope fields (intent_id, timestamp) not carried in CPSRequest;
    # enforce content fields (objective, ops shape, risk_tier enum).
    _cps_packet = {
        "cps_id":    _abi.make_cps_id(),
        "intent_id": _abi.make_intent_id(),
        "objective": req.objective,
        "ops":       req.ops,
        "risk_tier": req.risk_tier or "R0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if req.policy_profile:
        _cps_packet["policy_profile"] = req.policy_profile
    _cps_check = _abi.validate("CPSPacket.v1", _cps_packet)
    if not _cps_check["ok"]:
        return JSONResponse(
            {
                "ok": False,
                "abi_violation": True,
                "schema": "CPSPacket.v1",
                "errors": _cps_check["errors"],
            },
            status_code=400,
        )

    # Quorum gate: boot.runtime requires a valid YubiKey session token
    if req.policy_profile == "boot.runtime":
        ysk_token = http_request.headers.get("X-YSK-Token", "")
        if not _validate_ysk_token(ysk_token):
            return JSONResponse({
                "ok": False,
                "quorum_required": True,
                "reason": "boot.runtime ops require a valid X-YSK-Token YubiKey session",
                "policy_profile": "boot.runtime",
            }, status_code=403)

    # Pre-execution: never-event op check
    for op_spec in req.ops:
        if op_spec.get("op") in _NEVER_EVENT_OPS:
            return JSONResponse({
                "ok": False,
                "dignity_violation": True,
                "never_event": op_spec.get("op"),
                "reason": "Op blocked by Dignity Kernel never-events list",
            }, status_code=422)

    run_id = now_id()
    run_dir = RUNS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    cps_dict = {"cps_id": req.cps_id, "ops": req.ops, "expect": req.expect or {},
                "policy_profile": req.policy_profile,
                "risk_tier": req.risk_tier or "R0",
                "yubikey_verified": bool(req.yubikey_verified)}
    result = CPSExecutor.execute(cps_dict, WORKSPACE)

    # Post-execution: Dignity Kernel returnblock validation
    dk = DignityKernel()
    returnblock = {
        "decision":  {"allowed": result.get("ok")},
        "execution": {"all_ok": result.get("ok")},
        "result":    {"output_ok": result.get("ok")},
        "violations": [],
    }
    valid, dk_msg = dk.enforce_dignity_invariants(returnblock)
    if not valid:
        return JSONResponse({
            "ok": False,
            "dignity_violation": True,
            "dignity_message": dk_msg,
            "run_id": run_id,
        }, status_code=422)

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
    result.update({"run_id": run_id, "run_dir": str(run_dir), "dignity_enforced": True})

    # ABI gate: validate outgoing result against frozen ReturnBlock.v2 schema.
    # Warn on mismatch but never suppress the response.
    _ret_block = {
        "return_id":  _abi.make_return_id(),
        "cps_id":     req.cps_id,
        "ok":         bool(result.get("ok")),
        "summary":    "execution ok" if result.get("ok") else "execution failed",
        "detail":     {k: v for k, v in result.items()},
        "evidence":   [{"run_id": run_id, "ledger": result.get("ledger")}],
        "timestamp":  datetime.now(timezone.utc).isoformat(),
    }
    _rb_check = _abi.validate("ReturnBlock.v2", _ret_block)
    if not _rb_check["ok"]:
        _log.warning("ReturnBlock.v2 validation warning — run %s: %s", run_id, _rb_check["errors"])

    return JSONResponse(result)
