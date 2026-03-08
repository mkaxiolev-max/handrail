#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

ROOT="$(pwd)"
RUNS_ROOT="/Volumes/NSExternal/.run/boot"
mkdir -p "$RUNS_ROOT"

RUN_ID="$(python3 - <<'PY2'
from datetime import datetime, timezone
print(datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f"))
PY2
)"
TASK_ID="ops_boot_check_${RUN_ID}"
RUN_DIR="$RUNS_ROOT/$RUN_ID"
mkdir -p "$RUN_DIR"

export ROOT RUN_ID TASK_ID RUN_DIR RUNS_ROOT

POLICY_HASH="$(python3 - <<'PYHASH'
from pathlib import Path
import hashlib

paths = [
    Path("docker-compose.yml"),
    Path("services/handrail/handrail/server.py"),
    Path("runtime/boot/boot_orchestrator.py"),
    Path("scripts/boot/boot_ez.sh"),
    Path("scripts/boot/reset_clean.sh"),
    Path("scripts/boot/status.sh"),
]

h = hashlib.sha256()
for path in paths:
    if path.exists():
        h.update(path.read_bytes())
print(h.hexdigest())
PYHASH
)"
export POLICY_HASH

python3 - <<'PY'
import os
from runtime.audit.proof_ledger import append_event

append_event(
    os.environ["RUN_DIR"],
    "boot_go_started",
    {
        "run_id": os.environ["RUN_ID"],
        "task_id": os.environ["TASK_ID"],
        "policy_hash": os.environ["POLICY_HASH"],
        "root": os.environ["ROOT"],
    },
)
PY

cat > "$RUN_DIR/intent.json" <<EOF
{
  "run_id": "$RUN_ID",
  "task_id": "$TASK_ID",
  "task_type": "ops_boot_check",
  "objective": "governed boot entrypoint using Handrail and present-state artifacts",
  "policy_hash": "$POLICY_HASH"
}
EOF

cat > "$RUN_DIR/policy_snapshot.json" <<EOF
{
  "policy_hash": "$POLICY_HASH",
  "hard_rules": [
    "preserve audit trail",
    "prefer Handrail for execution",
    "post-check health endpoints",
    "write run artifacts deterministically"
  ],
  "allowed_action_bands": [
    "read",
    "inspect",
    "health-check",
    "bounded write"
  ]
}
EOF

HANDRAIL_UP="0"
if curl -fsS http://127.0.0.1:8011/healthz > "$RUN_DIR/handrail_healthz_pre.json" 2>/dev/null; then
  HANDRAIL_UP="1"
fi

if [ "$HANDRAIL_UP" = "1" ]; then
  python3 - <<'PY'
import os
from runtime.audit.proof_ledger import append_event

append_event(
    os.environ["RUN_DIR"],
    "handoff_to_handrail",
    {
        "mode": "direct_handrail",
        "endpoint": "http://127.0.0.1:8011",
    },
)
PY

  curl -fsS http://127.0.0.1:8011/v1/status > "$RUN_DIR/pre_status.json"

  BOOT_RESP="$(curl -fsS -X POST http://127.0.0.1:8011/v1/boot/ez)"
  printf '%s\n' "$BOOT_RESP" > "$RUN_DIR/boot_accept.json"

  CHILD_RUN_DIR="$(
    python3 - <<'PY' "$BOOT_RESP"
import json, sys
print(json.loads(sys.argv[1])["run_dir"])
PY
  )"
  export CHILD_RUN_DIR
  printf '%s\n' "$CHILD_RUN_DIR" > "$RUN_DIR/child_run_dir.txt"

  for _ in $(seq 1 40); do
    [ -f "$CHILD_RUN_DIR/result.json" ] && break
    [ -f "$CHILD_RUN_DIR/error.txt" ] && break
    sleep 2
  done

  curl -fsS --get \
    --data-urlencode "run_dir=$CHILD_RUN_DIR" \
    http://127.0.0.1:8011/v1/runs/get > "$RUN_DIR/child_run_artifacts.json"

  curl -fsS http://127.0.0.1:8011/v1/status > "$RUN_DIR/post_status.json"
else
  python3 - <<'PY'
import os
from runtime.audit.proof_ledger import append_event

