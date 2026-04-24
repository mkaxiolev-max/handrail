#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 Mike Kenworthy <mike@axiolev.com>
# SPDX-License-Identifier: LicenseRef-AXIOLEV-Proprietary
# AXIOLEV Holdings LLC — NS∞ PreToolUse guard hook
# Sole architect: Mike Kenworthy
# Exit 2 to DENY the tool call; exit 0 to ALLOW.
set -euo pipefail

INPUT="$(cat)"

# Deny: force push to main
if echo "$INPUT" | grep -qE 'git push.*--force|git push.*-f'; then
  echo "[pretool_guard] DENY: force push blocked" >&2
  exit 2
fi

# Deny: destructive rm
if echo "$INPUT" | grep -qE 'rm -rf /|rm -rf ~[^/]|rm -rf ~/axiolev_runtime'; then
  echo "[pretool_guard] DENY: destructive rm blocked" >&2
  exit 2
fi

# Deny: plaintext PAT in command
if echo "$INPUT" | grep -qE 'axiolev-deploy2|ghp_[A-Za-z0-9]{36}'; then
  echo "[pretool_guard] DENY: PAT pattern in command blocked" >&2
  exit 2
fi

# Deny: curl | sh / curl | bash (RCE pattern)
if echo "$INPUT" | grep -qE 'curl[^|]+\|[[:space:]]*(sh|bash)'; then
  echo "[pretool_guard] DENY: curl|sh pattern blocked" >&2
  exit 2
fi

# Deny: write to /etc or private GPG keys
if echo "$INPUT" | grep -qE '/etc/|\.gnupg/private-keys-'; then
  echo "[pretool_guard] DENY: protected path access blocked" >&2
  exit 2
fi

exit 0
