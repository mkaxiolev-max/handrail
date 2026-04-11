#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$ROOT_DIR"

STAMP="$(date +%Y%m%d_%H%M%S)"
RUN_DIR="/Volumes/NSExternal/.run/boot/${STAMP}"

mkdir -p "$RUN_DIR"

docker compose config > "$RUN_DIR/compose_config.txt"
docker compose ps > "$RUN_DIR/compose_ps.txt"
docker compose logs --tail=200 > "$RUN_DIR/logs_tail.txt" 2>&1 || true

curl -sS http://127.0.0.1:8011/healthz > "$RUN_DIR/handrail_healthz.json"
curl -sS http://localhost:9000/healthz > "$RUN_DIR/ns_healthz.json"
curl -sS http://localhost:8788/state > "$RUN_DIR/continuum_state.json"

cat > "$RUN_DIR/meta.txt" <<EOF
snapshot_ts=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
root_dir=$ROOT_DIR
run_dir=$RUN_DIR
EOF

printf '%s\n' "$RUN_DIR"
printf 'SNAPSHOT_OK=%s\n' "$RUN_DIR"