append_event(
    os.environ["RUN_DIR"],
    "handoff_to_handrail",
    {
        "mode": "bootstrap_fallback",
        "reason": "handrail_unreachable",
    },
)
PY

  ./scripts/boot/reset_clean.sh | tee "$RUN_DIR/reset_clean_output.txt"
  curl -fsS http://127.0.0.1:8011/v1/status > "$RUN_DIR/post_status.json"
fi

python3 -m runtime.boot.boot_orchestrator | tee "$RUN_DIR/present_state_boot_stdout.json"

PRESENT_STATE_RUN="$(
  cat /Volumes/NSExternal/.run/boot/latest_present_state_boot
)"
export PRESENT_STATE_RUN
printf '%s\n' "$PRESENT_STATE_RUN" > "$RUN_DIR/present_state_run_dir.txt"

python3 - <<'PY'
import json
import os
from pathlib import Path
from runtime.audit.proof_ledger import append_event
from runtime.state.memory_fabric import write_snapshot
from runtime.audit.run_summary import write_run_summary

run_dir = Path(os.environ["RUN_DIR"])
snapshot = {
    "run_id": os.environ["RUN_ID"],
    "task_id": os.environ["TASK_ID"],
    "policy_hash": os.environ["POLICY_HASH"],
    "child_run_dir": Path(run_dir / "child_run_dir.txt").read_text().strip() if (run_dir / "child_run_dir.txt").exists() else None,
    "present_state_run_dir": os.environ.get("PRESENT_STATE_RUN"),
    "artifacts": sorted([p.name for p in run_dir.iterdir() if p.is_file()]),
}
write_snapshot(run_dir, snapshot)
append_event(
    run_dir,
    "memory_fabric_snapshot_written",
    snapshot,
)
append_event(
    run_dir,
    "boot_go_finished",
    {
        "run_id": os.environ["RUN_ID"],
        "task_id": os.environ["TASK_ID"],
        "policy_hash": os.environ["POLICY_HASH"],
        "present_state_run_dir": os.environ.get("PRESENT_STATE_RUN"),
    },
    service="ns",
    layer="router",
    status="ok",
    message="Governed boot finished",
)

post_ok = False
services = {}
mounts = {}
checks = {}

if isinstance(post_status, dict):
    health = post_status.get("health", {})
    mounts_blob = post_status.get("mounts", {})
    services = {
        "handrail": "ok" if health.get("handrail") else "fail",
        "ns": "ok" if health.get("ns") else "fail",
        "continuum": "ok" if health.get("continuum") else "fail",
    }
    mounts = {
        "handrail": bool(mounts_blob.get("handrail_sees_NSExternal")),
        "ns": bool((mounts_blob.get("ns_healthz") or {}).get("storage", {}).get("external_ssd")),
        "continuum": True,
    }
    post_ok = all(v == "ok" for v in services.values())

checks = {
    "external_ssd": mounts.get("ns", False),
    "artifact_completeness": evaluators.get("artifact_completeness_verifier", {}).get("pass", False),
}

write_run_summary(
    run_dir,
    {
        "run_id": os.environ["RUN_ID"],
        "task_id": os.environ["TASK_ID"],
        "started_ts_ms": int((run_dir / "proof_ledger.jsonl").stat().st_mtime * 1000) if (run_dir / "proof_ledger.jsonl").exists() else None,
        "duration_ms": None,
        "ok": bool(post_ok),
        "intent": "governed boot entrypoint using Handrail and present-state artifacts",
        "task_type": "ops_boot_check",
        "policy_hash": os.environ["POLICY_HASH"],
        "services": services,
        "mounts": mounts,
        "checks": checks,
        "failure_reason": None if post_ok else "post_checks_failed",
        "artifact_refs": sorted([str(p) for p in run_dir.iterdir() if p.is_file()]),
        "event_count": sum(1 for _ in (run_dir / "proof_ledger.jsonl").open()) if (run_dir / "proof_ledger.jsonl").exists() else 0,
        "contradictions": [],
    },
)
PY

echo
echo "BOOT_GO_RUN_DIR=$RUN_DIR"
echo "CHILD_RUN_DIR=${CHILD_RUN_DIR:-none}"
echo "PRESENT_STATE_RUN=$PRESENT_STATE_RUN"
