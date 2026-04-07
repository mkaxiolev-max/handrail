"""
Immutable receipt chain — SHA256(event + payload + prev_hash).
Stores receipts in postgres with prev_hash column for chain verification.
Verifies chain integrity on startup and on demand via GET /integrity/verify.
"""

import os
import json
import hashlib
import datetime
import psycopg2
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/integrity", tags=["integrity"])

DB_URL = os.environ.get("DATABASE_URL", "postgresql://ns:ns_secure_pwd@postgres:5432/ns")


def _conn():
    return psycopg2.connect(DB_URL)


def _ensure_prev_hash_column():
    """Idempotent migration: add prev_hash column if not present."""
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                ALTER TABLE receipts ADD COLUMN IF NOT EXISTS prev_hash TEXT
            """)
        conn.commit()


def _compute_hash(event: str, payload: dict, prev_hash: str) -> str:
    raw = json.dumps({"event": event, "payload": payload}, sort_keys=True) + prev_hash
    return hashlib.sha256(raw.encode()).hexdigest()


def _get_last_receipt(cur):
    cur.execute(
        "SELECT id, event, payload, hash, prev_hash, created_at "
        "FROM receipts ORDER BY created_at DESC, id DESC LIMIT 1"
    )
    return cur.fetchone()


def verify_chain() -> dict:
    """Load all receipts ordered by created_at and verify each hash."""
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, event, payload, hash, prev_hash, created_at "
                "FROM receipts ORDER BY created_at ASC, id ASC"
            )
            rows = cur.fetchall()

    if not rows:
        return {"status": "ok", "chain_length": 0, "message": "empty chain — genesis state"}

    errors = []
    expected_prev = "0" * 64

    for i, row in enumerate(rows):
        rid, event, payload, stored_hash, stored_prev, created_at = row
        payload_dict = payload if isinstance(payload, dict) else {}

        # Verify prev_hash linkage
        if stored_prev is not None and stored_prev != expected_prev:
            errors.append({
                "index": i,
                "receipt_id": str(rid),
                "error": f"prev_hash mismatch: expected {expected_prev[:16]}… got {str(stored_prev)[:16]}…",
            })

        # Recompute hash
        recomputed = _compute_hash(event, payload_dict, expected_prev)
        if stored_hash != recomputed:
            errors.append({
                "index": i,
                "receipt_id": str(rid),
                "error": f"hash mismatch: stored {str(stored_hash)[:16]}… recomputed {recomputed[:16]}…",
            })

        expected_prev = stored_hash or recomputed

    if errors:
        return {
            "status": "broken",
            "chain_length": len(rows),
            "errors": errors,
            "message": f"Chain broken at {len(errors)} point(s)",
        }

    return {
        "status": "ok",
        "chain_length": len(rows),
        "tip_hash": rows[-1][3],
        "message": "Chain verified — unbroken",
    }


@router.on_event("startup")
async def startup():
    """Ensure prev_hash column exists, then verify chain on startup."""
    try:
        _ensure_prev_hash_column()
    except Exception as e:
        print(f"[receipt_chain] migration warning: {e}")
    try:
        result = verify_chain()
        print(f"[receipt_chain] startup verify: {result['status']} — {result.get('chain_length', 0)} receipts")
    except Exception as e:
        print(f"[receipt_chain] startup verify failed: {e}")


# ── Models ────────────────────────────────────────────────────────────────────

class ReceiptRequest(BaseModel):
    event: str
    payload: Optional[dict] = None


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/receipt")
async def append_receipt(req: ReceiptRequest):
    """Append a receipt to the chain. Computes hash and links to previous."""
    payload = req.payload or {}
    try:
        with _conn() as conn:
            with conn.cursor() as cur:
                last = _get_last_receipt(cur)
                prev_hash = last[3] if last and last[3] else "0" * 64
                h = _compute_hash(req.event, payload, prev_hash)
                cur.execute(
                    "INSERT INTO receipts (event, payload, hash, prev_hash) "
                    "VALUES (%s, %s, %s, %s) RETURNING id, created_at",
                    (req.event, json.dumps(payload), h, prev_hash),
                )
                row = cur.fetchone()
            conn.commit()
        return {
            "status": "appended",
            "id": str(row[0]),
            "event": req.event,
            "hash": h,
            "prev_hash": prev_hash,
            "created_at": row[1].isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/verify")
async def verify_endpoint():
    """Validate entire receipt chain — recomputes every hash."""
    try:
        result = verify_chain()
        if result["status"] == "broken":
            raise HTTPException(status_code=409, detail=result)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chain")
async def get_chain(limit: int = 100):
    """Return receipts in chain order."""
    try:
        with _conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, event, payload, hash, prev_hash, created_at "
                    "FROM receipts ORDER BY created_at ASC, id ASC LIMIT %s",
                    (limit,),
                )
                rows = cur.fetchall()
        return {
            "chain_length": len(rows),
            "receipts": [
                {
                    "id": str(r[0]),
                    "event": r[1],
                    "payload": r[2],
                    "hash": r[3],
                    "prev_hash": r[4],
                    "created_at": r[5].isoformat() if r[5] else None,
                }
                for r in rows
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
