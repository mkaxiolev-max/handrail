from __future__ import annotations
from collections import defaultdict
from pathlib import Path
from datetime import datetime, timezone
import orjson


class ContradictionLane:
    def __init__(self, edges_path: Path, jaccard_threshold: float = 0.85,
                 keep_window: int = 50_000):
        self.edges_path = edges_path
        self.edges_path.parent.mkdir(parents=True, exist_ok=True)
        self.jaccard_threshold = jaccard_threshold
        self.keep_window = keep_window
        self.id_seen: dict[str, str] = {}
        self.assignee_history: dict[str, list[str]] = defaultdict(list)
        self.claim_shingles: dict[str, set[str]] = {}
        self.fh = self.edges_path.open("ab")

    def check(self, obj) -> list[dict]:
        edges = []
        if obj.id in self.id_seen:
            edges.append({"kind": "duplicate_id", "a": obj.id, "b": obj.id, "weight": 1.0})
        for a in obj.assignees:
            self.assignee_history[obj.id].append(a)
            if len(self.assignee_history[obj.id]) > 1:
                prev = self.assignee_history[obj.id][-2]
                if prev != a:
                    edges.append({"kind": "assignee_shift", "id": obj.id,
                                  "from": prev, "to": a, "weight": 0.7})
        if obj.claims:
            shingles = self._shingle(" ".join(obj.claims[:3]))
            self.claim_shingles[obj.id] = shingles
            for other_id, other_sh in list(self.claim_shingles.items())[-self.keep_window:]:
                if other_id == obj.id or not other_sh or not shingles: continue
                inter = len(shingles & other_sh)
                if inter == 0: continue
                j = inter / len(shingles | other_sh)
                if j >= self.jaccard_threshold:
                    edges.append({"kind": "claim_overlap", "a": obj.id, "b": other_id,
                                  "jaccard": round(j, 4), "weight": j})
        self.id_seen[obj.id] = obj.raw_source_pointer
        for e in edges:
            e["ts"] = datetime.now(timezone.utc).isoformat()
            self.fh.write(orjson.dumps(e) + b"\n")
        if len(self.claim_shingles) > self.keep_window * 2:
            keep = list(self.claim_shingles.keys())[-self.keep_window:]
            self.claim_shingles = {k: self.claim_shingles[k] for k in keep}
        return edges

    @staticmethod
    def _shingle(text: str, n: int = 5) -> set[str]:
        toks = text.lower().split()
        return {" ".join(toks[i:i+n]) for i in range(len(toks)-n+1)} if len(toks) >= n else set()

    def close(self):
        self.fh.flush(); self.fh.close()
