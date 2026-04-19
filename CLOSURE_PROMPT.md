# NS∞ CLOSURE MAX — Omega L10 + Media + UI Integration

**AXIOLEV Holdings LLC © 2026** — axiolevns <axiolevns@axiolev.com>
**Repo:** `mkaxiolev-max/handrail`, branch `boot-operational-closure`
**Package root:** `ns/` per ns_scaffold.zip — do NOT relocate.

## Prior state (do NOT rebuild)
The system is already at `ns-infinity-manifold-complete-v1.0.0` with:
- Rings 1–7 complete
- NCOM/PIIC merged (`ncom-piic-merged-v2`)
- RIL/ORACLE merged (`ril-oracle-merged-v2`)
- CQHML Manifold merged (`cqhml-manifold-merged-v2`)
- 717 tests passing

## Locked ontology (ENFORCE)
L1 Constitutional | L2 Gradient Field | L3 Epistemic Envelope |
L4 The Loom | L5 Alexandrian Lexicon | L6 State Manifold |
L7 Alexandrian Archive | L8 Lineage Fabric | L9 HIC/PDP |
L10 Narrative + Interface (Omega + Violet)

**Do NOT reintroduce deprecated names:** Ether, Lexicon alone,
Manifold alone, Alexandria alone, CTF, Storytime as layer.
"Storytime" is retained ONLY as a service module name.

## Invariants (must remain intact)
I1..I10 per MASTER PROMPT. In particular:
- I1 Canon precedes Conversion (Ring 4 gate)
- I4 Hardware quorum (YubiKey serial 26116460 mandatory)
- I2/I5/I10 Append-only, hash-chained, supersede-not-delete

---

# Z3 — Omega L10 Projection/Ego Layer

Omega is the **mouth of the system**. Everything the institution
says externally passes through Omega and is recovery-ordered,
confidence-enveloped, mode-indexed, and receipted.

## Z3.1 Pydantic v2 primitives

Create/extend `ns/domain/models/omega_primitives.py`:

```python
from __future__ import annotations
from datetime import datetime, timezone
from enum import Enum
from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, Field

def _now() -> datetime:
    return datetime.now(tz=timezone.utc)

class Recoverability(str, Enum):
    EXACT = "exact"
    LOSSLESS_STRUCTURAL = "lossless_structural"
    LOSSLESS_SEMANTIC = "lossless_semantic"
    LOSSY_SEMANTIC = "lossy_semantic"
    IRRECOVERABLE = "irrecoverable"

class ProjectionMode(str, Enum):
    EXACT_VIEW = "exact_view"
    BRANCH_VIEW = "branch_view"
    MERGED_VIEW = "merged_view"
    CANON_VIEW = "canon_view"
    PARTIAL_RECONSTRUCTION = "partial_reconstruction"
    CONTRASTIVE_VIEW = "contrastive_view"

class ConfidenceEnvelope(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    evidence: float = Field(ge=0.0, le=1.0)
    contradiction: float = Field(ge=0.0, le=1.0)
    novelty: float = Field(ge=0.0, le=1.0)
    stability: float = Field(ge=0.0, le=1.0)

    def score(self) -> float:
        # Locked constitutional weights — amendment requires
        # HIC + PDP + YubiKey quorum (see Ring 4).
        return (0.45 * self.evidence
                + 0.25 * (1.0 - self.contradiction)
                + 0.15 * self.novelty
                + 0.15 * self.stability)

class Branch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    parent_id: Optional[str] = None
    created_at: datetime = Field(default_factory=_now)
    title: str
    lineage: list[str] = Field(default_factory=list)
    canon: bool = False

class Delta(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    id: str
    branch_id: str
    seq: int = Field(ge=0)
    op: Literal["add","amend","retract","supersede"]
    payload: dict
    prev_hash: str
    hash: str
    author: str
    ts: datetime = Field(default_factory=_now)

class Entanglement(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    a_ref: str
    b_ref: str
    kind: Literal["coref","causal","contradiction_coupling","semantic_shadow"]
    weight: float = Field(ge=0.0, le=1.0)
    evidence: list[str] = Field(default_factory=list)

class Contradiction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    claim_a: str
    claim_b: str
    pressure: float = Field(ge=0.0, le=1.0)
    resolution: Literal["open","superseded","branch_split","accepted_paraconsistent"] = "open"
    resolution_ref: Optional[str] = None

class SemanticAnchor(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    label: str
    embedding_ref: str
    recoverability: Recoverability = Recoverability.LOSSLESS_SEMANTIC
    stability: float = Field(ge=0.0, le=1.0, default=1.0)

class ShardManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    shards: list[str]
    erasure_scheme: str = "rs(10,4)"
    merkle_root: str
    recoverability: Recoverability = Recoverability.LOSSLESS_STRUCTURAL

class ProjectionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    target_ref: str
    mode: ProjectionMode
    constraints: dict = Field(default_factory=dict)
    requested_by: str

class ProjectionResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    target_ref: str
    mode: ProjectionMode
    content: dict
    order_used: list[str]
    confidence: ConfidenceEnvelope
    recoverability: Recoverability
    lineage: list[str]
    ts: datetime = Field(default_factory=_now)

class ForkOp(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    from_branch: str
    to_branch: str
    reason: str
    authorizer: str
    pdp_decision_ref: str
    hic_approval_ref: Optional[str] = None
    ts: datetime = Field(default_factory=_now)

class MergeOp(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    branches: list[str]
    into: str
    policy: str
    authorizer: str
    pdp_decision_ref: str
    hic_approval_ref: str
    ts: datetime = Field(default_factory=_now)

class SupersessionOp(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    superseded_ref: str
    superseder_ref: str
    reason: str
    authorizer: str
    pdp_decision_ref: str
    hic_approval_ref: str
    ts: datetime = Field(default_factory=_now)

class Storytime(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    projection_ref: str
    narrative: str
    arc: list[str] = Field(default_factory=list)
    ts: datetime = Field(default_factory=_now)
```

