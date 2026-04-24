# SPDX-FileCopyrightText: 2026 Mike Kenworthy <mike@axiolev.com>
# SPDX-License-Identifier: LicenseRef-AXIOLEV-Proprietary
# AXIOLEV Holdings LLC — NS∞ per-phase rubric updater
# Sole architect: Mike Kenworthy
"""
update_rubric.py — apply phase results to master_rubric.json.

Usage:
    python3 scripts/score/update_rubric.py \
        --phase 1 --component prime --dimensions A \
        --tests-passed 47 --tests-total 1015 \
        [--gate-trip <gate_id>] [--gate-clean <gate_id>]

Reads RUBRIC env var or defaults to
/Volumes/NSExternal/ALEXANDRIA/score/master_rubric.json.
"""
from __future__ import annotations
import argparse, json, os, sys
from datetime import datetime, timezone
from pathlib import Path

RUBRIC_PATH = Path(os.environ.get(
    "RUBRIC", "/Volumes/NSExternal/ALEXANDRIA/score/master_rubric.json"
))

DIMENSION_MAX = {
    "A":10,"B":10,"C":15,"D":10,"E":15,"F":10,"G":10,"H":10,"I":5,"J":5,
    "K":10,"L":10,"M":10,"N":10,"O":10,"P":15,"Q":15,"R":10,"S":5,"T":5,
    "U":10,"V":10,
}

BANDS = [
    (220, "Master-Certified"),
    (200, "Omega-Certified"),
    (160, "Omega-Grade"),
    (120, "High-Assurance"),
    (80,  "Governance-Bearing"),
    (60,  "Substrate-Strong"),
    (0,   "Pre-Substrate"),
]


def load() -> dict:
    return json.loads(RUBRIC_PATH.read_text())


def save(r: dict) -> None:
    tmp = RUBRIC_PATH.with_suffix(".json.tmp")
    r["timestamp"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    tmp.write_text(json.dumps(r, indent=2, sort_keys=True))
    tmp.replace(RUBRIC_PATH)


def current_band(composite: int) -> str:
    for threshold, name in BANDS:
        if composite >= threshold:
            return name
    return "Pre-Substrate"


def apply_phase(r: dict, phase: int, component: str, dims: list[str],
                tests_passed: int, tests_total: int,
                gate_trips: list[str], gate_cleans: list[str],
                receipt_ids: list[str]) -> dict:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # For each dimension touched by this phase, increase toward ceiling
    # based on pass rate across tests. Simple model: if tests_passed >= tests_total,
    # move the dimension to its maximum. Otherwise partial credit.
    for dim in dims:
        if dim not in r["dimensions"]:
            continue
        d = r["dimensions"][dim]
        max_pts = d["points_max"]
        if tests_total > 0:
            rate = tests_passed / tests_total
        else:
            rate = 0.0
        # Earned = max(current, floor(max * rate))
        earned = max(d["points_earned"], int(max_pts * rate))
        d["points_earned"] = min(earned, max_pts)
        if receipt_ids:
            d["evidence_receipts"].extend(receipt_ids)

    # Gate updates
    for gid in gate_trips:
        if gid in r["hard_fail_gates"]:
            r["hard_fail_gates"][gid] = {"clean_since": None, "trips_30d": (
                (r["hard_fail_gates"][gid] or {}).get("trips_30d", 0) + 1
            )}
    for gid in gate_cleans:
        if gid in r["hard_fail_gates"]:
            r["hard_fail_gates"][gid] = {"clean_since": ts, "trips_30d":
                (r["hard_fail_gates"].get(gid) or {}).get("trips_30d", 0)}

    # Recompute summary
    clean_24h = sum(
        1 for g in r["hard_fail_gates"].values()
        if g and g.get("clean_since") is not None
    )
    r["hard_fail_summary"] = {
        "clean_24h": clean_24h,
        "clean_30d": clean_24h,
        "active_trips": sum(
            1 for g in r["hard_fail_gates"].values()
            if g and g.get("clean_since") is None and g.get("trips_30d", 0) > 0
        ),
    }

    # Recompute composite + public score
    composite = sum(d["points_earned"] for d in r["dimensions"].values())
    public = min(100, int(composite * 100 / 220))
    r["composite_220"] = composite
    r["public_score_100"] = public
    r["bands"]["current"] = current_band(composite)
    r["tests_total"] = max(r.get("tests_total", 0), tests_total)

    if phase not in r["phases_completed"]:
        r["phases_completed"].append(phase)
    r["current_phase"] = phase + 1

    return r


def render_bar(pct: int, width: int = 40) -> str:
    fill = int(pct * width / 100)
    return "█" * fill + "░" * (width - fill)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", type=int, required=True)
    ap.add_argument("--component", required=True)
    ap.add_argument("--dimensions", required=True)  # comma-separated
    ap.add_argument("--tests-passed", type=int, default=0)
    ap.add_argument("--tests-total", type=int, default=0)
    ap.add_argument("--gate-trip", action="append", default=[])
    ap.add_argument("--gate-clean", action="append", default=[])
    ap.add_argument("--receipt-id", action="append", default=[])
    args = ap.parse_args()

    if not RUBRIC_PATH.exists():
        sys.stderr.write(f"[update_rubric] rubric not found at {RUBRIC_PATH}; run init_rubric.py first\n")
        sys.exit(1)

    dims = [d.strip() for d in args.dimensions.split(",") if d.strip()]
    r = load()
    old_composite = r["composite_220"]
    r = apply_phase(
        r, args.phase, args.component, dims,
        args.tests_passed, args.tests_total,
        args.gate_trip, args.gate_clean, args.receipt_id,
    )
    save(r)

    pct = r["public_score_100"]
    bar = render_bar(pct)
    delta = r["composite_220"] - old_composite
    print(f"\nNS∞ Integration Progress: [{bar}] {pct}/100")
    print(f"  phase complete:  {args.phase}/26")
    print(f"  composite:       {old_composite} → {r['composite_220']} (+{delta}) / 220")
    print(f"  band:            {r['bands']['current']} → {r['bands']['target']}")
    print(f"  hard-fails clean (24h): {r['hard_fail_summary']['clean_24h']}/18")
    print(f"  next phase:      {r['current_phase']}\n")


if __name__ == "__main__":
    main()
