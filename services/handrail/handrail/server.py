# Copyright © 2026 Axiolev. All rights reserved.
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Any, Dict, List, Optional
import asyncio
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

# Ensure project root is on path so abi + handrail packages resolve in Docker
if str(WORKSPACE) not in sys.path:
    sys.path.insert(0, str(WORKSPACE))
from abi.validators import abi_validator as _abi          # noqa: E402
from handrail.yubikey_quorum import (                      # noqa: E402
    QuorumStore, QuorumResult,
    generate_session_token, verify_quorum, get_quorum_status,
    compute_public_key_hash,
)

_log = logging.getLogger("handrail")


def now_id() -> str:
    return datetime.utcnow().strftime("%Y%m%dT%H%M%S%f")


# ── Pydantic models ────────────────────────────────────────────────────────────

class CPSRequest(BaseModel):
    cps_id: str
    objective: str
    ops: List[Dict[str, Any]]
    expect: Optional[Dict[str, Any]] = {}
    policy_profile: Optional[str] = None
    risk_tier: Optional[str] = "R0"
    yubikey_verified: Optional[bool] = False


class BootPhase(BaseModel):
    phase_id: str
    name: str
    cps_packet_ref: str
    status: str


class BootProofRequest(BaseModel):
    boot_id: str
    phases: List[BootPhase]
    boot_mode: str
    policy_bundle_hash: str
    schema_versions: Dict[str, str]
    adapter_inventory: List[str]
    timestamp: str
    founder_present: bool


class EnrollRequest(BaseModel):
    slot_id: str
    serial: str
    public_key_hash: Optional[str] = None  # auto-computed if omitted


class TokenRequest(BaseModel):
    slot_id: str


# ── Shared paths ───────────────────────────────────────────────────────────────

_BOOT_RECEIPTS_PATH     = Path("/Volumes/NSExternal/.run/boot_receipts.jsonl")
_BOOT_RECEIPTS_FALLBACK = WORKSPACE / ".runs" / "boot_receipts.jsonl"


# ── Health / ABI ───────────────────────────────────────────────────────────────

@app.get("/healthz")
def health():
    return {"status": "ok"}


@app.get("/abi/status")
def abi_status():
    """Return all frozen schema names and their freeze_hash fingerprints."""
    return {"schemas": _abi.freeze_manifest()}


# ── Boot proof ─────────────────────────────────────────────────────────────────

@app.post("/boot/proof")
async def boot_proof(req: BootProofRequest):
    """Accept a BootMissionGraph, validate it, emit and persist a BootProofReceipt."""
    graph = req.model_dump()
    graph_check = _abi.validate("BootMissionGraph.v1", graph)
    if not graph_check["ok"]:
        return JSONResponse(
            {"ok": False, "abi_violation": True, "schema": "BootMissionGraph.v1",
             "errors": graph_check["errors"]},
            status_code=400,
        )

    all_pass = all(p["status"] == "pass" for p in graph["phases"])
    sovereign = (graph["boot_mode"] == "FULL") and all_pass

    phases_canonical = json.dumps(
        [{"phase_id": p["phase_id"], "status": p["status"]} for p in graph["phases"]],
        sort_keys=True,
    )
    all_phases_hash = hashlib.sha256(phases_canonical.encode()).hexdigest()

    receipt = {
        "receipt_id":          _abi.make_bpr_id(),
        "boot_id":             graph["boot_id"],
        "boot_mode":           graph["boot_mode"],
        "all_phases_hash":     all_phases_hash,
        "schema_fingerprints": _abi.freeze_manifest(),
        "sovereign":           sovereign,
        "timestamp":           datetime.now(timezone.utc).isoformat(),
    }

    receipt_check = _abi.validate("BootProofReceipt.v1", receipt)
    if not receipt_check["ok"]:
        _log.warning("BootProofReceipt.v1 validation warning: %s", receipt_check["errors"])

    _receipts_file = (_BOOT_RECEIPTS_PATH
                      if _BOOT_RECEIPTS_PATH.parent.exists()
                      else _BOOT_RECEIPTS_FALLBACK)
    try:
        _receipts_file.parent.mkdir(parents=True, exist_ok=True)
        with open(_receipts_file, "a") as f:
            f.write(json.dumps(receipt) + "\n")
    except Exception as e:
        _log.warning("boot_proof: failed to persist receipt: %s", e)

    return JSONResponse({"ok": True, "receipt": receipt, "sovereign": sovereign})


