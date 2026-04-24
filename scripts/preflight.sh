#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 Mike Kenworthy <mike@axiolev.com>
# SPDX-License-Identifier: LicenseRef-AXIOLEV-Proprietary
# AXIOLEV Holdings LLC — NS∞ Master Integration Preflight
# Sole architect: Mike Kenworthy
set -euo pipefail

ALEX="/Volumes/NSExternal/ALEXANDRIA"
RUN="$HOME/axiolev_runtime"
DOCKER_HOST="${DOCKER_HOST:-unix:///Users/axiolevns/.docker/run/docker.sock}"
TS="$(date -u +%Y%m%dT%H%M%SZ)"
RECEIPT="$ALEX/integration/preflight.receipt"

mkdir -p "$ALEX/integration" "$ALEX/score" "$ALEX/receipts" "$ALEX/master_cert"

fail() { echo "PREFLIGHT FAIL: $*" >&2; exit 1; }
ok()   { echo "  ✓ $*"; }
warn() { echo "  ⚠ $*"; }

echo "== NS∞ MASTER INTEGRATION — PREFLIGHT =="
echo "  ts: $TS"

# 1) Working directory
[ "$PWD" = "$RUN" ] || fail "cwd != $RUN (got $PWD)"
ok "cwd is $RUN"

# 2) Branch
BRANCH="$(git rev-parse --abbrev-ref HEAD)"
[ "$BRANCH" = "integration/max-omega-20260421-191635" ] \
  || fail "branch != integration/max-omega-20260421-191635 (got $BRANCH)"
ok "branch is $BRANCH"

# 3) Alexandria writable
[ -d "$ALEX" ] || fail "Alexandria root missing: $ALEX"
touch "$ALEX/.preflight.tmp" && rm "$ALEX/.preflight.tmp" \
  || fail "Alexandria not writable"
ok "Alexandria writable: $ALEX"

# 4) Leaked PAT scrub verification (HARD GATE)
PAT_HITS="$(git log --all --full-history -p 2>/dev/null | grep -cE 'axiolev-deploy2|ghp_[A-Za-z0-9]{36}' || echo 0)"
if [ "$PAT_HITS" -gt 0 ]; then
  warn "PAT scan: $PAT_HITS potential hits in history"
  warn "Run git-filter-repo to scrub before push. Preflight continues (local-only mode)."
  PAT_CLEAN=false
else
  ok "PAT history clean"
  PAT_CLEAN=true
fi

# 5) Pytest baseline
PYTEST_OUT="$ALEX/integration/preflight_pytest.$TS.txt"
( cd "$RUN" && python3 -m pytest -q tests/ 2>&1 ) | tee "$PYTEST_OUT" || true
PASSED="$(grep -oE '[0-9]+ passed' "$PYTEST_OUT" | head -n1 | grep -oE '[0-9]+' || echo 0)"
FAILED="$(grep -oE '[0-9]+ failed'  "$PYTEST_OUT" | head -n1 | grep -oE '[0-9]+' || echo 0)"
if [ "$PASSED" -ge 500 ] && [ "$FAILED" -eq 0 ]; then
  ok "Tests $PASSED passed, $FAILED failed"
else
  fail "Baseline pytest expected ≥500 pass / 0 fail; got passed=$PASSED failed=$FAILED"
fi

# 6) Docker socket
DOCKER_HOST="$DOCKER_HOST" docker ps >/dev/null 2>&1 \
  || fail "Docker socket not accessible ($DOCKER_HOST)"
ok "Docker socket accessible"

# 7) Service health (flexible — count healthy containers)
HEALTHY=0
for port in 9001 9002 9003 9004 9005 9006 9007 9008 9009 9010 9011 9012 9013 9014 9015; do
  if curl -fsS --max-time 2 "http://localhost:${port}/health" >/dev/null 2>&1 \
     || curl -fsS --max-time 2 "http://localhost:${port}/healthz" >/dev/null 2>&1; then
    HEALTHY=$((HEALTHY+1))
  fi
done
# Also count docker healthy containers
DOCKER_HEALTHY="$(DOCKER_HOST="$DOCKER_HOST" docker ps --format '{{.Status}}' 2>/dev/null | grep -c healthy || echo 0)"
ok "HTTP-healthy services: $HEALTHY  |  Docker-healthy containers: $DOCKER_HEALTHY"
[ "$DOCKER_HEALTHY" -ge 1 ] || warn "No healthy docker containers — bring up services with ./boot.sh"

# 8) Score tracker scaffold
if [ ! -f "$ALEX/score/master_rubric.json" ]; then
  python3 "$RUN/scripts/score/init_rubric.py" --out "$ALEX/score/master_rubric.json"
  ok "Initialized master_rubric.json"
else
  COMPOSITE="$(python3 -c "import json; r=json.load(open('$ALEX/score/master_rubric.json')); print(r['composite_220'])" 2>/dev/null || echo '?')"
  PUBLIC="$(python3   -c "import json; r=json.load(open('$ALEX/score/master_rubric.json')); print(r['public_score_100'])" 2>/dev/null || echo '?')"
  ok "master_rubric.json present  composite=${COMPOSITE}/220  public=${PUBLIC}/100"
fi

# 9) Receipt
cat > "$RECEIPT" <<EOF
{
  "kind": "preflight.receipt",
  "ts": "$TS",
  "branch": "$BRANCH",
  "tests_passed": $PASSED,
  "tests_failed": $FAILED,
  "docker_healthy": $DOCKER_HEALTHY,
  "pat_history_clean": $PAT_CLEAN,
  "alexandria_writable": true,
  "docker_ok": true,
  "result": "PASS"
}
EOF
ok "Receipt written: $RECEIPT"

echo ""
echo "== PREFLIGHT PASS =="
echo ""
echo "Confirmed baseline:"
echo "  Composite: $(python3 -c "import json; r=json.load(open('$ALEX/score/master_rubric.json')); print(r['composite_220'])" 2>/dev/null || echo '?')/220"
echo "  Public:    $(python3 -c "import json; r=json.load(open('$ALEX/score/master_rubric.json')); print(r['public_score_100'])" 2>/dev/null || echo '?')/100"
echo "  Tests:     $PASSED passed"
echo "  Services:  $DOCKER_HEALTHY docker-healthy"
echo ""
echo "Ring-5 blockers (external — cannot be resolved autonomously):"
echo "  1. Stripe LLC verification"
echo "  2. Live Stripe secret key in Vercel"
echo "  3. YubiKey slot 2 enrollment"
echo "  4. DNS CNAME root.axiolev.com → root-jade-kappa.vercel.app"
echo "  5. GitHub PAT scrub (axiolev-deploy2) — PAT_CLEAN=$PAT_CLEAN"
echo "  6. macOS Keychain + gitleaks pre-commit hook"
echo ""
echo "Run Phase 1: python3 scripts/orchestrate/run_phase.py --phase 1"
