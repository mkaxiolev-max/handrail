"""
Upserts scan results into source_items using the live schema:
  (id uuid, path text UNIQUE, sha256 text, size_bytes bigint, ingest_status text, created_at)
"""
import os, psycopg2
from typing import List, Dict, Any

DB_URL = os.environ.get("DATABASE_URL", "postgresql://ns:ns_secure_pwd@postgres:5432/ns")

def _conn():
    return psycopg2.connect(DB_URL)

def ingest_scan_results(scan_results: List[Dict[str, Any]]) -> Dict[str, int]:
    inserted = skipped = errors = 0
    with _conn() as conn:
        with conn.cursor() as cur:
            for item in scan_results:
                if not item.get("changed", True):
                    skipped += 1
                    continue
                try:
                    cur.execute("""
                        INSERT INTO source_items (path, sha256, size_bytes, ingest_status)
                        VALUES (%s, %s, %s, 'pending')
                        ON CONFLICT (path) DO UPDATE
                            SET sha256=EXCLUDED.sha256,
                                size_bytes=EXCLUDED.size_bytes,
                                ingest_status='pending'
                    """, (item["path"], item["sha256"], item["size"]))
                    inserted += 1
                except Exception:
                    errors += 1
        conn.commit()
    return {"inserted": inserted, "skipped": skipped, "errors": errors}

def load_known_hashes() -> Dict[str, str]:
    try:
        with _conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT path, sha256 FROM source_items")
                return {row[0]: row[1] for row in cur.fetchall()}
    except Exception:
        return {}
