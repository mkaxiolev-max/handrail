from fastapi import APIRouter, HTTPException
import os, threading, time

router = APIRouter(prefix="/sources", tags=["ingest"])
DB_URL = os.environ.get("DATABASE_URL", "postgresql://ns:ns_secure_pwd@postgres:5432/ns")

_scan_state = {"status": "idle", "started_at": None, "finished_at": None, "result": None, "error": None}


def _run_scan():
    from ingest.file_ingest import load_known_hashes, ingest_scan_results
    from ingest.source_scanner import scan
    _scan_state.update({"status": "running", "started_at": time.time(), "result": None, "error": None})
    try:
        known = load_known_hashes()
        results = scan(known_hashes=known)
        counts = ingest_scan_results(results)
        _scan_state.update({
            "status": "done",
            "finished_at": time.time(),
            "result": {"total_files": len(results), **counts},
        })
    except Exception as e:
        _scan_state.update({"status": "error", "finished_at": time.time(), "error": str(e)})


@router.post("/scan")
async def trigger_scan():
    if _scan_state["status"] == "running":
        return {"status": "already_running", "started_at": _scan_state["started_at"]}
    t = threading.Thread(target=_run_scan, daemon=True)
    t.start()
    return {"status": "started", "message": "Scan running in background. Poll /sources/scan/last for results."}


@router.get("/scan/last")
async def last_scan():
    return _scan_state


@router.get("/items")
async def list_items(limit: int = 100):
    try:
        import psycopg2
        with psycopg2.connect(DB_URL) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, path, size_bytes, sha256, ingest_status, created_at FROM source_items ORDER BY created_at DESC LIMIT %s",
                    (limit,)
                )
                rows = cur.fetchall()
        return {"items": [{"id": str(r[0]), "path": r[1], "size": r[2], "sha256": r[3], "status": r[4], "ts": str(r[5])} for r in rows]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
