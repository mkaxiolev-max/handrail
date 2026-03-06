#!/usr/bin/env bash
set -euo pipefail

cd ~/axiolev_runtime

echo "=== docker compose ps ==="
docker compose ps

echo
echo "=== handrail ==="
curl -fsS http://127.0.0.1:8011/healthz ; echo

echo
echo "=== ns ==="
curl -fsS http://127.0.0.1:9000/healthz ; echo

echo
echo "=== continuum ==="
curl -fsS http://127.0.0.1:8788/state ; echo
