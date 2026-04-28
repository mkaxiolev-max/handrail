"""7-night trajectory runner — executes rubric harness N times against the frozen corpus."""
from __future__ import annotations
import json
from pathlib import Path
from services.coherence_kernel.harness.run_rubric import run_night
from services.coherence_kernel.harness.corpus import CORPUS_PATH

_TRAJECTORY_PATH = Path(__file__).parent / "synthetic_corpus" / "trajectory.jsonl"


def run_trajectory(
    n_nights: int = 7,
    corpus_path: Path = CORPUS_PATH,
    db_path: Path | None = None,
    output_path: Path = _TRAJECTORY_PATH,
) -> list[dict]:
    """Run n_nights nightly reports against the frozen corpus; append to trajectory JSONL."""
    reports = []
    for night in range(n_nights):
        report = run_night(night, corpus_path=corpus_path, db_path=db_path)
        reports.append(report)

    with output_path.open("a") as f:
        for r in reports:
            f.write(json.dumps(r) + "\n")

    return reports


def load_trajectory(path: Path = _TRAJECTORY_PATH) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
