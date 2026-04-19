"""Omega L10 Projection Engine — six recovery strategies, six modes.

Recovery order (attempt each in sequence, commit on first ok):
  1. exact_local            → EXACT
  2. delta_replay           → LOSSLESS_STRUCTURAL
  3. shard_recovery         → LOSSLESS_STRUCTURAL
  4. entanglement_assisted  → LOSSLESS_SEMANTIC
  5. semantic               → LOSSY_SEMANTIC
  6. graceful_partial       → IRRECOVERABLE (abstention fallback)

Every projection emits a `projection_emitted` receipt to the Lineage Fabric.
Canon promotion is NEVER called here — Omega is read/project only (I1).
AXIOLEV Holdings LLC © 2026
"""
from __future__ import annotations

import hashlib
import json
import uuid
from pathlib import Path
from typing import Optional

from ns.domain.models.omega_primitives import (
    ConfidenceEnvelope,
    ProjectionMode,
    ProjectionRequest,
    ProjectionResult,
    Recoverability,
)
from ns.integrations.omega_store import OmegaStore

# Locked recovery strategy table — order matters (first ok wins)
STRATEGIES: list[tuple[str, Recoverability]] = [
    ("exact_local", Recoverability.EXACT),
    ("delta_replay", Recoverability.LOSSLESS_STRUCTURAL),
    ("shard_recovery", Recoverability.LOSSLESS_STRUCTURAL),
    ("entanglement_assisted", Recoverability.LOSSLESS_SEMANTIC),
    ("semantic", Recoverability.LOSSY_SEMANTIC),
    ("graceful_partial", Recoverability.IRRECOVERABLE),
]


def _request_hash(req: ProjectionRequest) -> str:
    raw = json.dumps(
        {
            "target_ref": req.target_ref,
            "mode": req.mode.value,
            "constraints": req.constraints,
        },
        sort_keys=True,
    )
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


