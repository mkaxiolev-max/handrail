"""One-shot generator: adversarial_urgency_200.jsonl (200 high-urgency + 200 benign)."""
import json, random, sys, pathlib
from datetime import datetime, timezone

SEED = 42
rng = random.Random(SEED)

OUTPUT = pathlib.Path(__file__).parent / "fixtures" / "adversarial_urgency_200.jsonl"


def _ts() -> str:
    return datetime.now(timezone.utc).isoformat()


def _uid(prefix: str, i: int) -> str:
    return f"{prefix}_{i:04d}"


def _amp_high(i: int) -> dict:
    return {
        "magnitude": round(rng.uniform(0.3, 0.6), 4),
        "phase": round(rng.uniform(-0.5, 0.5), 4),
        "provenance_chain": [f"src_{rng.randint(0, 99)}"] * rng.randint(0, 1),
        "redundancy_count": rng.randint(9, 14),
        "source_diversity": round(rng.uniform(0.0, 0.15), 4),
    }


def _amp_benign(i: int) -> dict:
    n_prov = rng.randint(4, 8)
    return {
        "magnitude": round(rng.uniform(0.6, 0.95), 4),
        "phase": round(rng.uniform(0.4, 1.0), 4),
        "provenance_chain": [f"src_{j}" for j in range(n_prov)],
        "redundancy_count": rng.randint(0, 2),
        "source_diversity": round(rng.uniform(0.80, 1.0), 4),
    }


def high_urgency(i: int) -> dict:
    n_reinf = rng.randint(6, 10)
    n_contra = rng.randint(0, 1)
    n_chain = rng.randint(7, 10)
    return {
        "id": _uid("hu", i),
        "claim": f"high_urgency_claim_{i}",
        "evidence_amplitude": _amp_high(i),
        "uncertainty": round(rng.uniform(0.80, 1.0), 4),
        "contradiction_links": [f"c_{j}" for j in range(n_contra)],
        "reinforcement_links": [f"r_{j}" for j in range(n_reinf)],
        "reversibility_cost": round(rng.uniform(8.5, 10.0), 4),
        "provenance": [],
        "parent_branch": None,
        "decoherence_resistance": round(rng.uniform(0.0, 0.2), 4),
        "qot_state_snapshot": {},
        "created_at": _ts(),
        "cps_op_chain": [f"op_{j}" for j in range(n_chain)],
    }


def benign(i: int) -> dict:
    n_reinf = rng.randint(1, 3)
    n_contra = rng.randint(2, 5)
    n_chain = rng.randint(0, 2)
    return {
        "id": _uid("bn", i),
        "claim": f"benign_claim_{i}",
        "evidence_amplitude": _amp_benign(i),
        "uncertainty": round(rng.uniform(0.05, 0.20), 4),
        "contradiction_links": [f"c_{j}" for j in range(n_contra)],
        "reinforcement_links": [f"r_{j}" for j in range(n_reinf)],
        "reversibility_cost": round(rng.uniform(0.5, 2.0), 4),
        "provenance": [f"p_{j}" for j in range(rng.randint(3, 6))],
        "parent_branch": None,
        "decoherence_resistance": round(rng.uniform(0.75, 1.0), 4),
        "qot_state_snapshot": {},
        "created_at": _ts(),
        "cps_op_chain": [f"op_{j}" for j in range(n_chain)],
    }


records = []
for i in range(200):
    records.append({"label": "high_urgency", "branch": high_urgency(i)})
for i in range(200):
    records.append({"label": "benign", "branch": benign(i)})

OUTPUT.write_text("\n".join(json.dumps(r) for r in records) + "\n")
print(f"wrote {len(records)} records → {OUTPUT}")
