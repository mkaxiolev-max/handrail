"""Alexandrian Archive (L7 Memory Layer) integration.

Canonical alias: ``alexandrian_archive``
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

_SSD_ROOT = Path("/Volumes/NSExternal/ALEXANDRIA")
_FALLBACK_ROOT = Path.home() / "ALEXANDRIA"

_LAYOUT_DIRS = [
    "branches",
    "projections",
    "canon",
    "ledger",
    "lexicon",
    "state/transitions",
    "narrative",
]


def _resolve_root(override: Optional[Path]) -> Path:
    if override is not None:
        return Path(override)
    if _SSD_ROOT.exists():
        return _SSD_ROOT
    return _FALLBACK_ROOT


def _append_jsonl(path: Path, record: dict) -> None:
    with open(path, "a") as fh:
        fh.write(json.dumps(record) + "\n")
        fh.flush()
        os.fsync(fh.fileno())


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    records: list[dict] = []
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


class AlexandrianArchive:
    """Manage the Alexandrian Archive filesystem layout (L7 Memory Layer).

    Provides access to all sub-layers:
      L5  Alexandrian Lexicon — baptisms / supersessions
      L6  State Manifold     — shard deltas / manifests
      L7  Alexandrian Archive — branches / projections / canon
      L8  Lineage Fabric     — ledger/ns_events.jsonl (append-only, I2)
    """

    def __init__(self, root: Optional[Path] = None) -> None:
        self.root = _resolve_root(root)
        self._ensure_layout()

    def _ensure_layout(self) -> None:
        for sub in _LAYOUT_DIRS:
            (self.root / sub).mkdir(parents=True, exist_ok=True)

    # --- Branches (L7) ---

    def write_branch(self, branch_id: str, data: dict) -> Path:
        path = self.root / "branches" / f"{branch_id}.json"
        path.write_text(json.dumps(data))
        return path

    def read_branch(self, branch_id: str) -> dict:
        path = self.root / "branches" / f"{branch_id}.json"
        return json.loads(path.read_text())

    # --- Projections (L7) ---

    def write_projection(self, projection_id: str, data: dict) -> Path:
        path = self.root / "projections" / f"{projection_id}.json"
        path.write_text(json.dumps(data))
        return path

    def read_projection(self, projection_id: str) -> dict:
        path = self.root / "projections" / f"{projection_id}.json"
        return json.loads(path.read_text())

    # --- Lineage Fabric (L8) — append-only ledger (I2) ---

    def append_lineage_event(self, event: dict) -> None:
        _append_jsonl(self.root / "ledger" / "ns_events.jsonl", event)

    def read_lineage(self) -> list[dict]:
        return _read_jsonl(self.root / "ledger" / "ns_events.jsonl")

    # --- Alexandrian Lexicon (L5) — baptisms / supersessions (I10) ---

    def baptize(self, term: str, meaning: str, provenance: str) -> None:
        _append_jsonl(
            self.root / "lexicon" / "baptisms.jsonl",
            {"term": term, "meaning": meaning, "provenance": provenance},
        )

    def supersede(self, old_term: str, new_term: str, reason: str) -> None:
        _append_jsonl(
            self.root / "lexicon" / "supersessions.jsonl",
            {"old_term": old_term, "new_term": new_term, "reason": reason},
        )

    def read_baptisms(self) -> list[dict]:
        return _read_jsonl(self.root / "lexicon" / "baptisms.jsonl")

    def read_supersessions(self) -> list[dict]:
        return _read_jsonl(self.root / "lexicon" / "supersessions.jsonl")

    # --- State Manifold (L6) — shard deltas (append-only) ---

    def append_state_delta(self, shard_id: str, delta: dict) -> None:
        shard_dir = self.root / "state" / "shards" / shard_id
        shard_dir.mkdir(parents=True, exist_ok=True)
        _append_jsonl(shard_dir / "deltas.jsonl", delta)

    def write_shard_manifest(self, shard_id: str, manifest: dict) -> None:
        shard_dir = self.root / "state" / "shards" / shard_id
        shard_dir.mkdir(parents=True, exist_ok=True)
        (shard_dir / "manifest.json").write_text(json.dumps(manifest))

    def read_state_deltas(self, shard_id: str) -> list[dict]:
        return _read_jsonl(
            self.root / "state" / "shards" / shard_id / "deltas.jsonl"
        )


# Canonical alias per locked ontology
alexandrian_archive = AlexandrianArchive
