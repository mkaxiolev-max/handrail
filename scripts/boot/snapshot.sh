#!/usr/bin/env bash
set -euo pipefail

cd ~/axiolev_runtime

RUN_ID="$(date +%Y%m%d_%H%M%S)"
BASE="/Volumes/NSExternal/.run/boot/$RUN_ID"
mkdir -p "$BASE"

{
  echo "time=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "pwd=$(pwd)"
  echo "git_branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || true)"
  echo "git_commit=$(git rev-parse HEAD 2>/dev/null || true)"
  echo "docker=$(docker --version 2>/dev/null || true)"
  echo "compose=$(docker compose version 2>/dev/null || true)"
} > "$BASE/meta.txt"

docker compose ps > "$BASE/compose_ps.txt"
docker compose config > "$BASE/compose_config.txt"
curl -fsS http://127.0.0.1:8011/healthz > "$BASE/handrail_healthz.json"
curl -fsS http://127.0.0.1:9000/healthz > "$BASE/ns_healthz.json"
curl -fsS http://127.0.0.1:8788/state > "$BASE/continuum_state.json"
docker compose logs --tail=120 > "$BASE/logs_tail.txt"

printf '%s\n' "$BASE" | tee /Volumes/NSExternal/.run/boot/latest_manual_snapshot
echo "SNAPSHOT_OK=$BASE"
