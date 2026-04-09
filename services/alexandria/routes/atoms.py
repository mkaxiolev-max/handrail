from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import os, psycopg2
from graph.atom_factory import extract_atoms_from_text, detect_founder_arcs

router = APIRouter(prefix="/atoms", tags=["atoms"])
DB_URL = os.environ.get("DATABASE_URL", "postgresql://ns:ns_secure_pwd@postgres:5432/ns")

def _conn():
    return psycopg2.connect(DB_URL)

class Atom(BaseModel):
    type: str
    content: str
    source_id: Optional[str] = None

@router.post("/")
async def create_atom(atom: Atom):
    try:
        with _conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO atoms (type, content, source_id) VALUES (%s,%s,%s::uuid) RETURNING id",
                    (atom.type, atom.content, atom.source_id)
                )
                row = cur.fetchone()
            conn.commit()
        return {"status": "ok", "id": str(row[0])}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/")
@router.get("")
async def list_atoms(limit: int = 100, offset: int = 0):
    try:
        with _conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, type, content, source_id, created_at FROM atoms ORDER BY created_at DESC LIMIT %s OFFSET %s",
                    (limit, offset)
                )
                rows = cur.fetchall()
        return {"atoms": [
            {
                "id": str(r[0]),
                "type": r[1],
                "label": (r[2][:80] if r[2] else None) or r[1],
                "content": r[2],
                "source_id": str(r[3]) if r[3] else None,
                "created_at": str(r[4]),
            }
            for r in rows
        ]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/build")
async def build_atoms():
    """Read all parse_bundles, extract atoms, insert to DB."""
    try:
        conn = _conn()
        cur = conn.cursor()
        cur.execute(
            "SELECT id, source_item_id, text_content FROM parse_bundles "
            "WHERE text_content IS NOT NULL AND text_content != ''"
        )
        bundles = cur.fetchall()
        all_atoms = []
        for bundle in bundles:
            atoms = extract_atoms_from_text(
                bundle[2],
                source_item_id=str(bundle[1]) if bundle[1] else None,
                bundle_id=str(bundle[0]),
            )
            all_atoms.extend(atoms)
        arc_atoms = detect_founder_arcs(all_atoms)
        all_atoms.extend(arc_atoms)
        inserted = 0
        for atom in all_atoms:
            cur.execute(
                "INSERT INTO atoms (id, type, content, source_id) VALUES (%s,%s,%s,%s) ON CONFLICT DO NOTHING",
                (atom.id, atom.type, atom.content, atom.source_id)
            )
            inserted += 1
        conn.commit()
        cur.close()
        conn.close()
        type_counts: dict = {}
        for a in all_atoms:
            type_counts[a.type] = type_counts.get(a.type, 0) + 1
        return {"status": "ok", "bundles_processed": len(bundles), "atoms_created": inserted,
                "type_breakdown": type_counts, "arcs_detected": len(arc_atoms)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class IngestTextIn(BaseModel):
    text: str
    source_item_id: Optional[str] = None
    bundle_id: Optional[str] = None


@router.post("/ingest-text")
async def ingest_text(payload: IngestTextIn):
    """Extract atoms from raw text — for testing without parse_bundles."""
    try:
        conn = _conn()
        cur = conn.cursor()
        atoms = extract_atoms_from_text(payload.text, payload.source_item_id, payload.bundle_id)
        arc_atoms = detect_founder_arcs(atoms)
        atoms.extend(arc_atoms)
        inserted = 0
        for atom in atoms:
            cur.execute(
                "INSERT INTO atoms (id, type, content, source_id) VALUES (%s,%s,%s,%s) ON CONFLICT DO NOTHING",
                (atom.id, atom.type, atom.content, atom.source_id)
            )
            inserted += 1
        conn.commit()
        cur.close()
        conn.close()
        type_counts: dict = {}
        for a in atoms:
            type_counts[a.type] = type_counts.get(a.type, 0) + 1
        return {"status": "ok", "atoms_created": inserted, "type_breakdown": type_counts,
                "arcs_detected": len(arc_atoms), "atoms": [a.to_dict() for a in atoms]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def list_atoms_full(limit: int = 100, offset: int = 0):
    try:
        conn = _conn()
        cur = conn.cursor()
        cur.execute(
            "SELECT id, type, content, source_id, created_at FROM atoms ORDER BY created_at DESC LIMIT %s OFFSET %s",
            (limit, offset)
        )
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return {"atoms": [{"id": str(r[0]), "type": r[1], "content": r[2],
                           "source_id": str(r[3]) if r[3] else None, "created_at": str(r[4])}
                          for r in rows], "count": len(rows)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/healthz")
async def health():
    return {"status": "ok"}
