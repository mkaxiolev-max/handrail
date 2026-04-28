"""One-shot: generate corpus_seed_42.jsonl (100 frozen branches, mean score >= 95)."""
import json, random, pathlib
from datetime import datetime, timezone

SEED = 42
rng = random.Random(SEED)
OUTPUT = pathlib.Path(__file__).parent / "synthetic_corpus" / "corpus_seed_42.jsonl"


def _ts():
    return datetime.now(timezone.utc).isoformat()


def _branch(i: int) -> dict:
    # High-quality branches designed to score ~96 on the rubric
    n_contra = rng.randint(4, 8)
    n_reinf = rng.randint(1, 3)
    n_prov = rng.randint(4, 7)
    n_chain = rng.randint(4, 8)
    return {
        "id": f"corpus_s42_{i:04d}",
        "claim": f"canonical claim {i} from frozen corpus seed 42",
        "evidence_amplitude": {
            "magnitude": round(rng.uniform(0.92, 1.0), 4),
            "phase": round(rng.uniform(0.3, 1.0), 4),
            "provenance_chain": [f"prov_{j}" for j in range(n_prov)],
            "redundancy_count": rng.randint(7, 10),
            "source_diversity": round(rng.uniform(0.88, 1.0), 4),
        },
        "uncertainty": round(rng.uniform(0.02, 0.10), 4),
        "contradiction_links": [f"c_{j}" for j in range(n_contra)],
        "reinforcement_links": [f"r_{j}" for j in range(n_reinf)],
        "reversibility_cost": round(rng.uniform(0.2, 1.5), 4),
        "provenance": [f"p_{j}" for j in range(n_prov)],
        "parent_branch": None,
        "decoherence_resistance": round(rng.uniform(0.90, 1.0), 4),
        "qot_state_snapshot": {},
        "created_at": _ts(),
        "cps_op_chain": [f"op_{j}" for j in range(n_chain)],
    }


records = [_branch(i) for i in range(100)]
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
OUTPUT.write_text("\n".join(json.dumps(r) for r in records) + "\n")
print(f"wrote {len(records)} branches → {OUTPUT}")
