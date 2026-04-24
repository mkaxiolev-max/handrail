"""MASTER v3.2 scorer — AXIOLEV Holdings LLC © 2026.

Adds I7 (CPS Certification Power Score) at w=0.10; I1–I6 rescaled to maintain
sum-to-one invariant.

  v3.2 weights: I1=0.1215  I2=0.162  I3=0.162  I4=0.243
                I5=0.1215  I6=0.090  I7=0.100

Authoritative input: artifacts/ns_infinity_scorecard.json
Credits applied from: artifacts/max_closure/M*.json (milestone credit packages)
  - Direct credits  "Ix": delta      → +delta to Ix (weight 1.0)
  - I6 sub-credits  "I6.Cy": delta   → +delta * I6_SUB_WEIGHTS[Cy] to I6
  - Other sub-creds "Ix.sub": delta  → +delta * DEFAULT_SUB_WEIGHT(0.20) to Ix
  All scores hard-capped at 100.0; scorecard ceiling shown in gap report.
I7 score loaded from: artifacts/i7_breakdown.json
Emits: artifacts/FINAL_MAX_CERTIFICATION.json + .md
"""
from __future__ import annotations

import json
import pathlib
import sys
from datetime import datetime, timezone
from typing import Dict, List, Tuple

ROOT = pathlib.Path(__file__).resolve().parents[2]
ARTIFACTS = ROOT / "artifacts"
SCORECARD_PATH = ARTIFACTS / "ns_infinity_scorecard.json"
M_CREDITS_DIR = ARTIFACTS / "max_closure"
I7_BREAKDOWN_PATH = ARTIFACTS / "i7_breakdown.json"

# --------------------------------------------------------------------------- #
# Weight tables
# --------------------------------------------------------------------------- #

WEIGHTS_V21: Dict[str, float] = {
    "I1": 0.15, "I2": 0.20, "I3": 0.20, "I4": 0.30, "I5": 0.15,
}
WEIGHTS_V30: Dict[str, float] = {
    "I1": 0.150, "I2": 0.200, "I3": 0.175, "I4": 0.275, "I5": 0.150, "I6": 0.100,
}
WEIGHTS_V31: Dict[str, float] = {
    "I1": 0.135, "I2": 0.185, "I3": 0.175, "I4": 0.255, "I5": 0.145, "I6": 0.105,
}
WEIGHTS_V32: Dict[str, float] = {
    "I1": 0.1215, "I2": 0.162, "I3": 0.162, "I4": 0.243,
    "I5": 0.1215, "I6": 0.090, "I7": 0.100,
}

# Verified invariant: sum(WEIGHTS_V31) == 1.0, sum(WEIGHTS_V32) == 1.0
assert abs(sum(WEIGHTS_V31.values()) - 1.0) < 1e-9, "v3.1 weight sum != 1"
assert abs(sum(WEIGHTS_V32.values()) - 1.0) < 1e-9, "v3.2 weight sum != 1"

# I6 sub-weights (Ω-Logos spec)
I6_SUB_WEIGHTS: Dict[str, float] = {
    "C1": 0.20, "C2": 0.25, "C3": 0.20, "C4": 0.20, "C5": 0.15,
}
DEFAULT_SUB_WEIGHT: float = 0.20  # assumed per sub-dimension for I1–I5, I7

# --------------------------------------------------------------------------- #
# Band thresholds (descending order)
# --------------------------------------------------------------------------- #

BAND_THRESHOLDS: List[Tuple[float, str]] = [
    (96.0, "Transcendent 96"),
    (95.0, "SuperMax 95"),
    (93.0, "Certified 93"),
    (90.0, "Approaching 90"),
    (0.0,  "Below 90"),
]

PRIOR_SUPERMAX: float = 92.42


# --------------------------------------------------------------------------- #
# Core functions (importable by tests)
# --------------------------------------------------------------------------- #

def classify_band(score: float) -> str:
    """Return the certification band label for a composite score."""
    for threshold, label in BAND_THRESHOLDS:
        if score >= threshold:
            return label
    return "Below 90"


def weighted_composite(scores: Dict[str, float], weights: Dict[str, float]) -> float:
    """Compute weighted average of scores, renormalizing over instruments present.

    Instruments in `weights` but absent from `scores` are excluded and the
    remaining weights are renormalized so the result stays on the 0–100 scale.
    """
    shared = {k: scores[k] for k in weights if k in scores}
    w_total = sum(weights[k] for k in shared) or 1.0
    return round(sum(shared[k] * weights[k] / w_total for k in shared), 2)


# --------------------------------------------------------------------------- #
# Data loaders
# --------------------------------------------------------------------------- #

def load_scorecard() -> Dict[str, dict]:
    """Load ns_infinity_scorecard.json; return the instruments sub-dict."""
    data = json.loads(SCORECARD_PATH.read_text())
    return data["instruments"]


