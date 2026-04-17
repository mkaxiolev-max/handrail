#!/usr/bin/env bash
# axiolev_push.sh — signed commit + tag + push origin (no force)
# AXIOLEV HOLDINGS LLC — DIGNITY PRESERVED
set -u
REPO="${REPO:-$(cd "$(dirname "$0")/.." && pwd)}"
cd "$REPO"

MSG="${1:-chore: routine push}"
TAG="${2:-}"

git add -A
git commit -m "$MSG

AXIOLEV HOLDINGS LLC — DIGNITY PRESERVED" || echo "nothing to commit"

if [ -n "$TAG" ]; then
    git tag -a "$TAG" -m "$TAG $(date -u +%Y%m%dT%H%M%SZ)" && echo "tagged: $TAG"
fi

git push origin "$(git rev-parse --abbrev-ref HEAD)" && echo "pushed"
