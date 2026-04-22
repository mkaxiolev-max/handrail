# SECRET_DISCOVERY — NS∞ Security Closure Pass
**Date**: 2026-04-22T02:37Z  
**Tool**: gitleaks v8 + manual grep  
**Commits scanned**: 423  
**Bytes scanned**: 91.17 MB

---

## Classification

### 1. Active Tracked Working-Tree Findings (CRITICAL — REMEDIATED)

| File | Rule | Commit First Introduced | Status |
|------|------|------------------------|--------|
| `.terminal_manager/state/state_20260416T233746Z.md` | github-pat | 67ef55f8 | **REMOVED** via `git rm --cached` |
| `.terminal_manager/state/state_20260416T234033Z.md` | github-pat | 67ef55f8 | **REMOVED** via `git rm --cached` |

Action taken: both files removed from git index. `.terminal_manager/state/` and `.terminal_manager/logs/` added to `.gitignore`.

**The PAT `ghp_r...` is still in git history. It MUST be revoked at github.com/settings/tokens.**

---

### 2. Historical-Only Findings (in old commits, not in current working tree)

| File | Rule | Commit | Notes |
|------|------|--------|-------|
| `.env` | anthropic-api-key | abc43ec8 | Committed 2026-04-02, gitignored immediately after |
| `.env` | openai-api-key | abc43ec8 | Same commit |
| `.env` | generic-api-key (Twilio) | abc43ec8 | Same commit |
| `.run/boot/*/compose_resolved.txt` (×9) | generic-api-key | 78cf7c7c | Docker compose config captures with env expansion |
| `.terminal_manager/final_completion.sh` | generic-api-key | 67ef55f8, c9c4d119 | **FALSE POSITIVE** — see below |

Keys from abc43ec8 and 78cf7c7c era should be rotated if not already done.

---

### 3. False Positives

| File | Rule | Reason |
|------|------|--------|
| `services/handrail-adapter-macos/tests/test_clipboard.py` | stripe-access-token | Synthetic `whsec_abc123XYZ==` test fixture for Dignity Guard |
| `.terminal_manager/final_completion.sh` line 970 | generic-api-key | score-phase key variable `P7_[final_cert]` — not a credential |

---

## Summary

| Category | Count |
|----------|-------|
| Active tracked working-tree (critical) | 2 → **0 after remediation** |
| Historical only | 12 |
| False positives | 2 |
| Untracked/log/artifact (not committed) | 3 (.env, services/.env — never tracked) |

---

## Likely Providers Requiring Key Rotation

1. **GitHub** — PAT `ghp_r...` in commit 67ef55f8 (still in history)
2. **Anthropic** — `sk-ant-api03-...` in abc43ec8 (2026-04-02)
3. **OpenAI** — `sk-proj-...` in abc43ec8
4. **Twilio** — auth token in abc43ec8

---

## Rewrite Assessment (preliminary)

History rewrite is **RECOMMENDED** (not required for private repo, but important before any public exposure).  
See `HISTORY_RISK_ASSESSMENT.md` for exact commands.
