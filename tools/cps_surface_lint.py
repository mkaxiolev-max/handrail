#!/usr/bin/env python3
# Copyright © 2026 Axiolev. All rights reserved.
"""
CPS Surface Lint — CI gate
==========================
Reads artifacts/cps_action_surface.json and exits non-zero if any
action-surface site is untiered (missing @cps(tier=...) annotation).

Exit codes:
    0  — all sites are tiered (or there are no sites)
    1  — one or more untiered sites detected
    2  — the action_surface.json file is missing or malformed
         (run `python services/handrail/audit.py` first)

Usage:
    python tools/cps_surface_lint.py
    python tools/cps_surface_lint.py --surface artifacts/cps_action_surface.json
    python tools/cps_surface_lint.py --fail-under-tiered-pct 80
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_DEFAULT_SURFACE = _REPO_ROOT / "artifacts" / "cps_action_surface.json"


def _load_surface(path: Path) -> dict:
    if not path.exists():
        print(f"[cps-lint] ERROR: action surface file not found: {path}", file=sys.stderr)
        print("[cps-lint] Run: python services/handrail/audit.py", file=sys.stderr)
        sys.exit(2)
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        print(f"[cps-lint] ERROR: malformed JSON in {path}: {exc}", file=sys.stderr)
        sys.exit(2)


def _report(manifest: dict, fail_under_pct: float | None) -> int:
    sites: list[dict] = manifest.get("sites", [])
    summary: dict = manifest.get("summary", {})
    total: int = summary.get("total", len(sites))
    tiered: int = summary.get("tiered", sum(1 for s in sites if s.get("tiered")))
    untiered_sites = [s for s in sites if not s.get("tiered")]
    untiered: int = len(untiered_sites)

    tiered_pct = (tiered / total * 100) if total else 100.0

    print(f"[cps-lint] CPS action surface report")
    print(f"[cps-lint]   generated_at : {manifest.get('generated_at', 'unknown')}")
    print(f"[cps-lint]   total sites  : {total}")
    print(f"[cps-lint]   tiered       : {tiered}  ({tiered_pct:.1f}%)")
    print(f"[cps-lint]   untiered     : {untiered}")

    if untiered_sites:
        print()
        print(f"[cps-lint] UNTIERED SITES ({untiered}):")
        for site in untiered_sites:
            print(
                f"  [{site.get('kind', '?')}] "
                f"{site.get('file', '?')}:{site.get('line', '?')} "
                f"  symbol={site.get('symbol', '?')!r} "
                f"  detail={site.get('detail', '?')!r}"
            )

    # ── Failure conditions ──────────────────────────────────────────────────
    failed = False

    if untiered > 0:
        print()
        print(f"[cps-lint] FAIL: {untiered} untiered action-surface site(s) found.")
        print("[cps-lint]       Add @cps(tier='Rx') to each flagged function.")
        failed = True

    if fail_under_pct is not None and tiered_pct < fail_under_pct:
        print()
        print(
            f"[cps-lint] FAIL: tiered coverage {tiered_pct:.1f}% is below "
            f"required minimum {fail_under_pct:.1f}%."
        )
        failed = True

    if not failed:
        print()
        print("[cps-lint] OK: all action-surface sites are tiered.")

    return 1 if failed else 0


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="CPS surface lint gate")
    parser.add_argument(
        "--surface", default=str(_DEFAULT_SURFACE),
        help="Path to cps_action_surface.json (default: artifacts/cps_action_surface.json)",
    )
    parser.add_argument(
        "--fail-under-tiered-pct", type=float, default=None, metavar="PCT",
        help="Fail if tiered coverage percentage is below PCT (e.g. 80.0)",
    )
    parser.add_argument(
        "--quiet", action="store_true",
        help="Suppress per-site details; only print summary and PASS/FAIL",
    )
    args = parser.parse_args(argv)

    surface_path = Path(args.surface)
    manifest = _load_surface(surface_path)
    return _report(manifest, args.fail_under_tiered_pct)


if __name__ == "__main__":
    sys.exit(main())
