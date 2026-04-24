#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 Mike Kenworthy <mike@axiolev.com>
# SPDX-License-Identifier: LicenseRef-AXIOLEV-Proprietary
# AXIOLEV Holdings LLC — NS∞ Stop hook — session pause receipt
# Sole architect: Mike Kenworthy
set -euo pipefail

ALEX="/Volumes/NSExternal/ALEXANDRIA"
TS="$(date -u +%Y%m%dT%H%M%SZ)"
RECEIPT_DIR="$ALEX/receipts"

mkdir -p "$RECEIPT_DIR" 2>/dev/null || exit 0

RUBRIC="$ALEX/score/master_rubric.json"
COMPOSITE="?"; PUBLIC="?"; PHASE="?"
if [ -f "$RUBRIC" ]; then
  COMPOSITE="$(python3 -c "import json; r=json.load(open('$RUBRIC')); print(r.get('composite_220','?'))" 2>/dev/null || echo '?')"
  PUBLIC="$(python3    -c "import json; r=json.load(open('$RUBRIC')); print(r.get('public_score_100','?'))" 2>/dev/null || echo '?')"
  PHASE="$(python3     -c "import json; r=json.load(open('$RUBRIC')); print(r.get('current_phase','?'))" 2>/dev/null || echo '?')"
fi

BRANCH="$(git -C "$HOME/axiolev_runtime" rev-parse --abbrev-ref HEAD 2>/dev/null || echo unknown)"
HEAD="$(git -C "$HOME/axiolev_runtime" rev-parse --short HEAD 2>/dev/null || echo unknown)"

python3 - <<PY >> "$RECEIPT_DIR/session.jsonl" 2>/dev/null || true
import json, hashlib
body = {
    "kind": "session_pause",
    "ts": "$TS",
    "branch": "$BRANCH",
    "head": "$HEAD",
    "composite_220": "$COMPOSITE",
    "public_score_100": "$PUBLIC",
    "current_phase": "$PHASE",
    "resume": "python3 scripts/orchestrate/run_phase.py --phase $PHASE",
}
body["id"] = hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()[:16]
print(json.dumps(body, sort_keys=True))
PY
exit 0
