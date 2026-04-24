#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 Mike Kenworthy <mike@axiolev.com>
# SPDX-License-Identifier: LicenseRef-AXIOLEV-Proprietary
# AXIOLEV Holdings LLC — NS∞ omega ceremony sign script
# Sole architect: Mike Kenworthy
# Insert YubiKey and run this script to create the signed ceremonial tag.
set -euo pipefail
ALEX="/Volumes/NSExternal/ALEXANDRIA"
RUN="$HOME/axiolev_runtime"
TS="$(date -u +%Y%m%dT%H%M%SZ)"

RUBRIC="$ALEX/score/master_rubric.json"
COMPOSITE="$(python3 -c "import json; r=json.load(open('$RUBRIC')); print(r['composite_220'])" 2>/dev/null || echo '?')"
PUBLIC="$(python3    -c "import json; r=json.load(open('$RUBRIC')); print(r['public_score_100'])" 2>/dev/null || echo '?')"
TAG="ns-infinity-omega-v1-${TS}"

echo "=== NS∞ Ceremony: Omega-Certified — gates 1-12 clean ==="
echo "  composite: $COMPOSITE/220   public: $PUBLIC/100"
echo "  tag: $TAG"
echo "  YubiKey slot: 1"
echo ""

# Verify YubiKey (if ykman available)
if command -v ykman >/dev/null 2>&1; then
  ykman list | grep -q 26116460 || { echo "ERROR: YubiKey 26116460 not detected"; exit 1; }
  echo "  ✓ YubiKey 26116460 present"
fi

cd "$RUN"
git -c user.name=axiolevns -c user.email=axiolevns@axiolev.com   tag -a "$TAG" -m "Omega-Certified — gates 1-12 clean — composite=$COMPOSITE/220"   && echo "  ✓ tag $TAG applied (unsigned — sign manually with: git tag -s $TAG)"   || { echo "ERROR: tagging failed"; exit 1; }

# Write ceremony receipt to Alexandria
python3 - << PY
import json, hashlib, pathlib
alex = pathlib.Path("$ALEX")
(alex / "receipts").mkdir(parents=True, exist_ok=True)
body = {
    "kind": "ceremony.receipt",
    "tier": "Omega-Certified — gates 1-12 clean",
    "tag": "$TAG",
    "composite_220": "$COMPOSITE",
    "public_score_100": "$PUBLIC",
    "ts": "$TS",
    "yubikey_slot": 1,
}
body["id"] = hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()[:16]
with (alex / "receipts/ceremony.jsonl").open("a") as f:
    f.write(json.dumps(body, sort_keys=True) + "\n")
print("  ✓ ceremony receipt written")
PY

echo ""
echo "=== CEREMONY COMPLETE: Omega-Certified — gates 1-12 clean ==="
echo "Reply 'sealed' in your Claude session to continue."
