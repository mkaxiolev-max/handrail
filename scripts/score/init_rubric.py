# SPDX-FileCopyrightText: 2026 Mike Kenworthy <mike@axiolev.com>
# SPDX-License-Identifier: LicenseRef-AXIOLEV-Proprietary
# AXIOLEV Holdings LLC — NS∞ Master Integration rubric initializer
# Sole architect: Mike Kenworthy
"""
init_rubric.py — create or reset master_rubric.json.

Usage:
    python3 scripts/score/init_rubric.py --out /path/to/master_rubric.json
    python3 scripts/score/init_rubric.py --out /path/to/master_rubric.json --reset
"""
from __future__ import annotations
import argparse, json
from datetime import datetime, timezone
from pathlib import Path

DIMENSIONS = {
    "A": {"name": "Ontological Substrate",       "points_max": 10, "tier": "Prime"},
    "B": {"name": "Voice / Identity",             "points_max": 10, "tier": "Prime"},
    "C": {"name": "Receipts & Memory",            "points_max": 15, "tier": "Prime"},
    "D": {"name": "Adjudication",                 "points_max": 10, "tier": "Prime"},
    "E": {"name": "Deliberation (5-chamber)",     "points_max": 15, "tier": "Prime"},
    "F": {"name": "Programs / Dignity",           "points_max": 10, "tier": "Prime"},
    "G": {"name": "Quorum & Crypto ID",           "points_max": 10, "tier": "Prime"},
    "H": {"name": "Observability & Gates",        "points_max": 10, "tier": "Prime"},
    "I": {"name": "Resume & Recovery",            "points_max": 5,  "tier": "Prime"},
    "J": {"name": "Doctrine & Docs",              "points_max": 5,  "tier": "Prime"},
    "K": {"name": "Coherence: Local",             "points_max": 10, "tier": "Omega"},
    "L": {"name": "Coherence: Global",            "points_max": 10, "tier": "Omega"},
    "M": {"name": "Field: Edge Flow",             "points_max": 10, "tier": "Omega"},
    "N": {"name": "Field: Diffusion",             "points_max": 10, "tier": "Omega"},
    "O": {"name": "Field: Boundary",              "points_max": 10, "tier": "Omega"},
    "P": {"name": "Thermo: Entropy",              "points_max": 15, "tier": "Omega"},
    "Q": {"name": "Thermo: Dissipation",          "points_max": 15, "tier": "Omega"},
    "R": {"name": "Cross-Plane Invariants",       "points_max": 10, "tier": "Omega"},
    "S": {"name": "Omega Gate Matrix",            "points_max": 5,  "tier": "Omega"},
    "T": {"name": "Omega Doctrine Lift",          "points_max": 5,  "tier": "Omega"},
    "U": {"name": "Quantum-Ready",                "points_max": 10, "tier": "QR"},
    "V": {"name": "Akashic",                      "points_max": 10, "tier": "Akashic"},
}

# NS∞ v3.1 baseline — map legacy v3.1 evidence onto A..J dimensions
# K..V start at 0 (no Omega/QR/Akashic work done yet)
BASELINE_POINTS = {
    "A": 7,  "B": 7,  "C": 12, "D": 8,  "E": 12,
    "F": 7,  "G": 5,  "H": 6,  "I": 4,  "J": 4,
    "K": 0,  "L": 0,  "M": 0,  "N": 0,  "O": 0,
    "P": 0,  "Q": 0,  "R": 0,  "S": 0,  "T": 0,
    "U": 0,  "V": 0,
}

GATES_BASELINE = {str(i): None for i in range(1, 19)}
for i in range(1, 7):
    GATES_BASELINE[str(i)] = {
        "clean_since": "2026-04-23T00:00:00Z",
        "trips_30d": 0,
    }


def build_rubric() -> dict:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    dims = {}
    for k, meta in DIMENSIONS.items():
        dims[k] = {
            "name": meta["name"],
            "tier": meta["tier"],
            "points_earned": BASELINE_POINTS[k],
            "points_max": meta["points_max"],
            "evidence_receipts": [],
        }
    composite = sum(d["points_earned"] for d in dims.values())
    public = min(100, int(composite * 100 / 220))
    return {
        "schema_version": "1.0",
        "timestamp": ts,
        "composite_220": composite,
        "public_score_100": public,
        "dimensions": dims,
        "hard_fail_gates": GATES_BASELINE,
        "hard_fail_summary": {"clean_24h": 6, "clean_30d": 6, "active_trips": 0},
        "phases_completed": [],
        "current_phase": 1,
        "tests_total": 0,
        "bands": {"current": "Substrate-Strong", "target": "Master-Certified"},
        "tags_applied": [],
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--reset", action="store_true")
    args = ap.parse_args()
    out = Path(args.out)
    if out.exists() and not args.reset:
        print(f"[init_rubric] {out} already exists — skipping (use --reset to overwrite)")
        return
    out.parent.mkdir(parents=True, exist_ok=True)
    rubric = build_rubric()
    tmp = out.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(rubric, indent=2, sort_keys=True))
    tmp.replace(out)
    composite = rubric["composite_220"]
    public = rubric["public_score_100"]
    print(f"[init_rubric] wrote {out}  composite={composite}/220  public={public}/100")


if __name__ == "__main__":
    main()
