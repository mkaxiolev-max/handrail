#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 Mike Kenworthy <mike@axiolev.com>
# SPDX-License-Identifier: LicenseRef-AXIOLEV-Proprietary
# AXIOLEV Holdings LLC — NS∞ PostToolUse SPDX header injector
# Sole architect: Mike Kenworthy
# Reads JSON from stdin; extracts file_path; prepends SPDX header to new .py files.
set -euo pipefail

INPUT="$(cat)"
FILE_PATH="$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('file_path',''))" 2>/dev/null || echo "")"

[[ -z "$FILE_PATH" ]] && exit 0
[[ "${FILE_PATH##*.}" != "py" ]] && exit 0
[[ ! -f "$FILE_PATH" ]] && exit 0

HEADER='# SPDX-FileCopyrightText: 2026 Mike Kenworthy <mike@axiolev.com>
# SPDX-License-Identifier: LicenseRef-AXIOLEV-Proprietary
# AXIOLEV Holdings LLC
# Sole architect: Mike Kenworthy'

# Only add if not already present
if ! head -4 "$FILE_PATH" | grep -q "SPDX-FileCopyrightText"; then
  TMPFILE="$(mktemp)"
  printf '%s\n' "$HEADER" > "$TMPFILE"
  cat "$FILE_PATH" >> "$TMPFILE"
  mv "$TMPFILE" "$FILE_PATH"
fi
exit 0
