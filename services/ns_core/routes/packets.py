from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import os, psycopg2, json, hashlib, datetime

router = APIRouter(prefix="/packets", tags=["packets"])

DB_URL = os.environ.get("DATABASE_URL", "postgresql://ns:ns_secure_pwd@postgres:5432/ns")


def _conn():
    return psycopg2.connect(DB_URL)


def _ensure_table():
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS packets (
                    id SERIAL PRIMARY KEY,
                    packet_id TEXT UNIQUE NOT NULL,
                    kind TEXT NOT NULL,
                    payload JSONB,
                    hash TEXT,
                    ts TIMESTAMPTZ DEFAULT NOW()
                )
            """)
        conn.commit()


class Packet(BaseModel):
    kind: str
    payload: Optional[dict] = None


@router.on_event("startup")
async def startup():
    try:
        _ensure_table()
    except Exception:
        pass


@router.post("/")
async def create_packet(packet: Packet):
    body = json.dumps(packet.payload or {}, sort_keys=True)
    h = hashlib.sha256(f"{packet.kind}:{body}".encode()).hexdigest()
    pid = f"pkt_{h[:16]}"
    try:
        with _conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO packets (packet_id, kind, payload, hash) VALUES (%s,%s,%s,%s) ON CONFLICT (packet_id) DO NOTHING RETURNING id",
                    (pid, packet.kind, body, h)
                )
                row = cur.fetchone()
            conn.commit()
        return {"status": "ok", "packet_id": pid, "id": row[0] if row else None}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def list_packets(limit: int = 50):
    try:
        with _conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, packet_id, kind, hash, ts FROM packets ORDER BY ts DESC LIMIT %s",
                    (limit,)
                )
                rows = cur.fetchall()
        return {"packets": [{"id": r[0], "packet_id": r[1], "kind": r[2], "hash": r[3], "ts": str(r[4])} for r in rows]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{packet_id}")
async def get_packet(packet_id: str):
    try:
        with _conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, packet_id, kind, payload, hash, ts FROM packets WHERE packet_id=%s",
                    (packet_id,)
                )
                row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="not found")
        return {"id": row[0], "packet_id": row[1], "kind": row[2], "payload": row[3], "hash": row[4], "ts": str(row[5])}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
