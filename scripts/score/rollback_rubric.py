# SPDX-FileCopyrightText: 2026 Mike Kenworthy <mike@axiolev.com>
# SPDX-License-Identifier: LicenseRef-AXIOLEV-Proprietary
# AXIOLEV Holdings LLC — NS∞ rubric rollback
# Sole architect: Mike Kenworthy
"""
rollback_rubric.py — restore master_rubric.json to the state at a given tag.

Usage:
    python3 scripts/score/rollback_rubric.py --to-tag axiolev-ns-infinity-prime-p5-...
"""
from __future__ import annotations
import argparse, json, os, subprocess, sys
from pathlib import Path

RUBRIC_PATH = Path(os.environ.get(
    "RUBRIC", "/Volumes/NSExternal/ALEXANDRIA/score/master_rubric.json"
))
RECEIPTS = Path("/Volumes/NSExternal/ALEXANDRIA/receipts")


def phases_up_to_tag(tag: str) -> list[int]:
    """Return list of phase numbers encoded in tags up to and including <tag>."""
    result = subprocess.run(
        ["git", "tag", "-l", "axiolev-ns-infinity-*", "--sort=creatordate"],
        capture_output=True, text=True,
    )
    tags = result.stdout.strip().splitlines()
    phases = []
    for t in tags:
        import re
        m = re.search(r"-p(\d+)-", t)
        if m:
            phases.append(int(m.group(1)))
        if t == tag:
            break
    return phases


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--to-tag", required=True)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    phases = phases_up_to_tag(args.to_tag)
    print(f"[rollback] phases present up to {args.to_tag}: {phases}")
    print(f"[rollback] rolling back to phase {max(phases) if phases else 0}")

    if args.dry_run:
        print("[rollback] dry-run — not modifying rubric")
        return

    backup = RUBRIC_PATH.with_suffix(f".rollback-backup.json")
    if RUBRIC_PATH.exists():
        backup.write_text(RUBRIC_PATH.read_text())
        print(f"[rollback] backed up current rubric to {backup}")

    from scripts.score.init_rubric import build_rubric
    r = build_rubric()
    for phase in sorted(phases):
        r["phases_completed"].append(phase)
        r["current_phase"] = phase + 1
    r["tags_applied"] = [args.to_tag]

    tmp = RUBRIC_PATH.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(r, indent=2, sort_keys=True))
    tmp.replace(RUBRIC_PATH)
    print(f"[rollback] rubric reset to phase {r['current_phase'] - 1}  composite={r['composite_220']}/220")


if __name__ == "__main__":
    main()
