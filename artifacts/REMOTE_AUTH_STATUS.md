# REMOTE_AUTH_STATUS — NS∞
**Date**: 2026-04-22T02:38Z

---

## Current Remote

```
origin  https://github.com/mkaxiolev-max/handrail.git (fetch)
origin  https://github.com/mkaxiolev-max/handrail.git (push)
```

**Mode: HTTPS**

---

## SSH Auth Check

```bash
ssh -T git@github.com
→ Host key verification failed.
```

**SSH: NOT configured.** No `~/.ssh/` directory exists on this machine.

---

## Push Readiness

| Check | Status |
|-------|--------|
| Remote configured | YES |
| Remote mode | HTTPS (not SSH) |
| SSH keys on disk | NONE (no ~/.ssh/ directory) |
| SSH auth to GitHub | FAILED (host key verification) |
| Credential store | Unknown — likely macOS Keychain via HTTPS |
| Push blocked? | Unknown — HTTPS PAT credential may work via Keychain |

**push_ready: UNKNOWN** — HTTPS push may work if a PAT is stored in macOS Keychain for github.com. Cannot verify without attempting push.

---

## Security Note

The GitHub PAT `ghp_r...` found in history (commit 67ef55f8) may be the same PAT stored in macOS Keychain for HTTPS pushes. **If that PAT is revoked (required for security), HTTPS push will break until a new PAT is added.**

---

## Recommended Path: Switch to SSH

```bash
# Step 1: Generate SSH key
ssh-keygen -t ed25519 -C "mkaxiolev@gmail.com" -f ~/.ssh/github_axiolev

# Step 2: Add to SSH agent
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/github_axiolev

# Step 3: Add public key to GitHub
# Copy key: pbcopy < ~/.ssh/github_axiolev.pub
# Then: github.com → Settings → SSH Keys → New SSH Key

# Step 4: Add GitHub host key to known_hosts
ssh-keyscan -H github.com >> ~/.ssh/known_hosts

# Step 5: Verify
ssh -T git@github.com

# Step 6: Switch remote to SSH
git remote set-url origin git@github.com:mkaxiolev-max/handrail.git
```

---

## Exact Next Command (first step to enable SSH push)

```bash
ssh-keygen -t ed25519 -C "mkaxiolev@gmail.com" -f ~/.ssh/github_axiolev
```
