#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."

./scripts/boot/preflight_mac.sh

docker compose down --remove-orphans
docker compose up -d --build --force-recreate --remove-orphans

echo "NS:"
curl -fsS -m 2 -o /dev/null -w "%{http_code}\n" http://127.0.0.1:9000/healthz

echo "Continuum:"
ok=0
for i in {1..20}; do
  code=$(curl -sS -m 1 -o /dev/null -w "%{http_code}" http://127.0.0.1:8788/state || true)
  echo "try $i: $code"
  if [ "$code" = "200" ]; then ok=1; break; fi
  sleep 1
done
if [ "$ok" -ne 1 ]; then
  echo "Continuum did not reach 200. Showing logs."
  docker compose logs --tail=200 continuum
  exit 1
fi

echo "Handrail:"
curl -fsS -m 2 -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8011/healthz

RUN_ID="boot_$(date +%Y%m%d_%H%M%S)"
OUT=".run/boot/$RUN_ID"
mkdir -p "$OUT"
docker compose config > "$OUT/compose.rendered.yml"
docker compose ps > "$OUT/ps.txt"
docker compose logs --no-color > "$OUT/compose.logs.txt"
echo "Saved: $OUT"
