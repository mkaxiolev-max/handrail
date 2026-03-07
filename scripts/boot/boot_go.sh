#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

ROOT="$(pwd)"
RUNS_ROOT="/Volumes/NSExternal/.run/boot"
mkdir -p "$RUNS_ROOT"

RUN_ID="$(date -u +%Y%m%d_%H%M%S)"
TASK_ID="ops_boot_check_${RUN_ID}"
RUN_DIR="$RUNS_ROOT/$RUN_ID"
mkdir -p "$RUN_DIR"

export ROOT RUN_ID TASK_ID RUN_DIR RUNS_ROOT

POLICY_HASH="$(
  cat docker-compose.yml \
      services/handrail/handrail/server.py \
      runtime/boot/boot_orchestrator.py \
      scripts/boot/boot_ez.sh \
      scripts/boot/reset_clean.sh \
      scripts/boot/status.sh 2>/dev/null | shasum -a 256 | awk '{print $1}'
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
        "present_state_run_dir": os.environ.get("PRESENT_STATE_RUN"),
    },
)
PY

echo
echo "BOOT_GO_RUN_DIR=$RUN_DIR"
echo "CHILD_RUN_DIR=${CHILD_RUN_DIR:-none}"
echo "PRESENT_STATE_RUN=$PRESENT_STATE_RUN"
