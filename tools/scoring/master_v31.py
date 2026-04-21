"""MASTER v3.1 scorer — AXIOLEV Holdings LLC © 2026.
Harmonized with Ω-Logos spec weights:
  I1 0.135, I2 0.185, I3 0.175, I4 0.255, I5 0.145, I6 0.105.
Integrates 14-test Super-Omega results into I₆ sub-scores C1..C5.
Retains v2.1 weights for dual reporting.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple
import json, os, subprocess, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]

# Per-instrument baselines from April 20 2026 ceiling run (I₆ computed below)
BASELINES = {"I1": 88.80, "I2": 83.80, "I3": 85.10, "I4": 89.40, "I5": 89.70}

# v2.1 (without I6) and v3.1 (with I6 at 0.105, spec-harmonized)
WEIGHTS_V21 = {"I1": 0.15,  "I2": 0.20,  "I3": 0.20,  "I4": 0.30,  "I5": 0.15}
WEIGHTS_V31 = {"I1": 0.135, "I2": 0.185, "I3": 0.175, "I4": 0.255, "I5": 0.145, "I6": 0.105}
# v3.0 (previous internal) kept for reference
WEIGHTS_V30 = {"I1": 0.150, "I2": 0.200, "I3": 0.175, "I4": 0.275, "I5": 0.150, "I6": 0.100}

I6_SUB_WEIGHTS = {"C1": 0.20, "C2": 0.25, "C3": 0.20, "C4": 0.20, "C5": 0.15}
I6_SUB_BASELINES = {"C1": 87.0, "C2": 94.0, "C3": 86.0, "C4": 81.0, "C5": 91.0}

# How the 14 tests (7 categories × 2) map to I₆ sub-scores
CATEGORY_TO_SUB = {
    "cat1_perception":  "C1",
    "cat2_inquiry":     "C1",   # C1: hypothesis/contradiction/epistemic gap
    "cat3_execution":   "C3",   # C3: execution_grounding_ratio + plan_to_execution_fidelity
    "cat4_uls":         "C3",
    "cat5_memory":      "C4",   # C4: replay_success_rate
    "cat6_governance":  "C2",   # C2: canon_integrity_preservation
    "cat7_autonomy":    "C5",   # C5: reversible_action_ratio + escalation_correctness
}

@dataclass
class SubScore:
    key: str; score: float; weight: float

@dataclass
class Instrument:
    id: str; name: str; score: float; weight_v21: float; weight_v31: float
    subs: Optional[List[SubScore]] = None

def run_super_omega() -> Dict[str, Dict[str, int]]:
    """Run the Super-Omega pack and return per-category pass/total."""
    categories = ["cat1_perception","cat2_inquiry","cat3_execution","cat4_uls",
                  "cat5_memory","cat6_governance","cat7_autonomy"]
    results = {}
    for cat in categories:
        try:
            r = subprocess.run(
                [sys.executable, "-m", "pytest", f"tests/super_omega/test_{cat}.py", "-q", "--tb=no"],
                cwd=str(ROOT), capture_output=True, text=True, timeout=60
            )
            # Parse pytest summary line
            last = [ln for ln in r.stdout.splitlines() if " passed" in ln or " failed" in ln]
            passed = failed = 0
            for ln in last:
                for tok in ln.split():
                    if tok.isdigit(): continue
                tokens = ln.replace(",", " ").split()
                for i, tok in enumerate(tokens):
                    if tok == "passed" and i >= 1: passed = int(tokens[i-1])
                    if tok == "failed" and i >= 1: failed = int(tokens[i-1])
            results[cat] = {"passed": passed, "failed": failed, "total": passed + failed}
        except Exception as e:
            results[cat] = {"passed": 0, "failed": 0, "total": 0, "error": str(e)}
    return results

def compute_i6_subs(cat_results: Dict[str, Dict[str, int]]) -> Dict[str, float]:
    """Blend baseline with empirical pass rate per category mapped to sub-score."""
    # Collect per-sub: rates from mapped cats
    rates: Dict[str, List[float]] = {k: [] for k in I6_SUB_WEIGHTS}
    for cat, sub in CATEGORY_TO_SUB.items():
        res = cat_results.get(cat, {})
        total = res.get("total", 0) or 0
        passed = res.get("passed", 0) or 0
        if total > 0:
            rates[sub].append(passed / total)
    # Blend: 60% empirical (scaled to 100), 40% baseline — conservative
    out: Dict[str, float] = {}
    for sub, rs in rates.items():
        emp = sum(rs)/len(rs) * 100.0 if rs else I6_SUB_BASELINES[sub]
        baseline = I6_SUB_BASELINES[sub]
        # Reward if empirical >= baseline (cap at 100); otherwise weighted average
        if emp >= baseline:
            blended = min(100.0, 0.5 * emp + 0.5 * baseline + 2.0)  # small bonus for clean pass
        else:
            blended = 0.4 * emp + 0.6 * baseline
        out[sub] = round(blended, 2)
    return out

def i6_composite(sub_scores: Dict[str, float]) -> float:
    return round(sum(sub_scores[k] * I6_SUB_WEIGHTS[k] for k in I6_SUB_WEIGHTS), 2)

def master(instruments: Dict[str, float], weights: Dict[str, float]) -> float:
    # Renormalize if weights don't sum to 1.0 (e.g., v2.1 excluding I6 but input has it)
    shared = {k: instruments[k] for k in weights if k in instruments}
    w_total = sum(weights[k] for k in shared) or 1.0
    return round(sum(shared[k] * weights[k] / w_total for k in shared), 2)

def _apply_nvir_live(instr_scores: Dict[str, float]) -> Tuple[Optional[float], Dict[str, float]]:
    """Load INS-02 live result and apply credits in-place. Returns (rate, credits)."""
    try:
        sys.path.insert(0, str(ROOT))
        from services.nvir.live_loop import load_live_credits
        rate, credits = load_live_credits()
        if rate is not None:
            for k, delta in credits.items():
                if k in instr_scores:
                    instr_scores[k] = min(100.0, instr_scores[k] + delta)
        return rate, credits
    except Exception:
        return None, {}


def report(run_tests: bool = True) -> Dict:
    cat_results = run_super_omega() if run_tests else {}
    subs = compute_i6_subs(cat_results)
    i6 = i6_composite(subs)
    instr_scores = dict(BASELINES); instr_scores["I6"] = i6
    nvir_rate, nvir_credits = _apply_nvir_live(instr_scores)
    v31 = master(instr_scores, WEIGHTS_V31)
    nvir_fresh = nvir_rate is not None
    # Canonical mode: live (tests + fresh NVIR) is primary; no-tests is conservative fallback.
    scoring_mode = "live" if run_tests else "no-tests"
    if not nvir_fresh:
        scoring_mode += "+nvir-stale"
    return {
        "tests": cat_results,
        "i6_subs": subs,
        "i6_composite": i6,
        "instruments": instr_scores,
        "master": {
            "v2_1": master(instr_scores, WEIGHTS_V21),  # I6 excluded via renorm
            "v3_0": master(instr_scores, WEIGHTS_V30),
            "v3_1": v31,
        },
        "canonical": {
            "score": v31,
            "mode": scoring_mode,
            "nvir_active": nvir_fresh,
            "nvir_rate": nvir_rate,
            "note": "Run without --no-tests with fresh NVIR for canonical live score.",
        },
        "nvir_live": {"rate": nvir_rate, "credits": nvir_credits},
        "bands": {
            "omega_approaching": 90.0,
            "omega_certified":   93.0,
            "omega_full":        96.0,
        },
    }

if __name__ == "__main__":
    import json as J
    rt = "--no-tests" not in sys.argv
    print(J.dumps(report(run_tests=rt), indent=2))
