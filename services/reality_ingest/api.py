from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path
import json
from fastapi import FastAPI
import orjson

app = FastAPI(title="RIS", version="1.0")
INT_ROOT = Path.home() / "axiolev_runtime/.run/ris_uspto"
EXT_ROOT = Path("/Volumes/NSExternal/ris/uspto")


@app.get("/ris/healthz")
def healthz():
    return {"ok": True, "service": "ris",
            "ts": datetime.now(timezone.utc).isoformat(),
            "external_mounted": EXT_ROOT.exists()}


@app.get("/ris/state")
def state():
    hb_path = INT_ROOT / "heartbeat.json"
    state_path = INT_ROOT / "state.json"
    out = {"heartbeat": None, "state": None, "external_mounted": EXT_ROOT.exists()}
    if hb_path.exists():
        out["heartbeat"] = json.loads(hb_path.read_text())
        try:
            ts = datetime.fromisoformat(out["heartbeat"]["ts"].replace("Z", "+00:00"))
            age = (datetime.now(timezone.utc) - ts).total_seconds()
            out["heartbeat"]["age_s"] = int(age)
            out["heartbeat"]["live"] = age < 180
        except Exception:
            pass
    if state_path.exists():
        out["state"] = json.loads(state_path.read_text())
    return out


@app.get("/ris/recent")
def recent(limit: int = 50):
    norm_dir = INT_ROOT / "normalized"
    if not norm_dir.exists():
        return {"items": [], "count": 0}
    files = sorted(((p.stat().st_mtime, p) for p in norm_dir.rglob("*.json")), reverse=True)
    items = []
    for _, p in files[:limit]:
        try:
            d = orjson.loads(p.read_bytes())
            items.append({
                "id": d.get("id"),
                "title": (d.get("title") or "")[:120],
                "type": d.get("type"),
                "epistemic_class": d.get("epistemic_class"),
                "credibility": d.get("credibility"),
                "novelty": d.get("novelty"),
                "impact": d.get("impact"),
                "narrative_momentum": d.get("narrative_momentum"),
                "grant_date": d.get("grant_date"),
                "assignees": (d.get("assignees") or [])[:3],
                "cpc_codes": (d.get("cpc_codes") or [])[:3],
            })
        except Exception:
            continue
    return {"items": items, "count": len(items), "ts": datetime.now(timezone.utc).isoformat()}


@app.get("/ris/summary")
def summary():
    sums_dir = EXT_ROOT / "summaries"
    if not sums_dir.exists():
        return {"summary": None}
    sums = sorted(sums_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    return {"summary": orjson.loads(sums[0].read_bytes()), "path": str(sums[0])} if sums else {"summary": None}

@app.get("/ris/sources")
def sources():
    """Cockpit Sources screen feed. Returns lane health + drift state."""
    from services.reality_ingest.source_resolver import USPTOSourceResolver, ResolverConfig
    from pathlib import Path as _P
    import json as _json
    resolver = USPTOSourceResolver(ResolverConfig(
        receipts_dir=_P("/Volumes/NSExternal/ris/uspto/source_receipts"),
        drift_log_dir=_P("/Volumes/NSExternal/ris/uspto/drift_log"),
    ))
    snap = resolver.status_snapshot()
    drift_dir = _P("/Volumes/NSExternal/ris/uspto/drift_log")
    drift_events = []
    if drift_dir.exists():
        for f in sorted(drift_dir.glob("drift_*.json"),
                        key=lambda p: p.stat().st_mtime, reverse=True)[:10]:
            try:
                drift_events.append(_json.loads(f.read_text()))
            except Exception:
                pass
    return {"lanes": snap, "drift_events": drift_events,
            "ts": datetime.now(timezone.utc).isoformat()}


@app.get("/ris/lanes/breakdown")
def lanes_breakdown():
    """Records-per-lane breakdown. Reads from receipts."""
    from collections import Counter
    from pathlib import Path as _P
    receipts = _P("/Volumes/NSExternal/ris/uspto/receipts")
    counts = Counter()
    if receipts.exists():
        for p in list(receipts.rglob("*.json"))[:50000]:
            try:
                data = orjson.loads(p.read_bytes())
                counts[data.get("source_lane", "unknown")] += 1
            except Exception:
                continue
    return {"counts": dict(counts), "total": sum(counts.values())}
