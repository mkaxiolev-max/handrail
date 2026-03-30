"""
NS Canon Document Loader
Loads .md canon documents from the NSS base directory into Alexandria on boot.
Documents are stored as text files in Alexandria/canon/ and receipted.

Called once at server boot. Idempotent — skips docs already loaded by hash.
"""

import hashlib
import json
from pathlib import Path
from typing import List, Dict, Optional


# Canon documents to load at boot, in priority order
# NS_PRIMITIVES must load first — it is the foundation all others build on
CANON_MANIFEST = [
    ("CANON_NS_PRIMITIVES_v1.md",        "NS_PRIMITIVES",      "FOUNDER"),
    ("CANON_STABILIZATION_THEORY_v1.md", "STABILIZATION_STL",  "FOUNDER"),
    ("CANON_SAN_v1.md",                  "SAN_CANON",          "FOUNDER"),
    ("CANON_NS_OMEGA_v1.md",          "NS_OMEGA_CANON",     "FOUNDER"),
    ("CANON_ONTOLOGICAL_MAPPING_v1.md","ONTOLOGICAL_CANON", "FOUNDER"),
    ("AMENDMENT_CONCILIAR_v1.0.md",   "CONCILIAR_AMEND",   "FOUNDER"),
    ("SFE_ONTOLOGY_v1.yaml",          "SFE_ONTOLOGY",       "EXEC"),
    ("SFE_VERSIONING_RULES_v1.md",    "SFE_VERSIONING",     "EXEC"),
    ("VOICE_ARCHITECTURE_v1.md",      "VOICE_ARCH",         "EXEC"),
    ("VOICE_LANE_SPEC_v1.1.md",       "VOICE_LANE_SPEC",    "EXEC"),
    ("CALL_HUD_SPEC_v1.0.md",         "CALL_HUD_SPEC",      "EXEC"),
    ("ALEXANDRIA_V2_INTEGRATION.md",  "ALEXANDRIA_SPEC",    "EXEC"),
]


def _sha256(content: str) -> str:
    return "sha256:" + hashlib.sha256(content.encode("utf-8")).hexdigest()


def _get_canon_doc_dir() -> Path:
    """Returns Alexandria canon docs directory."""
    try:
        from nss.core.storage import ALEXANDRIA_ROOT
        d = ALEXANDRIA_ROOT / "canon_docs"
    except Exception:
        d = Path("/Volumes/NSExternal/ALEXANDRIA/canon_docs")
    d.mkdir(parents=True, exist_ok=True)
    return d


def _get_index_path(canon_doc_dir: Path) -> Path:
    return canon_doc_dir / "_index.json"


def _load_index(index_path: Path) -> Dict[str, str]:
    """Load hash index of already-ingested docs. key = doc_id, val = sha256."""
    if not index_path.exists():
        return {}
    try:
        return json.loads(index_path.read_text())
    except Exception:
        return {}


def _save_index(index_path: Path, index: Dict[str, str]) -> None:
    index_path.write_text(json.dumps(index, indent=2))


def ingest_canon_docs(
    base_dir: Path,
    receipt_chain=None,
) -> List[Dict]:
    """
    Ingest canon .md documents from base_dir into Alexandria.

    Args:
        base_dir:      Directory containing the .md canon files (NSS root)
        receipt_chain: Optional ReceiptChain to emit receipts for new ingests

    Returns:
        List of ingestion result dicts (one per processed doc)
    """
    canon_doc_dir = _get_canon_doc_dir()
    index_path = _get_index_path(canon_doc_dir)
    index = _load_index(index_path)

    results = []

    for filename, doc_id, min_tier in CANON_MANIFEST:
        src = base_dir / filename
        if not src.exists():
            results.append({
                "doc_id": doc_id,
                "filename": filename,
                "status": "missing",
            })
            continue

        content = src.read_text(encoding="utf-8")
        content_hash = _sha256(content)

        # Idempotent: skip if already ingested with same hash
        if index.get(doc_id) == content_hash:
            results.append({
                "doc_id": doc_id,
                "filename": filename,
                "status": "already_loaded",
                "hash": content_hash,
            })
            continue

        # Store to Alexandria canon_docs
        dest = canon_doc_dir / f"{doc_id}.md"
        dest.write_text(content, encoding="utf-8")

        # Update index
        index[doc_id] = content_hash
        _save_index(index_path, index)

        # Emit receipt
        if receipt_chain is not None:
            try:
                receipt_chain.emit(
                    event_type="CANON_DOC_LOADED",
                    source={"kind": "boot", "ref": "canon_loader"},
                    inputs={"filename": filename, "doc_id": doc_id},
                    outputs={"hash": content_hash, "min_tier": min_tier, "bytes": len(content)},
                )
            except Exception:
                pass

        results.append({
            "doc_id": doc_id,
            "filename": filename,
            "status": "ingested",
            "hash": content_hash,
            "min_tier": min_tier,
            "bytes": len(content),
        })

    return results


def get_canon_doc(doc_id: str, tier: str = "EXEC") -> Optional[str]:
    """
    Retrieve a canon document by doc_id.
    Returns None if the doc doesn't exist or if tier is insufficient.
    
    Tier hierarchy: FOUNDER > EXEC > SAN > USER
    """
    TIER_RANK = {"FOUNDER": 4, "EXEC": 3, "SAN": 2, "USER": 1}

    # Get minimum tier required for this doc from manifest
    doc_min_tier = "EXEC"  # default
    for filename, mid, min_tier in CANON_MANIFEST:
        if mid == doc_id:
            doc_min_tier = min_tier
            break

    if TIER_RANK.get(tier, 0) < TIER_RANK.get(doc_min_tier, 4):
        return None  # Tier insufficient

    canon_doc_dir = _get_canon_doc_dir()
    dest = canon_doc_dir / f"{doc_id}.md"
    if dest.exists():
        return dest.read_text(encoding="utf-8")
    return None


def get_ns_primitives() -> Optional[str]:
    """
    Retrieve NS Primitives canon directly.
    This is the foundational doc — called during boot validation.
    """
    base_dir = Path(__file__).parent.parent.parent  # NSS root
    src = base_dir / "CANON_NS_PRIMITIVES_v1.md"
    if src.exists():
        return src.read_text(encoding="utf-8")
    return get_canon_doc("NS_PRIMITIVES", tier="FOUNDER")


def summarize_ingest(results: List[Dict]) -> str:
    """Return a human-readable boot summary line."""
    total = len(results)
    ingested = sum(1 for r in results if r["status"] == "ingested")
    already = sum(1 for r in results if r["status"] == "already_loaded")
    missing = sum(1 for r in results if r["status"] == "missing")
    
    parts = [f"Canon docs: {total} manifest"]
    if ingested:
        parts.append(f"{ingested} ingested")
    if already:
        parts.append(f"{already} current")
    if missing:
        parts.append(f"{missing} missing")
    return " | ".join(parts)
