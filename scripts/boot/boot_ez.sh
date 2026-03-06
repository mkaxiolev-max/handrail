#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

echo "=== Boot EZ: snapshot before ==="
./scripts/boot/snapshot.sh

echo
echo "=== Boot EZ: restart ns + continuum only via Handrail ==="
RESP="$(curl -sS -X POST http://127.0.0.1:8011/v1/boot/ez)"
echo "$RESP"

RUN_DIR="$(python3 - <<'PY' "$RESP"
import json, sys
print(json.loads(sys.argv[1])["run_dir"])
PY
)"

echo
echo "=== Waiting for boot result in: $RUN_DIR ==="
for i in $(seq 1 24); do
  [ -f "$RUN_DIR/result.json" ] && break
  [ -f "$RUN_DIR/error.txt" ] && break
  sleep 2
done

echo
echo "=== result.json ==="
cat "$RUN_DIR/result.json" 2>/dev/null || true

echo
echo "=== error.txt ==="
cat "$RUN_DIR/error.txt" 2>/dev/null || true

echo
echo "=== final status ==="
./scripts/boot/status.sh
