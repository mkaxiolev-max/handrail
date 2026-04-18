#!/usr/bin/env bash
# NS∞ Shutdown Prep — run before closing the Mac
# Verifies state, writes shutdown record, leaves containers running.
# Conservative and fully reversible.
set -euo pipefail

REPO=~/axiolev_runtime
cd "$REPO"
mkdir -p "$REPO/artifacts"

STAMP=$(date -u +%Y%m%dT%H%M%SZ)
MD="$REPO/artifacts/final_shutdown_prep_${STAMP}.md"

# ── Verify first ─────────────────────────────────────────────────────────────
echo "[SHUTDOWN PREP] Running verification..."
bash "$REPO/scripts/boot/ns_verify_and_save.command"
VERIFY_EXIT=$?

if [ $VERIFY_EXIT -ne 0 ]; then
    echo "[ABORT] Shutdown prep halted — verification failed."
    exit 1
fi

# ── What is still running ─────────────────────────────────────────────────────
export DOCKER_HOST="unix://$HOME/.docker/run/docker.sock"
RUNNING=$(docker ps --format "  - {{.Names}} ({{.Status}})" 2>/dev/null || echo "  (docker not reachable)")
STATE_API_PID=$(pgrep -f "state_api.py" 2>/dev/null | head -1 || echo "")

BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
SHA=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
ALEX=$([ -d /Volumes/NSExternal ] && echo "MOUNTED" || echo "NOT MOUNTED")

# ── Write shutdown record ─────────────────────────────────────────────────────
cat > "$MD" <<EOF
# NS∞ Shutdown Prep — $STAMP

## What was verified
- ns_core :9000 — PASS
- state_api :9090 — PASS
- handrail :8011 — PASS
- continuum :8788 — PASS
- git branch: $BRANCH @ $SHA
- Alexandria: $ALEX

## What is still running (intentionally left up)
Docker containers:
$RUNNING

state_api PID: ${STATE_API_PID:-not found}

## What was NOT touched
- No Docker volumes pruned
- No Alexandria data modified
- No containers force-stopped
- No git history altered

## Safe next action
You may shut down the Mac.
On next boot: double-click **NS∞ Launch** on the Desktop or run:
  bash ~/axiolev_runtime/scripts/boot/ns_boot_founder.command

## Digest
Containers left running survive Mac shutdown gracefully.
Docker Desktop restarts them automatically if configured to do so,
or ns_boot_founder.command will bring them up on next login.

AXIOLEV HOLDINGS LLC — DIGNITY PRESERVED
EOF

echo ""
echo "Shutdown record: $MD"
echo ""
echo "Safe to shut down Mac."