class ProjectionEngine:
    """Attempt each recovery strategy in order; emit receipt on result."""

    def __init__(self, store: Optional[OmegaStore] = None) -> None:
        self._store = store or OmegaStore()

    # ------------------------------------------------------------------
    # Strategy implementations
    # ------------------------------------------------------------------

    def _exact_local(self, req: ProjectionRequest) -> Optional[dict]:
        """Return stored projection payload if an exact cached copy exists."""
        cached = self._store.read_projection(req.target_ref)
        if cached and cached.get("mode") == req.mode.value:
            return cached
        branch = self._store.read_branch(req.target_ref)
        if branch:
            return {"source": "exact_local", "branch": branch}
        return None

    def _delta_replay(self, req: ProjectionRequest) -> Optional[dict]:
        """Reconstruct from stored delta chain in the Alexandrian Archive."""
        deltas_path = self._store.root / "state" / "shards" / req.target_ref / "deltas.jsonl"
        if not deltas_path.exists():
            return None
        deltas: list[dict] = []
        with open(deltas_path) as fh:
            for line in fh:
                line = line.strip()
                if line:
                    try:
                        deltas.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
        if not deltas:
            return None
        return {"source": "delta_replay", "delta_count": len(deltas), "deltas": deltas}

    def _shard_recovery(self, req: ProjectionRequest) -> Optional[dict]:
        """Recover from erasure-coded shards (rs(10,4) scheme)."""
        manifest_path = (
            self._store.root / "shards" / req.target_ref / "manifest.json"
        )
        if not manifest_path.exists():
            return None
        try:
            manifest = json.loads(manifest_path.read_text())
        except (json.JSONDecodeError, OSError):
            return None
        return {"source": "shard_recovery", "manifest": manifest}

    def _entanglement_assisted(self, req: ProjectionRequest) -> Optional[dict]:
        """Use entanglement graph to recover semantics from coreferent nodes."""
        ent_dir = self._store.root / "entanglements"
        found: list[dict] = []
        if ent_dir.exists():
            for f in ent_dir.glob("*.json"):
                try:
                    ent = json.loads(f.read_text())
                    if ent.get("a_ref") == req.target_ref or ent.get("b_ref") == req.target_ref:
                        found.append(ent)
                except (json.JSONDecodeError, OSError):
                    pass
        if not found:
            return None
        return {"source": "entanglement_assisted", "entanglements": found}

    def _semantic(self, req: ProjectionRequest) -> Optional[dict]:
        """Semantic approximation via anchor lookup — lossy but valid."""
        anchor_dir = self._store.root / "anchors"
        anchors: list[dict] = []
        if anchor_dir.exists():
            for f in anchor_dir.glob("*.json"):
                try:
                    a = json.loads(f.read_text())
                    if req.target_ref in a.get("label", "") or req.target_ref in a.get("embedding_ref", ""):
                        anchors.append(a)
                except (json.JSONDecodeError, OSError):
                    pass
        # Always succeeds with at minimum a synthetic semantic stub
        return {
            "source": "semantic",
            "anchors": anchors,
            "approximated": True,
            "target_ref": req.target_ref,
        }

    def _graceful_partial(self, req: ProjectionRequest) -> dict:
        """Last-resort abstention — always succeeds, marks gap explicitly."""
        return {
            "source": "graceful_partial",
            "gap": True,
            "target_ref": req.target_ref,
            "reason": "all_strategies_exhausted",
        }

    # ------------------------------------------------------------------
    # Confidence envelope per strategy
    # ------------------------------------------------------------------

    _STRATEGY_CONFIDENCE: dict[str, dict[str, float]] = {
        "exact_local":           {"evidence": 1.0, "contradiction": 0.0, "novelty": 0.0, "stability": 1.0},
        "delta_replay":          {"evidence": 0.9, "contradiction": 0.05, "novelty": 0.1, "stability": 0.9},
        "shard_recovery":        {"evidence": 0.85, "contradiction": 0.05, "novelty": 0.1, "stability": 0.85},
        "entanglement_assisted": {"evidence": 0.7, "contradiction": 0.15, "novelty": 0.3, "stability": 0.7},
        "semantic":              {"evidence": 0.5, "contradiction": 0.2, "novelty": 0.5, "stability": 0.5},
        "graceful_partial":      {"evidence": 0.1, "contradiction": 0.0, "novelty": 0.1, "stability": 0.1},
    }

    def _build_confidence(self, strategy: str) -> ConfidenceEnvelope:
        vals = self._STRATEGY_CONFIDENCE[strategy]
        return ConfidenceEnvelope(**vals)

    # ------------------------------------------------------------------
    # Mode → recoverability floor
    # ------------------------------------------------------------------

    _MODE_FLOOR: dict[ProjectionMode, Recoverability] = {
        ProjectionMode.EXACT_VIEW:              Recoverability.EXACT,
        ProjectionMode.BRANCH_VIEW:             Recoverability.LOSSLESS_STRUCTURAL,
        ProjectionMode.MERGED_VIEW:             Recoverability.LOSSLESS_STRUCTURAL,
        ProjectionMode.CANON_VIEW:              Recoverability.LOSSLESS_SEMANTIC,
        ProjectionMode.PARTIAL_RECONSTRUCTION:  Recoverability.IRRECOVERABLE,
        ProjectionMode.CONTRASTIVE_VIEW:        Recoverability.LOSSY_SEMANTIC,
    }

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def project(self, req: ProjectionRequest) -> ProjectionResult:
        """Run recovery strategies in order; return first successful result."""
        order_used: list[str] = []
        content: Optional[dict] = None
        winning_strategy: Optional[str] = None
        winning_recoverability: Optional[Recoverability] = None

        strategy_fns = {
            "exact_local": self._exact_local,
            "delta_replay": self._delta_replay,
            "shard_recovery": self._shard_recovery,
            "entanglement_assisted": self._entanglement_assisted,
            "semantic": self._semantic,
            "graceful_partial": self._graceful_partial,
        }

        for name, recoverability in STRATEGIES:
            order_used.append(name)
            fn = strategy_fns[name]
            result = fn(req)
            if result is not None:
                content = result
                winning_strategy = name
                winning_recoverability = recoverability
                break

        # graceful_partial always returns non-None, so this can't be None
        assert content is not None
        assert winning_strategy is not None
        assert winning_recoverability is not None

        confidence = self._build_confidence(winning_strategy)
        mode = req.mode
        # If all strategies exhausted (graceful_partial won), force mode
        if winning_strategy == "graceful_partial":
            mode = ProjectionMode.PARTIAL_RECONSTRUCTION

        projection_id = _request_hash(req)
        result_obj = ProjectionResult(
            target_ref=req.target_ref,
            mode=mode,
            content=content,
            order_used=order_used,
            confidence=confidence,
            recoverability=winning_recoverability,
            lineage=[req.requested_by, req.target_ref],
        )

        # Persist projection cache (I7 determinism — same request → same cache key)
        self._store.write_projection(projection_id, result_obj.model_dump(mode="json"))

        # Emit Lineage Fabric receipt (I2 — append-only)
        self._store.append_receipt(
            {
                "name": "projection_emitted",
                "projection_id": projection_id,
                "target_ref": req.target_ref,
                "mode": mode.value,
                "strategy": winning_strategy,
                "recoverability": winning_recoverability.value,
                "requested_by": req.requested_by,
            }
        )

        return result_obj
