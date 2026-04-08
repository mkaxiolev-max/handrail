from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import os, psycopg2, datetime, sys

# Allow import from orchestration package
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

router = APIRouter(prefix="/feed", tags=["feed"])

DB_URL = os.environ.get("DATABASE_URL", "postgresql://ns:ns_secure_pwd@postgres:5432/ns")


def _conn():
    return psycopg2.connect(DB_URL)


def _ensure_table():
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS feed_events (
                    id SERIAL PRIMARY KEY,
                    kind TEXT NOT NULL,
                    payload JSONB,
                    source TEXT,
                    ts TIMESTAMPTZ DEFAULT NOW()
                )
            """)
        conn.commit()


class FeedEvent(BaseModel):
    kind: str
    payload: Optional[dict] = None
    source: Optional[str] = None


@router.on_event("startup")
async def startup():
    try:
        _ensure_table()
    except Exception:
        pass


@router.post("/")
async def push_event(event: FeedEvent):
    import json
    try:
        with _conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO feed_events (kind, payload, source) VALUES (%s,%s,%s) RETURNING id",
                    (event.kind, json.dumps(event.payload), event.source)
                )
                row = cur.fetchone()
            conn.commit()
        return {"status": "ok", "id": row[0]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
@router.get("")
async def get_feed(limit: int = 50):
    """Return feed_items (generated cards) for the UI timeline."""
    try:
        with _conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, type, payload, created_at FROM feed_items ORDER BY created_at DESC LIMIT %s",
                    (limit,)
                )
                rows = cur.fetchall()
        items = [
            {
                "id": str(r[0]),
                "type": r[1],
                "label": (r[2] or {}).get("label", r[1]) if isinstance(r[2], dict) else r[1],
                "payload": r[2],
                "ts": str(r[3]),
            }
            for r in rows
        ]
        return {"events": items, "items": items}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/build")
async def build_feed():
    """
    Generate feed cards from live system state and insert to feed_items.
    Writes a feed_generated receipt to the chain.
    """
    try:
        from orchestration.feed_builder import build_feed as _build
        result = _build()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
