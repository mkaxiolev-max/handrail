import json
from pathlib import Path
import subprocess

def replay_run(run_dir: str, dry_run: bool = True):
    run_dir = Path(run_dir)

    ledger = run_dir / "proof_ledger.jsonl"
    summary = run_dir / "run_summary.json"

    if not ledger.exists():
        raise RuntimeError("missing ledger")

    events = [
        json.loads(line)
        for line in ledger.read_text().splitlines()
        if line.strip()
    ]

    replay_results = []

    for e in events:
        if e["event_type"] != "task_completed":
            continue

        data = e.get("data", {})
        cmd = data.get("command")

        if not cmd:
            continue

        if dry_run:
            replay_results.append({
                "command": cmd,
                "replayed": False,
                "mode": "dry-run"
            })
            continue

        proc = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True
        )

        replay_results.append({
            "command": cmd,
            "rc": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "replayed": True
        })

    return {
        "run_dir": str(run_dir),
        "events": len(events),
        "replay_results": replay_results,
    }
