#!/usr/bin/env python3
"""
Patch server.py to:
1. Use updated CPSExecutor result shape (results array, expect_result, metrics)
2. Write artifact_manifest.json alongside cps_request.json and cps_result.json
3. Add httpx import if missing

Run from repo root:
  python3 scripts/patch_server_phase1.py
"""

import sys
from pathlib import Path

SERVER_PATH = Path("services/handrail/handrail/server.py")

MANIFEST_HELPER = '''

def _write_artifact_manifest(run_dir):
    """Write artifact_manifest.json for a CPS run directory."""
    import hashlib, time
    files = []
    for fname in ["cps_request.json", "cps_result.json"]:
        fpath = run_dir / fname
        if fpath.exists():
            h = hashlib.sha256(fpath.read_bytes()).hexdigest()
            files.append({
                "path": fname,
                "type": fname.replace(".json", "").replace("cps_", ""),
                "checksum": f"sha256:{h}",
                "created_ts_ms": int(time.time() * 1000),
            })
    manifest = {"files": files}
    (run_dir / "artifact_manifest.json").write_text(json.dumps(manifest, indent=2))

'''

OLD_OPS_CPS = '''@app.post("/ops/cps")
def ops_cps(req: CPSRequest):
    """Execute CPS (Cognitive Program Sequence) transaction"""
    from handrail.cps_engine import CPSExecutor
    
    run_id = now_id()
    run_dir = RUNS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    
    cps_dict = {
        "cps_id": req.cps_id,
        "objective": req.objective,
        "ops": req.ops,
        "expect": req.expect or {}
    }
    
    (run_dir / "cps_request.json").write_text(json.dumps(cps_dict, indent=2))
    
    result = CPSExecutor.execute(cps_dict, WORKSPACE)
    result["run_id"] = run_id
    result["run_dir"] = str(run_dir)
    
    (run_dir / "cps_result.json").write_text(json.dumps(result, indent=2))
    (RUNS_DIR / "latest").write_text(str(run_dir))
    
    return JSONResponse(result)'''

NEW_OPS_CPS = '''@app.post("/ops/cps")
def ops_cps(req: CPSRequest):
    """Execute CPS (Cognitive Program Sequence) transaction"""
    from handrail.cps_engine import CPSExecutor

    run_id = now_id()
    run_dir = RUNS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    cps_dict = {
        "cps_id": req.cps_id,
        "objective": req.objective,
        "ops": req.ops,
        "expect": req.expect or {},
        "policy_profile": req.policy_profile,
    }

    (run_dir / "cps_request.json").write_text(json.dumps(cps_dict, indent=2))

    result = CPSExecutor.execute(cps_dict, WORKSPACE)
    result["run_id"] = run_id
    result["run_dir"] = str(run_dir)

    (run_dir / "cps_result.json").write_text(json.dumps(result, indent=2))
    _write_artifact_manifest(run_dir)
    (RUNS_DIR / "latest").write_text(str(run_dir))

    return JSONResponse(result)'''

OLD_CPS_REQUEST = '''class CPSRequest(BaseModel):
    cps_id: str
    objective: str | None = None
    ops: list[dict[str, Any]]
    expect: dict[str, Any] | None = None'''

NEW_CPS_REQUEST = '''class CPSRequest(BaseModel):
    cps_id: str
    objective: str | None = None
    ops: list[dict[str, Any]]
    expect: dict[str, Any] | None = None
    policy_profile: str | None = None'''


def patch():
    if not SERVER_PATH.exists():
        print(f"ERROR: {SERVER_PATH} not found. Run from repo root.")
        sys.exit(1)

    src = SERVER_PATH.read_text()
    changed = False

    # 1. Add policy_profile to CPSRequest
    if "policy_profile" not in src:
        if OLD_CPS_REQUEST in src:
            src = src.replace(OLD_CPS_REQUEST, NEW_CPS_REQUEST)
            print("✅ Added policy_profile to CPSRequest")
            changed = True
        else:
            print("⚠️  CPSRequest model not found in expected form — check manually")

    # 2. Add manifest helper before /ops/cps endpoint
    if "_write_artifact_manifest" not in src:
        anchor = '@app.post("/ops/cps")'
        if anchor in src:
            src = src.replace(anchor, MANIFEST_HELPER + anchor)
            print("✅ Added _write_artifact_manifest helper")
            changed = True
        else:
            print("⚠️  /ops/cps anchor not found — add manifest helper manually")

    # 3. Update ops_cps body to write manifest + pass policy_profile
    if "_write_artifact_manifest(run_dir)" not in src:
        if OLD_OPS_CPS in src:
            src = src.replace(OLD_OPS_CPS, NEW_OPS_CPS)
            print("✅ Updated ops_cps to write artifact_manifest and pass policy_profile")
            changed = True
        else:
            print("⚠️  ops_cps body not in expected form — apply NEW_OPS_CPS manually")

    if changed:
        SERVER_PATH.write_text(src)
        print(f"\n✅ server.py patched. Run: git diff services/handrail/handrail/server.py")
    else:
        print("No changes needed — already up to date.")


if __name__ == "__main__":
    patch()
