#!/usr/bin/env bash
set -euo pipefail
cd ~/axiolev_runtime
echo "Rebuilding images..."
docker compose build
echo "Done."
