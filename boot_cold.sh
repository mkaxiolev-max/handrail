#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

docker compose down --remove-orphans
docker compose up -d --build --force-recreate --remove-orphans

curl -sS -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8011/healthz
curl -sS -o /dev/null -w "%{http_code}\n" http://127.0.0.1:9000/healthz

# wait for continuum health (or /state if you prefer)
for i in {1..60}; do
  status=$(docker inspect -f "{{.State.Health.Status}}" axiolev_runtime-continuum-1 2>/dev/null || echo "unknown")
  [ "$status" = "healthy" ] && break
  sleep 1
done

curl -sS -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8788/state

RUN_ID="run_$(date +%Y%m%d_%H%M%S)"
mkdir -p ".run/boot/$RUN_ID"
docker compose ps > ".run/boot/$RUN_ID/ps.txt"
docker compose logs --no-color > ".run/boot/$RUN_ID/logs.txt"
cp docker-compose.yml ".run/boot/$RUN_ID/docker-compose.yml"
[ -f .env ] && cp .env ".run/boot/$RUN_ID/.env"
echo "$RUN_ID"
