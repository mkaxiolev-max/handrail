#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

echo "PWD=$(pwd)"
echo "Compose file:"
ls -la docker-compose.yml

echo
echo "Bringing up ALL services with remove-orphans + force-recreate"
docker compose up -d --force-recreate --remove-orphans

echo
echo "docker compose ps:"
docker compose ps

echo
echo "Mount check inside handrail:"
docker compose exec -T handrail sh -lc 'echo "container=$(hostname)"; test -d /Volumes/NSExternal && echo YES || echo NO; ls -la /Volumes | head -n 20'

echo
echo "Mount check inside ns:"
docker compose exec -T ns sh -lc 'echo "container=$(hostname)"; test -d /Volumes/NSExternal && echo YES || echo NO; ls -la /Volumes | head -n 20'

echo
echo "Mount check inside continuum:"
docker compose exec -T continuum sh -lc 'echo "container=$(hostname)"; test -d /Volumes/NSExternal && echo YES || echo NO; ls -la /Volumes | head -n 20'

echo
echo "Health checks:"
curl -fsS -m 2 http://127.0.0.1:8011/healthz >/dev/null && echo "Handrail OK" || echo "Handrail DOWN"
curl -fsS -m 2 http://127.0.0.1:9000/healthz >/dev/null && echo "NS OK" || echo "NS DOWN"
curl -fsS -m 2 http://127.0.0.1:8788/state  >/dev/null && echo "Continuum OK" || echo "Continuum DOWN"

echo
echo "NS healthz snippet:"
curl -sS http://127.0.0.1:9000/healthz | head -c 420
echo