def load_milestone_credits() -> Dict[str, float]:
    """Aggregate per-instrument credits from artifacts/max_closure/M*.json.

    Each M*.json may contain an optional ``credits`` object whose keys are
    either direct instrument IDs ("I4", "I7") or dot-notation sub-keys
    ("I6.C2", "I5.reversibility").  Files missing the field are silently
    skipped.  Gitleaks scan files are excluded by name pattern.
    """
    totals: Dict[str, float] = {}
    search_dirs = [M_CREDITS_DIR, ARTIFACTS]
    seen: set = set()
    for d in search_dirs:
        if not d.exists():
            continue
        for path in sorted(d.glob("M*.json")):
            if path in seen or "gitleaks" in path.name:
                continue
            seen.add(path)
            try:
                data = json.loads(path.read_text())
                for key, delta in (data.get("credits") or {}).items():
                    totals[key] = totals.get(key, 0.0) + float(delta)
            except Exception:
                pass
    return totals


def _resolve_credits_to_deltas(
    raw_credits: Dict[str, float],
    known_instruments: set,
) -> Dict[str, float]:
    """Expand raw credit keys into per-instrument float deltas.

    Rules
    -----
    - "Ix" (no dot, known instrument)   → delta * 1.0
    - "I6.Cy" (I6 sub-credit)           → delta * I6_SUB_WEIGHTS.get(Cy, DEFAULT_SUB_WEIGHT)
    - "Ix.sub" (other sub-credit)        → delta * DEFAULT_SUB_WEIGHT
    """
    deltas: Dict[str, float] = {}
    for key, delta in raw_credits.items():
        if "." in key:
            parent, sub = key.split(".", 1)
            if parent not in known_instruments:
                continue
            if parent == "I6":
                w = I6_SUB_WEIGHTS.get(sub, DEFAULT_SUB_WEIGHT)
            else:
                w = DEFAULT_SUB_WEIGHT
            deltas[parent] = deltas.get(parent, 0.0) + delta * w
        elif key in known_instruments:
            deltas[key] = deltas.get(key, 0.0) + delta
    return deltas


def load_i7_score() -> float:
    """Return I7 on the 0–100 scale from artifacts/i7_breakdown.json."""
    if not I7_BREAKDOWN_PATH.exists():
        return 0.0
    d = json.loads(I7_BREAKDOWN_PATH.read_text())
    raw = float(d.get("raw_score", 0.0))
    raw_max = float(d.get("raw_max", 100.0))
    return round(raw / raw_max * 100.0, 2) if raw_max > 0 else 0.0


# --------------------------------------------------------------------------- #
# Report builder
# --------------------------------------------------------------------------- #

def report() -> dict:
    instruments_meta = load_scorecard()
    milestone_credits = load_milestone_credits()
    i7_score = load_i7_score()

    known = set(instruments_meta.keys())
    deltas = _resolve_credits_to_deltas(milestone_credits, known)

    # Effective scores = scorecard current + resolved deltas, hard-capped at 100.0
    scores: Dict[str, float] = {}
    for inst, meta in instruments_meta.items():
        base = float(meta["current"])
        scores[inst] = min(100.0, base + deltas.get(inst, 0.0))

    # I7 is authoritative from i7_breakdown (live certification result)
    scores["I7"] = i7_score

    # Scorecard ceilings used for gap reporting only
    sc_ceilings: Dict[str, float] = {
        inst: float(meta.get("ceiling", 100.0))
        for inst, meta in instruments_meta.items()
    }

    v21 = weighted_composite(scores, WEIGHTS_V21)
    v30 = weighted_composite(scores, WEIGHTS_V30)
    v31 = weighted_composite(scores, WEIGHTS_V31)
    v32 = weighted_composite(scores, WEIGHTS_V32)

    ceiling_scores_100 = {k: 100.0 for k in scores}
    ceiling_v32 = weighted_composite(ceiling_scores_100, WEIGHTS_V32)

    # Per-instrument table (ordered by WEIGHTS_V32 key order)
    instruments_out: Dict[str, dict] = {}
    gaps_remaining: List[dict] = []
    for inst, w in WEIGHTS_V32.items():
        curr = scores.get(inst, 0.0)
        sc_ceil = sc_ceilings.get(inst, 100.0)
        gap_to_sc = round(max(0.0, sc_ceil - curr), 4)
        gap_to_100 = round(100.0 - curr, 4)
        instruments_out[inst] = {
            "name": instruments_meta.get(inst, {}).get("name", inst),
            "current": curr,
            "scorecard_ceiling": sc_ceil,
            "gap_to_scorecard_ceiling": gap_to_sc,
            "gap_to_100": gap_to_100,
            "weight_v32": w,
            "ceiling_note": instruments_meta.get(inst, {}).get("ceiling_note", ""),
        }
        if gap_to_100 > 0.001:
            gaps_remaining.append({
                "instrument": inst,
                "current": curr,
                "ceiling": 100.0,
                "gap": gap_to_100,
                "composite_impact": round(gap_to_100 * w, 4),
                "note": instruments_meta.get(inst, {}).get("ceiling_note", ""),
            })
    gaps_remaining.sort(key=lambda x: -x["composite_impact"])

    delta_vs_supermax = round(v32 - PRIOR_SUPERMAX, 2)

    return {
        "generated": datetime.now(timezone.utc).isoformat(),
        "scorer_version": "v3.2",
        "instruments": instruments_out,
        "composites": {
            "v2_1": v21,
            "v3_0": v30,
            "v3_1": v31,
            "v3_2": v32,
        },
        "band": classify_band(v32),
        "prior_supermax": PRIOR_SUPERMAX,
        "delta_vs_supermax": delta_vs_supermax,
        "ceiling_v32": ceiling_v32,
        "gap_to_ceiling": round(ceiling_v32 - v32, 2),
        "gaps_remaining": gaps_remaining,
        "milestone_credits_applied": milestone_credits,
        "resolved_deltas": deltas,
        "weights": {
            "v2_1": WEIGHTS_V21,
            "v3_0": WEIGHTS_V30,
            "v3_1": WEIGHTS_V31,
            "v3_2": WEIGHTS_V32,
        },
    }


