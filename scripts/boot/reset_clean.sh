#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

echo "=== RESET CLEAN: snapshot before ==="
./scripts/boot/snapshot.sh || true

echo
echo "=== docker compose down ==="
docker compose down --remove-orphans

echo
echo "=== docker compose up ==="
docker compose up -d --build

echo
echo "=== waiting for services ==="
for i in $(seq 1 30); do
  H="$(curl -sS -o /dev/null -w "%{http_code}" http://127.0.0.1:8011/healthz || true)"
  N="$(curl -sS -o /dev/null -w "%{http_code}" http://127.0.0.1:9000/healthz || true)"
  C="$(curl -sS -o /dev/null -w "%{http_code}" http://127.0.0.1:8788/state || true)"
  echo "try $i: handrail=$H ns=$N continuum=$C"
  if [ "$H" = "200" ] && [ "$N" = "200" ] && [ "$C" = "200" ]; then
    break
  fi
  sleep 2
done

echo
echo "=== final status ==="
./scripts/boot/status.sh

echo
echo "=== snapshot after ==="
./scripts/boot/snapshot.sh || true
