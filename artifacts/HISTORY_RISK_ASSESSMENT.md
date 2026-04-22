# HISTORY_RISK_ASSESSMENT — NS∞
**Date**: 2026-04-22T02:38Z  
**Safety tag**: secret-closure-pre-rewrite-20260422T023701Z

---

## Decision

**rewrite_level: RECOMMENDED**

Rewrite is not mechanically required right now (repo is private, secrets acknowledged in .gitleaksignore), but is strongly recommended before:
- Making the repo public
- Sharing the repo URL with any third party
- The GitHub PAT is particularly sensitive — once revoked, risk drops significantly

---

## Triggers

| Finding | Commit | Type | Risk |
|---------|--------|------|------|
| GitHub PAT `ghp_r...` | 67ef55f8 | Active credential (must revoke) | HIGH |
| Anthropic API key | abc43ec8 | Rotatable | HIGH if not rotated |
| OpenAI API key | abc43ec8 | Rotatable | HIGH if not rotated |
| Twilio auth token | abc43ec8 | Rotatable | MEDIUM (already known SID) |
| Compose resolved files with API keys | 78cf7c7c | Derived from .env | MEDIUM |

---

## Exact Commands for History Rewrite (DO NOT RUN without explicit founder authorization)

**Prerequisites:**
```bash
# 1. Confirm safety tag exists
git tag | grep secret-closure-pre-rewrite

# 2. Install git-filter-repo if not present
brew install git-filter-repo

# 3. Create a local backup first
git clone --mirror . ../axiolev_runtime_mirror_backup_$(date +%Y%m%d)
```

**Rewrite Command:**
```bash
# Remove .env from all history
git filter-repo --path .env --invert-paths

# Remove terminal_manager state files from history
git filter-repo --path .terminal_manager/state/state_20260416T233746Z.md --invert-paths
git filter-repo --path .terminal_manager/state/state_20260416T234033Z.md --invert-paths

# Remove compose-resolved boot run files from history
git filter-repo --path .run/ --invert-paths
```

**After rewrite:**
```bash
# Force-push ONLY with explicit founder authorization
# git push --force-with-lease origin integration/max-omega-20260421-191635

# Verify gitleaks clean
gitleaks detect --no-banner --source . --exit-code 1
```

---

## Important: Pre-Rewrite Action

**Rotate credentials FIRST, before any rewrite.** Rotating makes the historical exposure moot even before the rewrite.

1. Revoke GitHub PAT at: github.com/settings/tokens
2. Regenerate Anthropic key at: console.anthropic.com
3. Regenerate OpenAI key at: platform.openai.com
4. Rotate Twilio auth token at: twilio.com console

---

## Force Push Required After Rewrite

Yes — history rewrite rewrites commit SHAs and requires `--force-with-lease` push.  
This will break any branch checkouts. Tag `secret-closure-pre-rewrite-20260422T023701Z` will still point to pre-rewrite HEAD.
