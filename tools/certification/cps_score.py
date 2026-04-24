#!/usr/bin/env python3
# Copyright © 2026 AXIOLEV Holdings LLC. All rights reserved.
"""
tools/certification/cps_score.py — I7 certification sub-score calculator.

Runs the ten T-060..T-069 pillar tests via pytest, computes per-pillar scores
(0.0–10.0 each, 100.0 max), then emits artifacts/i7_breakdown.json.

Usage:
    python tools/certification/cps_score.py [--tests-dir PATH] [--artifacts-dir PATH]
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Pillar registry — maps pillar id to test module path and human label
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parents[2]

PILLARS = [
    {
        "id":       "T060_governance",
        "label":    "Governance",
        "desc":     "Policy authority chain verifiable",
        "test_file": "tests/certification/test_T060_governance.py",
    },
    {
        "id":       "T061_risk",
        "label":    "Risk",
        "desc":     "Risk register coverage >= defined scope",
        "test_file": "tests/certification/test_T061_risk.py",
    },
    {
        "id":       "T062_lineage",
        "label":    "Lineage",
        "desc":     "Lineage Fabric end-to-end chain integrity",
        "test_file": "tests/certification/test_T062_lineage.py",
    },
    {
        "id":       "T063_transparency",
        "label":    "Transparency",
        "desc":     "Public-facing artifacts resolvable + signed",
        "test_file": "tests/certification/test_T063_transparency.py",
    },
    {
        "id":       "T064_safety",
        "label":    "Safety",
        "desc":     "Kill-switch + pause-budget bounds enforced",
        "test_file": "tests/certification/test_T064_safety.py",
    },
    {
        "id":       "T065_bias",
        "label":    "Bias",
        "desc":     "Bias audit pack runs clean on fixtures",
        "test_file": "tests/certification/test_T065_bias.py",
    },
    {
        "id":       "T066_security",
        "label":    "Security",
        "desc":     "Secret-scan + SBOM current; CVE SLA met",
        "test_file": "tests/certification/test_T066_security.py",
    },
    {
        "id":       "T067_runtime",
        "label":    "Runtime",
        "desc":     "Runtime invariants monitored + alertable",
        "test_file": "tests/certification/test_T067_runtime.py",
    },
    {
        "id":       "T068_auditability",
        "label":    "Auditability",
        "desc":     "Audit-log completeness + tamper-evident",
        "test_file": "tests/certification/test_T068_auditability.py",
    },
    {
        "id":       "T069_continuous",
        "label":    "Continuous",
        "desc":     "Continuous-cert daily job green for 7d rolling",
        "test_file": "tests/certification/test_T069_continuous.py",
    },
]

_POINTS_PER_PILLAR = 10.0
_MAX_SCORE         = _POINTS_PER_PILLAR * len(PILLARS)   # 100.0


# ---------------------------------------------------------------------------
# Test runner
# ---------------------------------------------------------------------------

def _run_pillar(pillar: dict, tests_dir: Path) -> dict:
    """Run a single pillar test file; return a result dict."""
    test_path = tests_dir / pillar["test_file"]
    if not test_path.exists():
        return {
            "status":        "missing",
            "tests_passed":  0,
            "tests_failed":  0,
            "tests_total":   0,
            "score":         0.0,
            "error":         f"Test file not found: {test_path}",
        }

    proc = subprocess.run(
        [sys.executable, "-m", "pytest", str(test_path), "-q", "--tb=short", "--no-header"],
        capture_output=True,
        text=True,
        cwd=str(tests_dir),
    )

    stdout = proc.stdout + proc.stderr
    passed = _parse_count(stdout, "passed")
    failed = _parse_count(stdout, "failed")
    errors = _parse_count(stdout, "error")
    total  = passed + failed + errors

    failed_total = failed + errors
    status = "pass" if proc.returncode == 0 else "fail"
    score  = _POINTS_PER_PILLAR * (passed / total) if total > 0 else 0.0

    return {
        "status":       status,
        "tests_passed": passed,
        "tests_failed": failed_total,
        "tests_total":  total,
        "score":        round(score, 2),
        "stdout":       stdout[-2000:] if len(stdout) > 2000 else stdout,
    }


def _parse_count(output: str, keyword: str) -> int:
    """Extract a count like '3 passed' from pytest summary line."""
    import re
    match = re.search(r"(\d+)\s+" + keyword, output)
    return int(match.group(1)) if match else 0


# ---------------------------------------------------------------------------
# Score aggregation
# ---------------------------------------------------------------------------

def compute_i7_breakdown(tests_dir: Path) -> dict:
    """Run all pillars, aggregate scores, return breakdown dict."""
    now = datetime.now(timezone.utc).isoformat()
    pillar_results: dict[str, dict] = {}
    total_score = 0.0

    for pillar in PILLARS:
        result = _run_pillar(pillar, tests_dir)
        pillar_results[pillar["id"]] = {
            "label":        pillar["label"],
            "desc":         pillar["desc"],
            "test_file":    pillar["test_file"],
            "score":        result["score"],
            "max":          _POINTS_PER_PILLAR,
            "status":       result["status"],
            "tests_passed": result["tests_passed"],
            "tests_failed": result["tests_failed"],
            "tests_total":  result["tests_total"],
        }
        if "error" in result:
            pillar_results[pillar["id"]]["error"] = result["error"]
        total_score += result["score"]

    i7_score = round(total_score / _MAX_SCORE * 10.0, 3)

    return {
        "generated_at":  now,
        "i7_score":      i7_score,
        "i7_max":        10.0,
        "raw_score":     round(total_score, 2),
        "raw_max":       _MAX_SCORE,
        "pillars_pass":  sum(1 for p in pillar_results.values() if p["status"] == "pass"),
        "pillars_fail":  sum(1 for p in pillar_results.values() if p["status"] != "pass"),
        "pillars_total": len(PILLARS),
        "pillars":       pillar_results,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compute I7 certification sub-scores from T-060..T-069 pillar tests."
    )
    parser.add_argument(
        "--tests-dir",
        default=str(_REPO_ROOT),
        help="Repository root (contains tests/certification/). Default: repo root.",
    )
    parser.add_argument(
        "--artifacts-dir",
        default=str(_REPO_ROOT / "artifacts"),
        help="Directory to write i7_breakdown.json. Default: <repo>/artifacts/.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print breakdown to stdout without writing the artifact file.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    tests_dir    = Path(args.tests_dir)
    artifacts_dir = Path(args.artifacts_dir)

    print("NS∞ I7 Certification Score — computing pillar sub-scores …")
    breakdown = compute_i7_breakdown(tests_dir)

    # Pretty-print summary
    print(f"\n{'─' * 60}")
    print(f"  I7 Score: {breakdown['i7_score']:.3f} / {breakdown['i7_max']:.1f}")
    print(f"  Pillars:  {breakdown['pillars_pass']} pass / {breakdown['pillars_fail']} fail")
    print(f"{'─' * 60}")
    for pid, p in breakdown["pillars"].items():
        icon = "✓" if p["status"] == "pass" else "✗"
        print(f"  {icon} {pid:<22} {p['score']:5.1f}/{p['max']:.0f}  {p['label']}")
    print(f"{'─' * 60}\n")

    if args.dry_run:
        print(json.dumps(breakdown, indent=2))
        return 0

    artifacts_dir.mkdir(parents=True, exist_ok=True)
    out_path = artifacts_dir / "i7_breakdown.json"
    out_path.write_text(json.dumps(breakdown, indent=2) + "\n")
    print(f"Artifact written: {out_path}")

    return 0 if breakdown["pillars_fail"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
