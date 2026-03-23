#!/usr/bin/env python3
"""Handrail CLI v2 - run, inspect, replay, list"""
import json, sys, subprocess
from pathlib import Path

HANDRAIL_PORT = "8011"
RUNS_DIR = Path("/Volumes/NSExternal/.run/boot")
CPS_DIR = Path(__file__).parent / "cps"

def load_cps(cps_id: str) -> dict:
    cps_path = CPS_DIR / cps_id
    if not cps_path.exists():
        print(f"ERROR: CPS not found: {cps_id}"); sys.exit(1)
    return json.loads(cps_path.read_text())

def execute_cps(cps_dict: dict) -> dict:
    import urllib.request
    url = f"http://127.0.0.1:{HANDRAIL_PORT}/ops/cps"
    data = json.dumps(cps_dict).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.loads(response.read())

def run_cps(cps_id: str) -> None:
    print(f"[handrail] Running {cps_id}...", file=sys.stderr)
    cps = load_cps(cps_id)
    result = execute_cps(cps)
    print(json.dumps(result, indent=2))
    status = "✅ OK" if result.get("ok") else "❌ FAILED"
    print(f"\n[handrail] {status} | run_id: {result.get('run_id')}", file=sys.stderr)

def inspect_run(run_id: str) -> None:
    run_dir = RUNS_DIR / run_id
    if not run_dir.exists():
        print(f"ERROR: Run not found: {run_id}"); sys.exit(1)
    result = json.loads((run_dir / "cps_result.json").read_text())
    print(f"\n{'='*60}\nINSPECT: {run_id}\n{'='*60}")
    print(f"CPS_ID: {result.get('cps_id')}\nSTATUS: {'✅ OK' if result.get('ok') else '❌ FAILED'}")
    print(f"OPS: {result.get('metrics', {}).get('op_count')}\nDURATION: {result.get('metrics', {}).get('duration_ms')}ms")
    print(f"IDENTITY: {result.get('identity', {}).get('input_hash', 'N/A')[:32]}...")
    print(f"LEDGER: {result.get('ledger', {}).get('hash', 'N/A')[:32]}...")
    print(f"\nOPERATIONS ({len(result.get('results', []))}):")
    for op in result.get('results', []):
        status = "✅" if op.get('ok') else "❌"
        print(f"  {status} {op.get('op')} ({op.get('latency_ms')}ms) - {op.get('decision_code')}")
    print(f"\n{'='*60}\n")

def replay_run(run_id: str) -> None:
    run_dir = RUNS_DIR / run_id
    if not run_dir.exists():
        print(f"ERROR: Run not found: {run_id}"); sys.exit(1)
    cps = json.loads((run_dir / "cps_request.json").read_text())
    print(f"[handrail] Replaying {run_id} ({cps.get('cps_id')})...", file=sys.stderr)
    result = execute_cps(cps)
    print(json.dumps(result, indent=2))
    original = json.loads((run_dir / "cps_result.json").read_text())
    match = "✅ DETERMINISTIC" if original.get('result_digest') == result.get('result_digest') else "⚠️  DIVERGED"
    print(f"\n[handrail] {match}", file=sys.stderr)

def list_cps() -> None:
    print(f"\n{'='*60}\nAVAILABLE CPS\n{'='*60}\n")
    for cps_id in sorted([f.name for f in CPS_DIR.iterdir() if f.is_file()]):
        try:
            cps = json.loads((CPS_DIR / cps_id).read_text())
            print(f"  {cps_id:30} | {len(cps.get('ops', []))} ops")
        except:
            print(f"  {cps_id:30} | (invalid)")
    print(f"\n{'='*60}\n")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("USAGE: handrail [run|inspect|replay|list] [cps_id|run_id]", file=sys.stderr); sys.exit(1)
    cmd = sys.argv[1]
    if cmd == "run" and len(sys.argv) > 2:
        run_cps(sys.argv[2])
    elif cmd == "inspect" and len(sys.argv) > 2:
        inspect_run(sys.argv[2])
    elif cmd == "replay" and len(sys.argv) > 2:
        replay_run(sys.argv[2])
    elif cmd == "list":
        list_cps()
    else:
        print(f"ERROR: Unknown command {cmd}", file=sys.stderr); sys.exit(1)
