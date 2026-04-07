from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import os, psycopg2
from graph.edge_builder import build_edges_from_atoms

router = APIRouter(prefix="/graph", tags=["graph"])
DB_URL = os.environ.get("DATABASE_URL", "postgresql://ns:ns_secure_pwd@postgres:5432/ns")

def _conn():
    return psycopg2.connect(DB_URL)

def _count_types(items: list) -> dict:
    counts: dict = {}
    for item in items:
        counts[item.get("type", "unknown")] = counts.get(item.get("type", "unknown"), 0) + 1
    return counts

class Edge(BaseModel):
    from_id: str
    to_id: str
    type: str

@router.post("/edge")
async def add_edge(edge: Edge):
    try:
        with _conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO edges (from_id, to_id, type) VALUES (%s::uuid,%s::uuid,%s) RETURNING id",
                    (edge.from_id, edge.to_id, edge.type)
                )
                row = cur.fetchone()
            conn.commit()
        return {"status": "ok", "id": str(row[0])}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/edges")
async def list_edges(limit: int = 100):
    try:
        with _conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, from_id, to_id, type, created_at FROM edges ORDER BY created_at DESC LIMIT %s",
                    (limit,)
                )
                rows = cur.fetchall()
        return {"edges": [{"id": str(r[0]), "from": str(r[1]), "to": str(r[2]), "type": r[3], "created_at": str(r[4])} for r in rows]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/neighbors/{node_id}")
async def neighbors(node_id: str):
    try:
        with _conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT to_id, type FROM edges WHERE from_id=%s::uuid UNION SELECT from_id, type FROM edges WHERE to_id=%s::uuid",
                    (node_id, node_id)
                )
                rows = cur.fetchall()
        return {"node_id": node_id, "neighbors": [{"id": str(r[0]), "type": r[1]} for r in rows]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/build")
async def build_graph():
    """Compute pairwise atom similarity, insert edges."""
    try:
        conn = _conn()
        result = build_edges_from_atoms(conn)
        conn.close()
        return {"status": "ok", **result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("")
async def get_graph(limit: int = 200):
    """Return all nodes + edges as graph JSON."""
    try:
        conn = _conn()
        cur = conn.cursor()
        cur.execute(
            "SELECT id, type, content, source_id, created_at FROM atoms ORDER BY created_at DESC LIMIT %s",
            (limit,)
        )
        nodes = [{"id": str(r[0]), "type": r[1], "content": r[2],
                  "source_id": str(r[3]) if r[3] else None, "created_at": str(r[4])}
                 for r in cur.fetchall()]
        cur.execute(
            "SELECT id, from_id, to_id, type, created_at FROM edges ORDER BY created_at DESC LIMIT %s",
            (limit * 3,)
        )
        edges = [{"id": str(r[0]), "from_id": str(r[1]), "to_id": str(r[2]),
                  "type": r[3], "created_at": str(r[4])}
                 for r in cur.fetchall()]
        cur.close()
        conn.close()
        arcs = [n for n in nodes if n["type"] == "arc"]
        return {"nodes": nodes, "edges": edges, "summary": {
            "node_count": len(nodes), "edge_count": len(edges), "arc_count": len(arcs),
            "type_breakdown": _count_types(nodes), "edge_type_breakdown": _count_types(edges),
        }}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/arcs")
async def get_arcs():
    """Return founder arc atoms only."""
    try:
        conn = _conn()
        cur = conn.cursor()
        cur.execute("SELECT id, type, content, source_id, created_at FROM atoms WHERE type='arc' ORDER BY created_at DESC")
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return {"arcs": [{"id": str(r[0]), "type": r[1], "content": r[2],
                           "source_id": str(r[3]) if r[3] else None, "created_at": str(r[4])}
                          for r in rows], "count": len(rows)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/healthz")
async def health():
    return {"status": "ok"}
