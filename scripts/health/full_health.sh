#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 Mike Kenworthy <mike@axiolev.com>
# SPDX-License-Identifier: LicenseRef-AXIOLEV-Proprietary
# AXIOLEV Holdings LLC — NS∞ full health check (ports 9001-9023)
# Sole architect: Mike Kenworthy
set -euo pipefail

DOCKER_HOST="${DOCKER_HOST:-unix:///Users/axiolevns/.docker/run/docker.sock}"
HEALTHY=0; TOTAL=0; FAILS=""

for port in $(seq 9001 9023); do
  TOTAL=$((TOTAL+1))
  STATUS="$(curl -fsS --max-time 2 "http://localhost:${port}/health" 2>/dev/null \
    || curl -fsS --max-time 2 "http://localhost:${port}/healthz" 2>/dev/null \
    || echo '{"status":"unreachable"}')"
  if echo "$STATUS" | python3 -c "import sys,json; d=json.load(sys.stdin); sys.exit(0 if d.get('status','') in ('OK','ok','healthy','up') else 1)" 2>/dev/null; then
    printf "  ✓ :%d\n" "$port"
    HEALTHY=$((HEALTHY+1))
  else
    printf "  ✗ :%d  %s\n" "$port" "$(echo "$STATUS" | head -c 80)"
    FAILS="$FAILS $port"
  fi
done

echo ""
DOCKER_HEALTHY="$(DOCKER_HOST="$DOCKER_HOST" docker ps --format '{{.Status}}' 2>/dev/null | grep -c healthy || echo 0)"
echo "HTTP healthy: $HEALTHY/$TOTAL  |  Docker healthy: $DOCKER_HEALTHY"
[ -n "$FAILS" ] && echo "Unreachable: $FAILS"
[ "$HEALTHY" -ge 14 ] && echo "STATUS: OK (≥14 healthy)" || echo "STATUS: DEGRADED"
