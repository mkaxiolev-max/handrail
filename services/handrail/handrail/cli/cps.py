"""
Handrail CLI — CPS operations
"""

from __future__ import annotations

import json
from pathlib import Path

import httpx

# ---------------------------------------------------------------------------
# Paths — override via env vars if needed
# ---------------------------------------------------------------------------

def _handrail_root() -> Path:
    import os
    root = os.environ.get("HANDRAIL_ROOT")
    if root:
        return Path(root)
    # Walk up from this file looking for services/handrail
    here = Path(__file__).resolve()
    for parent in here.parents:
        candidate = parent / "services" / "handrail" / "handrail"
        if candidate.exists():
            return candidate
    # Fallback: assume we're inside services/handrail/handrail/cli/
    return here.parent.parent


def _cps_dir() -> Path:
    import os
    d = os.environ.get("HANDRAIL_CPS_DIR")
    if d:
        return Path(d)
    return _handrail_root() / "cps"


def _policy_dir() -> Path:
    import os
    d = os.environ.get("HANDRAIL_POLICY_DIR")
    if d:
        return Path(d)
    return _handrail_root() / "policy"


def _run_base_dir() -> Path:
    import os
    d = os.environ.get("HANDRAIL_RUN_DIR")
    if d:
        return Path(d)
    # Try NSExternal first, fall back to /tmp
    ns = Path("/Volumes/NSExternal/.run/boot")
    if ns.parent.parent.exists():
        return ns
    return Path("/tmp/handrail_runs")


# ---------------------------------------------------------------------------
# CPS operations
# ---------------------------------------------------------------------------

def list_cps() -> list[str]:
    cps_dir = _cps_dir()
    if not cps_dir.exists():
        return []
    return sorted(p.stem for p in cps_dir.glob("*"))


def cat_cps(cps_id: str) -> dict:
    cps_dir = _cps_dir()
    path = cps_dir / cps_id
    if not path.exists():
        raise FileNotFoundError(f"CPS not found: {cps_id} (looked in {cps_dir})")
    return json.loads(path.read_text())


def run_cps(cps_id: str, api_base: str = "http://127.0.0.1:8011") -> dict:
    plan = cat_cps(cps_id)
    try:
        resp = httpx.post(f"{api_base}/ops/cps", json=plan, timeout=60)
        resp.raise_for_status()
        return resp.json()
    except httpx.ConnectError:
        raise RuntimeError(f"Cannot reach Handrail API at {api_base} — is it running?")


# ---------------------------------------------------------------------------
# Run dir operations
# ---------------------------------------------------------------------------

def _find_run_dir(run_id: str) -> Path:
    base = _run_base_dir()
    # Direct path
    direct = base / run_id
    if direct.exists():
        return direct
    # Search recursively (run dirs may be nested by date)
    matches = list(base.rglob(run_id))
    if matches:
        return matches[0]
    raise FileNotFoundError(f"Run not found: {run_id} (searched under {base})")


def inspect_run(run_id: str) -> dict:
    run_dir = _find_run_dir(run_id)
    result_path = run_dir / "cps_result.json"
    request_path = run_dir / "cps_request.json"
    if not result_path.exists():
        raise FileNotFoundError(f"cps_result.json not found in {run_dir}")
    result = json.loads(result_path.read_text())
    request = json.loads(request_path.read_text()) if request_path.exists() else {}
    return {
        "run_id": run_id,
        "run_dir": str(run_dir),
        "cps_id": result.get("cps_id") or request.get("cps_id"),
        "objective": request.get("objective"),
        "policy_profile": result.get("policy_profile") or request.get("policy_profile"),
        "ok": result.get("ok"),
        "decision_codes": [r.get("decision_code") for r in result.get("results", [])],
        "result_digest": result.get("result_digest"),
        "expect_result": result.get("expect_result"),
        "metrics": result.get("metrics"),
    }


def replay_run(run_id: str, api_base: str = "http://127.0.0.1:8011") -> dict:
    run_dir = _find_run_dir(run_id)
    request_path = run_dir / "cps_request.json"
    if not request_path.exists():
        raise FileNotFoundError(f"cps_request.json not found in {run_dir}")
    original_result_path = run_dir / "cps_result.json"
    original_digest = None
    if original_result_path.exists():
        original = json.loads(original_result_path.read_text())
        original_digest = original.get("result_digest")

    # Re-execute
    plan = json.loads(request_path.read_text())
    try:
        resp = httpx.post(f"{api_base}/ops/cps", json=plan, timeout=60)
        resp.raise_for_status()
        new_result = resp.json()
    except httpx.ConnectError:
        raise RuntimeError(f"Cannot reach Handrail API at {api_base}")

    new_digest = new_result.get("result_digest")
    match = original_digest == new_digest

    return {
        "run_id": run_id,
        "match": match,
        "original_digest": original_digest,
        "replay_digest": new_digest,
        "replay_ok": new_result.get("ok"),
        "verdict": "MATCH" if match else "MISMATCH",
    }


def logs_run(run_id: str, full: bool = False) -> None:
    run_dir = _find_run_dir(run_id)
    ledger = run_dir / "proof_ledger.jsonl"
    if ledger.exists():
        print(f"=== proof_ledger.jsonl ({run_dir.name}) ===")
        print(ledger.read_text())
    if full:
        result_path = run_dir / "cps_result.json"
        if result_path.exists():
            print(f"\n=== cps_result.json ===")
            print(result_path.read_text())
    else:
        result_path = run_dir / "cps_result.json"
        if result_path.exists():
            result = json.loads(result_path.read_text())
            print(f"=== Run {run_id} ===")
            print(f"ok:             {result.get('ok')}")
            print(f"result_digest:  {result.get('result_digest', '')[:20]}...")
            print(f"metrics:        {result.get('metrics')}")
            print(f"expect_passed:  {result.get('expect_result', {}).get('passed')}")


# ---------------------------------------------------------------------------
# Policy listing
# ---------------------------------------------------------------------------

def list_policies() -> list[str]:
    policy_dir = _policy_dir()
    names = set()
    # External files
    if policy_dir.exists():
        for p in policy_dir.glob("*.json"):
            names.add(p.stem)
    # Builtin
    from handrail.cps_engine import BUILTIN_POLICIES
    names.update(BUILTIN_POLICIES.keys())
    return sorted(names)
