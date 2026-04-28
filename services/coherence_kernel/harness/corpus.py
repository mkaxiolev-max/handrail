"""Load and validate the frozen synthetic corpus."""
from __future__ import annotations
import json
from pathlib import Path
from services.coherence_kernel import schemas

CORPUS_PATH = Path(__file__).parent / "synthetic_corpus" / "corpus_seed_42.jsonl"


def load_corpus(path: Path = CORPUS_PATH) -> list[schemas.BranchState]:
    branches = []
    for line in path.read_text().splitlines():
        if line.strip():
            branches.append(schemas.BranchState(**json.loads(line)))
    return branches
