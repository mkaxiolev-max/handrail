"""Run the collapse-readiness rubric on the synthetic corpus; return nightly report."""
from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path
from services.coherence_kernel import readiness
from services.coherence_kernel.harness.corpus import load_corpus, CORPUS_PATH


def run_night(night_index: int, corpus_path: Path = CORPUS_PATH, db_path: Path | None = None) -> dict:
    """Score all corpus branches; return structured nightly report."""
    branches = load_corpus(corpus_path)
    scores = []
    for branch in branches:
        rs = readiness.compute_readiness(branch, db_path=db_path)
        scores.append(rs.score_100)

    n = len(scores)
    aggregate = round(sum(scores) / n, 4) if n else 0.0
    above_threshold = sum(1 for s in scores if s >= 78.0)
    above_omega = sum(1 for s in scores if s >= 95.0)
    return {
        "night": night_index,
        "n_branches": n,
        "aggregate_score": aggregate,
        "above_threshold_78": above_threshold,
        "pct_above_threshold": round(above_threshold / n * 100, 2) if n else 0.0,
        "above_omega_95": above_omega,
        "pct_above_omega": round(above_omega / n * 100, 2) if n else 0.0,
        "min_score": round(min(scores), 4) if scores else 0.0,
        "max_score": round(max(scores), 4) if scores else 0.0,
        "ts": datetime.now(timezone.utc).isoformat(),
    }


if __name__ == "__main__":
    import json, sys
    night = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    print(json.dumps(run_night(night), indent=2))