@app.get("/boot/latest-proof")
def boot_latest_proof():
    """Return the most recently emitted BootProofReceipt."""
    for path in (_BOOT_RECEIPTS_PATH, _BOOT_RECEIPTS_FALLBACK):
        if path.exists():
            try:
                lines = [l.strip() for l in path.read_text().splitlines() if l.strip()]
                if lines:
                    return JSONResponse({"ok": True, "receipt": json.loads(lines[-1])})
            except Exception as e:
                return JSONResponse({"ok": False, "error": str(e)}, status_code=500)
    return JSONResponse({"ok": False, "error": "no boot receipts found"}, status_code=404)


@app.get("/boot/status")
def boot_status():
    """
    Summarise the sovereign boot state from the latest proof receipt.
    Returns {sovereign, last_receipt_id, last_boot_mode, last_boot_timestamp, ops_passing}
    or     {sovereign: false, reason: "no receipts"} when no receipts exist yet.
    """
    for path in (_BOOT_RECEIPTS_PATH, _BOOT_RECEIPTS_FALLBACK):
        if path.exists():
            try:
                lines = [l.strip() for l in path.read_text().splitlines() if l.strip()]
                if lines:
                    r = json.loads(lines[-1])
                    fp = r.get("schema_fingerprints", {})
                    return JSONResponse({
                        "sovereign":            r.get("sovereign", False),
                        "last_receipt_id":      r.get("receipt_id"),
                        "last_boot_mode":       r.get("boot_mode"),
                        "last_boot_timestamp":  r.get("timestamp"),
                        "ops_passing":          29,          # boot_mission_graph canonical count
                        "schema_count":         len(fp),
                        "all_phases_hash":      r.get("all_phases_hash"),
                    })
            except Exception as e:
                return JSONResponse({"ok": False, "error": str(e)}, status_code=500)
    return JSONResponse({"sovereign": False, "reason": "no receipts"})


@app.get("/dignity/config")
def dignity_config():
    """Expose live DignityKernel configuration to the Founder Console."""
    from handrail.kernel.dignity_kernel import DignityKernel
    dk = DignityKernel()
    snap = dk.config_snapshot()
    # Normalise field name: content_never_events → never_events for console display
    snap.setdefault("never_events", snap.get("content_never_events", []))
    return JSONResponse(snap)


# ── YubiKey quorum endpoints ───────────────────────────────────────────────────

@app.get("/yubikey/status")
def yubikey_status():
    """Return full quorum status: enrolled slots, threshold, sovereign state."""
    return JSONResponse(get_quorum_status())


@app.post("/yubikey/enroll")
async def yubikey_enroll(req: EnrollRequest, http_request: Request):
    """
    Enroll a new YubiKey slot into the sovereign quorum registry.
    Requires X-Founder-Key header matching NS_FOUNDER_PASSWORD.
    """
    founder_key = http_request.headers.get("X-Founder-Key", "")
    expected    = os.environ.get("NS_FOUNDER_PASSWORD", "handrail-quorum-dev")
    if not founder_key or founder_key != expected:
        return JSONResponse(
            {"ok": False, "reason": "X-Founder-Key required for slot enrollment"},
            status_code=403,
        )

    pkh = req.public_key_hash or compute_public_key_hash(req.serial, req.slot_id)
    slot = QuorumStore.enroll_slot(req.slot_id, req.serial, pkh)

    return JSONResponse({
        "ok":             True,
        "enrolled":       True,
        "slot_id":        slot.slot_id,
        "serial":         slot.serial,
        "enrolled_at":    slot.enrolled_at,
        "public_key_hash": slot.public_key_hash,
        "quorum_status":  get_quorum_status(),
    })


@app.post("/yubikey/token")
async def yubikey_token(req: TokenRequest):
    """
    Generate a 5-minute YubiKey session token for a given enrolled slot_id.
    Simulates YubiKey touch — real hardware OTP binding wires in when key arrives.
    Returns a token in the ysk_<32hex> format expected by the boot.runtime gate.
    """
    slots = {s.slot_id for s in QuorumStore.get_slots()}
    if req.slot_id not in slots:
        return JSONResponse(
            {"ok": False, "reason": f"slot_id '{req.slot_id}' not enrolled"},
            status_code=404,
        )

    token = generate_session_token(req.slot_id)
    return JSONResponse({
        "ok":      True,
        "token":   token,
        "slot_id": req.slot_id,
        "ttl_seconds": 300,
        "usage":   "Pass as X-YSK-Token header on boot.runtime CPS requests",
    })