## Z3.2 Alexandrian Archive layout (already mostly present)

Ensure these directories on `/Volumes/NSExternal/ALEXANDRIA/`:
```
branches/<branch_id>.json
projections/<projection_id>.json   (cache keyed by hash of request)
entanglements/<ent_id>.json
contradictions/<c_id>.json
anchors/<anchor_id>.json
shards/<shard_id>/{data,manifest.json}
storytime/<st_id>.json
ledger/ns_events.jsonl             (append-only, SHA-256 chained)
```

Storage adapter: `ns/integrations/omega_store.py` with:
- `read_json(subpath) -> dict | None`
- `write_json(subpath, obj) -> str` (returns sha256)
- `append_receipt(line: dict)` (fsync, flock, hash-chained)
- NEVER overwrites without an explicit supersede op.

## Z3.3 FastAPI routes

Add to `ns/api/routers/omega.py`:
- `POST /projections` → accepts `ProjectionRequest`, returns `ProjectionResult`
- `GET  /projections/{id}` → cached result
- `POST /storytime` → accepts `{projection_ref, narrative, arc}`,
  emits Storytime record + receipt `narrative_emitted_with_receipt_hash`
- `GET  /storytime/{id}`

Wire into `ns/api/server.py` lifespan.

## Z3.4 Projection engine — recovery order

`ns/services/omega/projection_engine.py`:

```python
STRATEGIES = [
    ("exact_local",            Recoverability.EXACT),
    ("delta_replay",           Recoverability.LOSSLESS_STRUCTURAL),
    ("shard_recovery",         Recoverability.LOSSLESS_STRUCTURAL),
    ("entanglement_assisted",  Recoverability.LOSSLESS_SEMANTIC),
    ("semantic",               Recoverability.LOSSY_SEMANTIC),
    ("graceful_partial",       Recoverability.IRRECOVERABLE),
]
```

Algorithm: attempt each strategy in order. On first `ok`, compute
the `ConfidenceEnvelope`, record `order_used`, return
`ProjectionResult`. If all fail, return `mode=PARTIAL_RECONSTRUCTION`
with `recoverability=IRRECOVERABLE` and explicit `gap` marker in
`content`.

Every projection writes a receipt named `projection_emitted` to
the Lineage Fabric.

## Z3.5 Canon promotion gate — already complete (Ring 4)

Do NOT reimplement. Verify that Omega's projection layer DOES NOT
bypass the existing `ns/services/canon/promotion_guard.py`. If
Omega ever writes to canon, it MUST call `promote(branch_id, ctx)`
which requires HIC + PDP + YubiKey quorum + ring6_phi_parallel.

## Z3.6 Tests

`ns/tests/test_omega_projection.py` — at minimum:
- 6 recovery strategies exercised (one test each)
- 6 projection modes return valid `ProjectionResult`
- ConfidenceEnvelope.score() with fixed inputs returns expected float
- `order_used` is recorded and non-empty
- Receipt `projection_emitted` lands in ledger
- Canon gate still refuses unauthorized promotion after Omega is live
- Abstention returns mode=PARTIAL_RECONSTRUCTION when all strategies fail

Target: ≥ 20 new tests. Must make `python3 -m pytest -x -q
ns/tests/test_omega_projection.py` GREEN.

---

# Z4 — Media engine integration

If `/mnt/user-data/uploads/media_engine_repo.zip` exists:
1. Unpack to `ns/services/media_engine/` (strip top-level dir if present).
2. Inspect for `router.py` / `service.py` / `schemas.py`.
3. Wire router into `ns/api/server.py` under `/media/*`.
4. Every media operation MUST call `pi/check` for admissibility
   and MUST route execution via Handrail (no direct fs/network).
5. Tests: `ns/tests/test_media_engine.py` — smoke + admissibility gate.

If zip absent: skip with receipt `media_engine_skipped_no_source`.

# Z5 — UI addition integration

If `/mnt/user-data/uploads/Ui_addition*` exists:
1. Read the spec.
2. Populate `ns/services/ui/{engine_room.py, living_architecture.py,
   runtime_panels.py, websocket_events.py}` additions only.
3. Every tile MUST fetch from real endpoints (no fabricated greens).
4. Tests: extend `ns/tests/test_ncom.py` (or add
   `ns/tests/test_ui_additions.py`) — projection-invariant tests.

If spec absent: skip with receipt `ui_addition_skipped_no_source`.

---

# Stop conditions

- Each phase: stop only when its pytest target is GREEN.
- Do NOT advance past a RED phase.
- Do NOT modify Rings 1–7, NCOM/PIIC, RIL/ORACLE, or CQHML code.
- Do NOT relax Canon gate thresholds or rewrite ontology names.
- Bash 3.2 only in shell scripts.
- All new files carry AXIOLEV header.
