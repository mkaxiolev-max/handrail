"""
axiolev-ug-registry-v2
AXIOLEV Holdings LLC © 2026

Registry adapter: Omega L10 primitive -> Entity specialization.
"""
from __future__ import annotations
from typing import Any

from .entity import Entity, EntityKind, Identity, Provenance, Epistemics


def branch_to_entity(b: Any) -> Entity:
    return Entity(
        id=b.id,
        kind=EntityKind.BRANCH,
        identity=Identity(canonical_name=b.title, aliases=[]),
        state={"canon_promoted": b.canon_promoted, "mode": str(b.mode), "parent_id": b.parent_id},
        provenance=Provenance(origin="omega.branch", chain=[b.parent_id] if b.parent_id else []),
    )


def delta_to_entity(d: Any) -> Entity:
    return Entity(
        id=d.id,
        kind=EntityKind.DELTA,
        identity=Identity(canonical_name=f"delta:{d.id}"),
        state={"payload_hash": d.payload_hash, "prev_hash": d.prev_hash, "payload": d.payload},
        provenance=Provenance(origin="omega.delta", chain=[d.branch_id]),
    )


def entanglement_to_entity(e: Any) -> Entity:
    return Entity(
        id=e.id,
        kind=EntityKind.ENTANGLEMENT,
        identity=Identity(canonical_name=f"entanglement:{e.relation}"),
        state={"strength": e.strength, "relation": e.relation},
        provenance=Provenance(origin="omega.entanglement", chain=list(e.branch_ids)),
    )


def contradiction_to_entity(c: Any) -> Entity:
    return Entity(
        id=c.id,
        kind=EntityKind.CONTRADICTION,
        identity=Identity(canonical_name=f"contradiction:{c.axis}"),
        state={"severity": c.severity, "resolved": c.resolved, "axis": c.axis},
        provenance=Provenance(origin="omega.contradiction", chain=list(c.branch_ids)),
    )


def anchor_to_entity(a: Any) -> Entity:
    return Entity(
        id=a.id,
        kind=EntityKind.SEMANTIC_ANCHOR,
        identity=Identity(canonical_name=a.concept),
        state={"embedding_ref": a.embedding_ref},
        provenance=Provenance(origin="omega.semantic_anchor", chain=[a.branch_id]),
    )


def shard_to_entity(s: Any) -> Entity:
    return Entity(
        id=s.id,
        kind=EntityKind.SHARD_MANIFEST,
        identity=Identity(canonical_name=f"shard:{s.checksum[:12]}"),
        state={"shards": s.shards, "checksum": s.checksum},
        provenance=Provenance(origin="omega.shard_manifest", chain=[s.branch_id]),
    )


def projection_result_to_entity(p: Any) -> Entity:
    return Entity(
        id=p.request_id,
        kind=EntityKind.PROJECTION,
        identity=Identity(canonical_name=f"projection:{p.mode}"),
        state={"recoverability": str(p.recoverability),
               "order_used": [str(o) for o in p.order_used],
               "payload": p.payload},
        provenance=Provenance(origin="omega.projection", chain=[p.branch_id]),
        epistemics=Epistemics(
            evidence=p.confidence.evidence,
            contradiction=p.confidence.contradiction,
            novelty=p.confidence.novelty,
            stability=p.confidence.stability,
        ),
    )
