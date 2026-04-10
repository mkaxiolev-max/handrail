#!/usr/bin/env bash
# ============================================================
# AXIOLEV Holdings LLC — NS∞ System
# Copyright © 2024–2026 AXIOLEV Holdings LLC. All rights reserved.
# Jurisdiction: Wyoming, USA
#
# This file is proprietary and confidential.
# Unauthorized use, reproduction, or distribution is prohibited.
#
# AI assistance does not transfer, assign, or convey any ownership
# interest in this work. All AI-assisted development (Anthropic Claude,
# OpenAI GPT, Google Gemini, xAI Grok) was performed under work-made-for-hire
# doctrine and under the exclusive direction of Mike Kenworthy, founder.
#
# File: axiolev_push.sh
# Purpose: Production push script — pre-flight, optional commit, annotated milestone tags, push
# Ring: Ring 5 — Production
# ============================================================

set -euo pipefail

# ── Banner ──────────────────────────────────────────────────
echo ""
echo "  ╔══════════════════════════════════════════════════════╗"
echo "  ║          AXIOLEV Holdings LLC — NS∞ System           ║"
echo "  ║         Production Push · axiolev_push.sh            ║"
echo "  ║   Copyright © 2024–2026 AXIOLEV Holdings LLC        ║"
echo "  ║              Wyoming, USA · All rights reserved      ║"
echo "  ╚══════════════════════════════════════════════════════╝"
echo ""

# ── Defaults ────────────────────────────────────────────────
STAGE=0
AMEND=0
COMMIT_MSG=""
TAG_LABEL=""
DRY_RUN=0

# ── Arg parsing ─────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case "$1" in
    --stage)    STAGE=1; shift ;;
    --message)  COMMIT_MSG="$2"; shift 2 ;;
    --amend)    AMEND=1; shift ;;
    --tag)      TAG_LABEL="$2"; shift 2 ;;
    --dry-run)  DRY_RUN=1; shift ;;
    -h|--help)
      echo "Usage: axiolev_push.sh [OPTIONS]"
      echo ""
      echo "Options:"
      echo "  --stage              Stage all tracked changes before committing"
      echo "  --message MSG        Commit message (triggers commit if provided)"
      echo "  --amend              Amend last commit instead of creating new"
      echo "  --tag LABEL          Create annotated milestone tag (e.g. final, ring4-complete)"
      echo "  --dry-run            Print what would happen without executing"
      echo ""
      echo "Examples:"
      echo "  axiolev_push.sh --message 'feat(omega): certify all 7 paths'"
      echo "  axiolev_push.sh --tag final"
      echo "  axiolev_push.sh --stage --message 'chore(docs): IP dignity artifacts' --tag final"
      exit 0
      ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

# ── Helper ──────────────────────────────────────────────────
run() {
  if [[ $DRY_RUN -eq 1 ]]; then
    echo "[DRY-RUN] $*"
  else
    "$@"
  fi
}

# ── Pre-flight ──────────────────────────────────────────────
echo "── Pre-flight ──────────────────────────────────────────"

BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo "  Branch:  $BRANCH"

if [[ "$BRANCH" == "main" || "$BRANCH" == "master" ]]; then
  echo ""
  echo "  ⚠  WARNING: You are pushing directly to $BRANCH."
  echo "     This affects the canonical production branch."
  echo ""
  read -r -p "  Type 'yes' to confirm push to $BRANCH: " CONFIRM
  if [[ "$CONFIRM" != "yes" ]]; then
    echo "  Aborted."
    exit 1
  fi
fi

STATUS=$(git status --porcelain)
if [[ -n "$STATUS" ]]; then
  echo "  Uncommitted changes detected:"
  git status --short
  echo ""
fi

AHEAD=$(git rev-list --count "origin/$BRANCH..HEAD" 2>/dev/null || echo "0")
echo "  Commits ahead of origin/$BRANCH: $AHEAD"

COMMIT_COUNT=$(git rev-list --count HEAD)
echo "  Total commits: $COMMIT_COUNT"
echo ""

# ── Optional stage ──────────────────────────────────────────
if [[ $STAGE -eq 1 ]]; then
  echo "── Staging ─────────────────────────────────────────────"
  run git add -u
  echo "  Staged all tracked changes."
  echo ""
fi

# ── Optional commit ─────────────────────────────────────────
if [[ -n "$COMMIT_MSG" ]]; then
  echo "── Commit ──────────────────────────────────────────────"
  FULL_MSG="${COMMIT_MSG}

IP: AXIOLEV Holdings LLC © 2024–2026 · Wyoming, USA · All rights reserved
Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"

  if [[ $AMEND -eq 1 ]]; then
    run git commit --amend -m "$FULL_MSG"
    echo "  Amended last commit."
  else
    run git commit -m "$FULL_MSG"
    echo "  Created commit."
  fi
  echo ""
fi

# ── Push branch ─────────────────────────────────────────────
echo "── Push branch ─────────────────────────────────────────"
run git push origin "$BRANCH"
echo "  Pushed $BRANCH to origin."
echo ""

# ── Optional annotated tag ──────────────────────────────────
if [[ -n "$TAG_LABEL" ]]; then
  echo "── Annotated tag ───────────────────────────────────────"

  TODAY=$(date -u +%Y%m%d)
  TAG_NAME="axiolev-ns-infinity-${TAG_LABEL}-${TODAY}"
  SHORT_SHA=$(git rev-parse --short HEAD)

  TAG_MSG="$(cat <<EOF
${TAG_NAME}

AXIOLEV Holdings LLC — NS∞ System
Milestone: ${TAG_LABEL}
Date: $(date -u +%Y-%m-%d) (UTC)
Branch: ${BRANCH}
Commit: ${SHORT_SHA}

Copyright © 2024–2026 AXIOLEV Holdings LLC. All rights reserved.
Jurisdiction: Wyoming, USA

This software is proprietary and confidential.
Unauthorized use, reproduction, or distribution is prohibited.

AI assistance does not transfer, assign, or convey any ownership
interest in this work. All AI-assisted development (Anthropic Claude,
OpenAI GPT, Google Gemini, xAI Grok) was performed under
work-made-for-hire doctrine and under the exclusive direction of
Mike Kenworthy, founder, AXIOLEV Holdings LLC.

Ring status at tag:
  Ring 1 — Foundations:   COMPLETE
  Ring 2 — Intelligence:  COMPLETE
  Ring 3 — Sovereign:     COMPLETE
  Ring 4 — Capability:    COMPLETE
  Ring 5 — Production:    BLOCKED (Stripe live keys, domain, legal entity)
EOF
)"

  echo "  Tag name: $TAG_NAME"
  if [[ $DRY_RUN -eq 0 ]]; then
    git tag -a "$TAG_NAME" -m "$TAG_MSG"
    git push origin "$TAG_NAME"
    echo "  Tag pushed to origin."
  else
    echo "[DRY-RUN] git tag -a $TAG_NAME -m <ownership block>"
    echo "[DRY-RUN] git push origin $TAG_NAME"
  fi
  echo ""
fi

# ── Done ────────────────────────────────────────────────────
echo "── Complete ─────────────────────────────────────────────"
echo "  Branch: $BRANCH → origin"
[[ -n "$TAG_LABEL" ]] && echo "  Tag:    axiolev-ns-infinity-${TAG_LABEL}-$(date -u +%Y%m%d) → origin"
echo ""
echo "  IP: AXIOLEV Holdings LLC © 2024–2026 · Wyoming, USA"
echo "  All rights reserved."
echo ""
