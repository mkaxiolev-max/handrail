"""POST /documents/parse  |  GET /documents/{id}/parse-status"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
import uuid
from pathlib import Path
from typing import Optional

import psycopg2
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from parse.parser import parse
from parse.bundle_builder import build

router = APIRouter(prefix="/documents", tags=["documents"])

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://ns:ns_secure_pwd@postgres:5432/ns")


def _conn():
    return psycopg2.connect(DATABASE_URL)


# ── helpers ──────────────────────────────────────────────────────────────────

def _sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _upsert_source_item(cur, path: str, sha: str, size: int) -> str:
    cur.execute(
        """
        INSERT INTO source_items (path, sha256, size_bytes, ingest_status)
        VALUES (%s, %s, %s, 'parsing')
        ON CONFLICT (path) DO UPDATE
          SET sha256 = EXCLUDED.sha256,
              size_bytes = EXCLUDED.size_bytes,
              ingest_status = 'parsing'
        RETURNING id
        """,
        (path, sha, size),
    )
    return str(cur.fetchone()[0])


def _insert_bundle(cur, bundle) -> str:
    bundle_id = str(uuid.uuid4())
    cur.execute(
        """
        INSERT INTO parse_bundles (id, source_item_id, parser_type, text_content, structure_json)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (
            bundle_id,
            bundle.source_item_id,
            bundle.parser_type,
            bundle.text_content,
            json.dumps(bundle.structure_json),
        ),
    )
    return bundle_id


def _mark_done(cur, source_item_id: str):
    cur.execute(
        "UPDATE source_items SET ingest_status='parsed' WHERE id=%s",
        (source_item_id,),
    )


# ── endpoints ─────────────────────────────────────────────────────────────────

class ParseRequest(BaseModel):
    document_id: Optional[str] = None   # existing source_item id
    path: Optional[str] = None          # direct path (for CPS / internal callers)
    mode: str = "native"


@router.post("/parse")
async def parse_document(
    file: Optional[UploadFile] = File(None),
    document_id: Optional[str] = Form(None),
    path: Optional[str] = Form(None),
    mode: str = Form("native"),
):
    """
    Accept either:
      - multipart file upload  (for direct test)
      - path= form field       (for internal callers referencing host path)
      - document_id= form field (resolve from source_items)
    """
    tmp_path: Optional[str] = None

    try:
        conn = _conn()
        cur = conn.cursor()

        # ── resolve file path ────────────────────────────────────────────
        if file is not None:
            suffix = Path(file.filename or "upload").suffix or ".bin"
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
            shutil.copyfileobj(file.file, tmp)
            tmp.flush()
            tmp_path = tmp.name
            resolve_path = file.filename or tmp_path
        elif path:
            if not Path(path).exists():
                raise HTTPException(404, f"File not found: {path}")
            tmp_path = None
            resolve_path = path
        elif document_id:
            cur.execute("SELECT path FROM source_items WHERE id=%s", (document_id,))
            row = cur.fetchone()
            if not row:
                raise HTTPException(404, f"document_id {document_id} not in source_items")
            resolve_path = row[0]
            tmp_path = None
        else:
            raise HTTPException(400, "Provide file upload, path=, or document_id=")

        actual_path = tmp_path if tmp_path else resolve_path

        # ── register source_item ─────────────────────────────────────────
        sha = _sha256(actual_path)
        size = Path(actual_path).stat().st_size
        source_item_id = _upsert_source_item(cur, resolve_path, sha, size)
        conn.commit()

        # ── parse ────────────────────────────────────────────────────────
        if mode != "native":
            raise HTTPException(400, "Only mode=native supported currently")

        doc = parse(actual_path)

        # ── build bundle + store ─────────────────────────────────────────
        bundle = build(source_item_id, doc)
        bundle_id = _insert_bundle(cur, bundle)
        _mark_done(cur, source_item_id)
        conn.commit()

        return {
            "status": "ok",
            "source_item_id": source_item_id,
            "bundle_id": bundle_id,
            "parser_type": bundle.parser_type,
            "file_type": doc.file_type,
            "page_count": doc.page_count,
            "chunk_count": bundle.chunk_count,
            "text_length": len(doc.raw_text),
            "confidence": bundle.confidence,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))
    finally:
        if tmp_path and Path(tmp_path).exists():
            Path(tmp_path).unlink(missing_ok=True)
        try:
            cur.close()
            conn.close()
        except Exception:
            pass


@router.get("/{document_id}/parse-status")
async def parse_status(document_id: str):
    try:
        conn = _conn()
        cur = conn.cursor()

        cur.execute(
            "SELECT path, sha256, size_bytes, ingest_status, created_at FROM source_items WHERE id=%s",
            (document_id,),
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(404, f"No document with id {document_id}")

        path, sha, size, status, created_at = row

        cur.execute(
            """
            SELECT id, parser_type, created_at,
                   length(text_content) as text_len,
                   structure_json->>'chunk_count' as chunks
            FROM parse_bundles WHERE source_item_id=%s
            ORDER BY created_at DESC LIMIT 5
            """,
            (document_id,),
        )
        bundles = [
            {
                "bundle_id": str(r[0]),
                "parser_type": r[1],
                "created_at": str(r[2]),
                "text_length": r[3],
                "chunk_count": r[4],
            }
            for r in cur.fetchall()
        ]

        return {
            "document_id": document_id,
            "path": path,
            "sha256": sha,
            "size_bytes": size,
            "ingest_status": status,
            "registered_at": str(created_at),
            "bundles": bundles,
            "bundle_count": len(bundles),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))
    finally:
        try:
            cur.close()
            conn.close()
        except Exception:
            pass