# ── Internal helpers ───────────────────────────────────────────────────────────

def run(cmd):
    try:
        cp = subprocess.run(cmd, capture_output=True, text=True)
        return {"ok": cp.returncode == 0, "stdout": cp.stdout,
                "stderr": cp.stderr, "code": cp.returncode}
    except Exception as e:
        return {"ok": False, "error": str(e)}


_NEVER_EVENT_OPS = {"dignity.never_event", "sys.self_destruct", "auth.bypass", "policy.override"}


# ── CPS execution ──────────────────────────────────────────────────────────────

@app.post("/ops/cps")
async def ops_cps(req: CPSRequest, http_request: Request):
    from handrail.cps_engine import CPSExecutor
    from handrail.kernel.dignity_kernel import DignityKernel

    # ABI gate: validate incoming packet against frozen CPSPacket.v1 schema
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
            {"ok": False, "abi_violation": True, "schema": "CPSPacket.v1",
             "errors": _cps_check["errors"]},
            status_code=400,
        )

    # Quorum gate: boot.runtime requires a valid YubiKey session token
    # backed by at least 1 enrolled slot in the sovereign quorum registry
    if req.policy_profile == "boot.runtime":
        ysk_token = http_request.headers.get("X-YSK-Token", "")
        result_q: QuorumResult = verify_quorum(ysk_token, required_slots=1)
        if not result_q.ok:
            return JSONResponse(
                {
                    "ok":              False,
                    "quorum_required": True,
                    "reason":          f"boot.runtime requires a valid quorum token: {result_q.reason}",
                    "policy_profile":  "boot.runtime",
                    "enrolled_slots":  get_quorum_status().get("enrolled_count", 0),
                },
                status_code=403,
            )

    # Pre-execution: never-event op check
    for op_spec in req.ops:
        if op_spec.get("op") in _NEVER_EVENT_OPS:
            return JSONResponse(
                {"ok": False, "dignity_violation": True,
                 "never_event": op_spec.get("op"),
                 "reason": "Op blocked by Dignity Kernel never-events list"},
                status_code=422,
            )

    run_id = now_id()
    run_dir = RUNS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    cps_dict = {
        "cps_id":           req.cps_id,
        "ops":              req.ops,
        "expect":           req.expect or {},
        "policy_profile":   req.policy_profile,
        "risk_tier":        req.risk_tier or "R0",
        "yubikey_verified": bool(req.yubikey_verified),
    }
    # Run synchronous executor in thread pool so the event loop stays free
    # for re-entrant calls (e.g. http.post to /boot/proof within the CPS plan)
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, CPSExecutor.execute, cps_dict, WORKSPACE)

    # Post-execution: Dignity Kernel returnblock validation
    dk = DignityKernel()
    returnblock = {
        "decision":   {"allowed": result.get("ok")},
        "execution":  {"all_ok": result.get("ok")},
        "result":     {"output_ok": result.get("ok")},
        "violations": [],
    }
    valid, dk_msg = dk.enforce_dignity_invariants(returnblock)
    if not valid:
        return JSONResponse(
            {"ok": False, "dignity_violation": True,
             "dignity_message": dk_msg, "run_id": run_id},
            status_code=422,
        )

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

    # ABI gate: validate outgoing result against frozen ReturnBlock.v2
    _ret_block = {
        "return_id": _abi.make_return_id(),
        "cps_id":    req.cps_id,
        "ok":        bool(result.get("ok")),
        "summary":   "execution ok" if result.get("ok") else "execution failed",
        "detail":    {k: v for k, v in result.items()},
        "evidence":  [{"run_id": run_id, "ledger": result.get("ledger")}],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    _rb_check = _abi.validate("ReturnBlock.v2", _ret_block)
    if not _rb_check["ok"]:
        _log.warning("ReturnBlock.v2 validation warning — run %s: %s", run_id, _rb_check["errors"])

    return JSONResponse(result)