# --------------------------------------------------------------------------- #
# Artifact emitters
# --------------------------------------------------------------------------- #

def _render_md(d: dict) -> str:
    c = d["composites"]
    v32 = c["v3_2"]

    def cleared(t: float) -> str:
        return "✓" if v32 >= t else "✗"

    lines = [
        "# NS∞ FINAL MAX CERTIFICATION",
        "",
        f"**AXIOLEV Holdings LLC © 2026**  ",
        f"Generated: {d['generated']}",
        "",
        "## Composite Scores",
        "",
        "| Version | Score | Band |",
        "|---------|------:|------|",
        f"| v2.1    | {c['v2_1']:.2f} | {classify_band(c['v2_1'])} |",
        f"| v3.0    | {c['v3_0']:.2f} | {classify_band(c['v3_0'])} |",
        f"| v3.1    | {c['v3_1']:.2f} | {classify_band(c['v3_1'])} |",
        f"| **v3.2** | **{v32:.2f}** | **{d['band']}** |",
        "",
        f"**Prior SUPERMAX (v3.1):** {d['prior_supermax']}  ",
        f"**Delta v3.2 vs SUPERMAX:** {d['delta_vs_supermax']:+.2f}",
        "",
        "## Per-Instrument Detail (v3.2 weights)",
        "",
        "| Instrument | Name | Current | SC Ceiling | Gap→100 | Weight |",
        "|:----------:|------|--------:|-----------:|--------:|-------:|",
    ]
    for inst, m in d["instruments"].items():
        lines.append(
            f"| {inst} | {m['name']} | {m['current']:.2f} | {m['scorecard_ceiling']:.2f} "
            f"| {m['gap_to_100']:.2f} | {m['weight_v32']:.4f} |"
        )
    lines += [
        "",
        f"**v3.2 Ceiling (all at 100):** {d['ceiling_v32']:.2f}  ",
        f"**Gap to 100-ceiling:** {d['gap_to_ceiling']:.2f}",
        "",
        "## Remaining Gaps to 100.0 (descending composite impact)",
        "",
    ]
    if d["gaps_remaining"]:
        lines += [
            "| Instrument | Current | Gap→100 | Composite Impact |",
            "|:----------:|--------:|--------:|-----------------:|",
        ]
        for g in d["gaps_remaining"]:
            lines.append(
                f"| {g['instrument']} | {g['current']:.2f} "
                f"| {g['gap']:.2f} | {g['composite_impact']:.4f} |"
            )
        lines += [""]
        for g in d["gaps_remaining"]:
            if g["note"]:
                lines.append(f"- **{g['instrument']}**: {g['note']}")
    else:
        lines.append("_No gaps — all instruments at 100.0._")
    lines += [
        "",
        "## Band Thresholds",
        "",
        "| Band | Threshold | Cleared |",
        "|------|----------:|:-------:|",
        f"| Approaching 90  | 90.0 | {cleared(90.0)} |",
        f"| Certified 93    | 93.0 | {cleared(93.0)} |",
        f"| SuperMax 95     | 95.0 | {cleared(95.0)} |",
        f"| Transcendent 96 | 96.0 | {cleared(96.0)} |",
        "",
        "---",
        "",
        "_NS∞ MASTER scorer v3.2 — AXIOLEV Holdings LLC © 2026_",
        "",
    ]
    return "\n".join(lines)


def emit_artifacts(data: dict) -> Tuple[pathlib.Path, pathlib.Path]:
    """Write FINAL_MAX_CERTIFICATION.json and .md to artifacts/."""
    ARTIFACTS.mkdir(parents=True, exist_ok=True)

    json_path = ARTIFACTS / "FINAL_MAX_CERTIFICATION.json"
    json_path.write_text(json.dumps(data, indent=2) + "\n")

    md_path = ARTIFACTS / "FINAL_MAX_CERTIFICATION.md"
    md_path.write_text(_render_md(data))

    return json_path, md_path


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

if __name__ == "__main__":
    data = report()
    j_path, m_path = emit_artifacts(data)
    print(json.dumps(data, indent=2))
    print(
        f"\nArtifacts written:\n  {j_path}\n  {m_path}",
        file=sys.stderr,
    )
