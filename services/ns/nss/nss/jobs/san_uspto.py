"""
SAN USPTO Terrain (v0 - boot safe)

Goal right now:
- NS must boot deterministically.
- Keep /san/hello, /san/terrain, /san/status working.
- Remove PatentsView dependency entirely (can add later).

This module provides the symbols imported by nss/api/server.py:
- TerrainMode, TerrainConfig
- get_san_engine, get_active_run, get_last_progress
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any


class TerrainMode(str, Enum):
    HELLO = "hello"
    TERRAIN = "terrain"


@dataclass
class TerrainConfig:
    mode: TerrainMode = TerrainMode.TERRAIN
    cpc_codes: List[str] = field(default_factory=list)
    gb_cap: float = 0.2


@dataclass
class TerrainSnapshot:
    snapshot_id: str
    mode: str
    cpc_codes: List[str]
    patent_count: int = 0
    claim_count: int = 0
    citation_count: int = 0
    bytes_downloaded: int = 0
    created_at: str = ""
    sha_manifest: Dict[str, str] = field(default_factory=dict)


class TerrainStore:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.snapshots_dir = base_dir / "snapshots"
        self.patents_dir = base_dir / "patents"
        self.claims_dir = base_dir / "claims"
        self.edges_dir = base_dir / "edges"
        self.raw_dir = base_dir / "raw"
        self.index_path = base_dir / "_terrain_index.json"
        self.text_index_path = base_dir / "_text_index.json"
        self._ensure_dirs()

    def _ensure_dirs(self) -> None:
        for p in [self.base_dir, self.snapshots_dir, self.patents_dir, self.claims_dir, self.edges_dir, self.raw_dir]:
            p.mkdir(parents=True, exist_ok=True)
        if not self.index_path.exists():
            self.index_path.write_text(json.dumps({"patents": {}, "snapshots": [], "stats": {}}, indent=2))
        if not self.text_index_path.exists():
            self.text_index_path.write_text("{}")

    def _load_index(self) -> Dict[str, Any]:
        try:
            return json.loads(self.index_path.read_text())
        except Exception:
            return {"patents": {}, "snapshots": [], "stats": {}}

    def _save_index(self, idx: Dict[str, Any]) -> None:
        self.index_path.write_text(json.dumps(idx, indent=2))

    def save_snapshot(self, snap: TerrainSnapshot) -> None:
        path = self.snapshots_dir / f"{snap.snapshot_id}.json"
        path.write_text(json.dumps(snap.__dict__, indent=2))

        idx = self._load_index()
        idx.setdefault("snapshots", []).append(
            {"id": snap.snapshot_id, "mode": snap.mode, "patents": snap.patent_count, "created_at": snap.created_at}
        )
        self._save_index(idx)

    def get_stats(self) -> Dict[str, Any]:
        # Back-compat for server.py
        return self.stats()

    def stats(self) -> Dict[str, Any]:
        snaps = list(self.snapshots_dir.glob("*.json"))
        return {
            "patents": len(list(self.patents_dir.glob("*.json"))),
            "claims": len(list(self.claims_dir.glob("*.json"))),
            "edges": len(list(self.edges_dir.glob("*.json"))),
            "snapshots": len(snaps),
            "terrain_dir": str(self.base_dir),
            "index_entries": 0,
        }


class SanEngine:
    def __init__(self, config: TerrainConfig, receipt_chain=None):
        self.config = config
        self.receipt_chain = receipt_chain
        base_dir = Path("/Volumes/NSExternal/ALEXANDRIA/san_terrain")
        self.store = TerrainStore(base_dir)
        self._active: bool = False
        self._last_progress: List[dict] = []

    def _progress(self, phase: str, message: str, mode: Optional[str] = None, **extra: Any) -> None:
        ev = {"phase": phase, "message": message}
        if mode:
            ev["mode"] = mode
        ev.update(extra)
        self._last_progress.append(ev)
        self._last_progress = self._last_progress[-200:]

    def hello(self) -> Dict[str, Any]:
        self._progress("init", "Starting terrain init — mode: hello", mode="hello")
        self._progress("hello", "USPTO mode active (PatentsView disabled).", mode="hello")
        res = {
            "mode": "hello",
            "steps": [
                {"step": "uspto_mode", "status": "ok", "note": "PatentsView disabled; USPTO-only scaffold"},
                {"step": "store_health", "status": "ok", "stats": self.store.stats()},
            ],
            "terrain_ready": True,
            "stats": self.store.stats(),
            "bytes_used": 0,
            "message": "SAN terrain pipeline (USPTO-only) is wired. Implement ingest later.",
        }
        self._progress("complete", "Hello complete", mode="hello", results=res)
        return {"result": res, "progress": list(self._last_progress)}

    def run_terrain(self, cpc_codes: List[str], gb_cap: float) -> Dict[str, Any]:
        self._active = True
        self._last_progress = []
        self._progress("init", "Starting terrain run (USPTO-only scaffold)", mode="terrain", cpc_codes=cpc_codes, gb_cap=gb_cap)

        snap = TerrainSnapshot(
            snapshot_id=f"snap_{int(time.time())}",
            mode="terrain",
            cpc_codes=list(cpc_codes),
            created_at=time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        )
        self.store.save_snapshot(snap)
        self._progress("complete", "Terrain snapshot written (no ingest yet)", mode="terrain", snapshot_id=snap.snapshot_id)

        self._active = False
        return {
            "ok": True,
            "mode": "terrain",
            "snapshot_id": snap.snapshot_id,
            "downloaded": [],
            "bytes_downloaded": 0,
            "stats": self.store.stats(),
        }


_ENGINE: Optional[SanEngine] = None


def get_san_engine(config: TerrainConfig = None, receipt_chain=None) -> SanEngine:
    global _ENGINE
    _ENGINE = SanEngine(config or TerrainConfig(), receipt_chain=receipt_chain)
    return _ENGINE


def get_active_run() -> bool:
    return bool(_ENGINE and _ENGINE._active)


def get_last_progress() -> List[dict]:
    return list(_ENGINE._last_progress) if _ENGINE else []
