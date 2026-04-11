#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

echo "=== handrail openapi ==="
curl -sS http://127.0.0.1:8011/openapi.json | python3 -c '
import sys, json
j=json.load(sys.stdin)
for p in j.get("paths", {}):
    print(p)
'

echo
echo "=== handrail /v1/status ==="
curl -sS http://127.0.0.1:8011/v1/status
echo

echo
echo "=== handrail /v1/run smoke ==="
RESP="$(curl -sS -X POST http://127.0.0.1:8011/v1/run \
  -H "Content-Type: application/json" \
  -d '{
    "cmd":["bash","-lc","curl -sS http://127.0.0.1:8011/healthz && echo && curl -sS http://localhost:9000/healthz && echo && curl -sS http://localhost:8788/state"],
    "cwd":"/Users/axiolevns/axiolev_runtime",
    "timeout_s":30
  }')"

echo "$RESP"

LATEST="$(curl -sS http://127.0.0.1:8011/v1/runs/latest | python3 -c 'import sys,json; print(json.load(sys.stdin)["latest_run_dir"])')"

echo
echo "=== latest run dir ==="
echo "$LATEST"

echo
echo "=== result.json ==="
cat "$LATEST/result.json"

echo
echo "=== stdout.txt ==="
cat "$LATEST/stdout.txt"
