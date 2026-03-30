#!/usr/bin/env bash
set -euo pipefail

echo "[preflight] docker daemon"
docker info >/dev/null

echo "[preflight] external mount"
test -d /Volumes/NSExternal || { echo "MISSING: /Volumes/NSExternal (mount the drive)"; exit 1; }

echo "[preflight] ok"
