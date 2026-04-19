"""
axiolev-ui-router-v2
AXIOLEV Holdings LLC © 2026 — axiolevns@axiolev.com

NS∞ Living Architecture UI — 8 named backend endpoints per Ui_addition.pdf.
All responses are projections (L10) and never amend constitutional state (L1-L9).
"""
from __future__ import annotations
import asyncio, json, os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse


ui_router = APIRouter(tags=["ui"])


def _alex_ledger() -> str:
    return os.environ.get("NS_ALEX_LEDGER",
                          "/Volumes/NSExternal/ALEXANDRIA/ledger/ns_events.jsonl")


def _alex_ctf_dir() -> str:
    return os.environ.get("NS_ALEX_CTF",
                          "/Volumes/NSExternal/ALEXANDRIA/ctf/receipts")


def _read_last_jsonl(path: str, n: int = 50) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    p = Path(path)
    if not p.exists():
        return out
    try:
        with p.open("r", encoding="utf-8") as fh:
            lines = fh.readlines()
        for ln in lines[-n:]:
            ln = ln.strip()
            if not ln:
                continue
            try:
                out.append(json.loads(ln))
            except Exception:
                continue
    except Exception:
        pass
    return out


@ui_router.get("/ns/state")
def ns_state() -> Dict[str, Any]:
    return {
        "ts": datetime.now(timezone.utc).isoformat(),
        "layers": {
            "L1": {"name": "Constitutional", "status": "active"},
            "L2": {"name": "Gradient Field", "status": "active"},
            "L3": {"name": "Epistemic Envelope", "status": "active"},
            "L4": {"name": "The Loom", "status": "active"},
            "L5": {"name": "Alexandrian Lexicon", "status": "active"},
            "L6": {"name": "State Manifold", "status": "active"},
            "L7": {"name": "Alexandrian Archive",
                   "status": "mounted" if os.path.isdir("/Volumes/NSExternal/ALEXANDRIA") else "absent"},
            "L8": {"name": "Lineage Fabric", "status": "active"},
            "L9": {"name": "HIC/PDP", "status": "active"},
            "L10": {"name": "Narrative + Interface", "status": "active"},
        },
        "invariants": {f"I{i}": "intact" for i in range(1, 11)},
    }


@ui_router.get("/ns/engine/live")
async def ns_engine_live():
    async def gen():
        count = 0
        while True:
            ts = datetime.now(timezone.utc).isoformat()
            payload = {"ts": ts, "seq": count, "event": "heartbeat", "layer": "L10"}
            yield f"data: {json.dumps(payload)}\n\n"
            count += 1
            await asyncio.sleep(1)
    return StreamingResponse(gen(), media_type="text/event-stream")


@ui_router.get("/program/list")
def program_list() -> Dict[str, Any]:
    return {
        "ts": datetime.now(timezone.utc).isoformat(),
        "programs": [
            {"id": "ns_core", "port": 9000, "status": "unknown"},
            {"id": "handrail", "port": 8011, "status": "unknown"},
            {"id": "continuum", "port": 8788, "status": "unknown"},
            {"id": "state_api", "port": 9090, "status": "unknown"},
        ],
    }


@ui_router.get("/program/{program_id}")
def program_detail(program_id: str) -> Dict[str, Any]:
    known = {"ns_core", "handrail", "continuum", "state_api"}
    if program_id not in known:
        raise HTTPException(status_code=404, detail="program not found")
    return {"id": program_id, "ts": datetime.now(timezone.utc).isoformat(),
            "status": "unknown", "endpoints": []}


@ui_router.get("/alexandria/graph")
def alexandria_graph() -> Dict[str, Any]:
    events = _read_last_jsonl(_alex_ledger(), n=200)
    nodes = []
    seen = set()
    for e in events:
        sid = f"{e.get('event')}:{e.get('subject')}"
        if sid not in seen:
            nodes.append({"id": sid, "kind": e.get("event"), "subject": e.get("subject")})
            seen.add(sid)
    return {"ts": datetime.now(timezone.utc).isoformat(),
            "node_count": len(nodes), "edge_count": 0, "nodes": nodes[:50], "edges": []}


@ui_router.get("/receipt/{receipt_id}")
def receipt_lookup(receipt_id: str) -> Dict[str, Any]:
    ctf_dir = Path(_alex_ctf_dir())
    if ctf_dir.exists():
        for p in ctf_dir.glob("*.json"):
            if receipt_id in p.stem:
                try:
                    with p.open("r", encoding="utf-8") as fh:
                        return json.load(fh)
                except Exception:
                    break
    events = _read_last_jsonl(_alex_ledger(), n=1000)
    for e in events:
        if e.get("sha256", "").startswith(receipt_id) or e.get("subject") == receipt_id:
            return e
    raise HTTPException(status_code=404, detail="receipt not found")


@ui_router.get("/canon")
def canon_view() -> Dict[str, Any]:
    canon_path = os.environ.get("NS_CANON_RULES",
                                "/Volumes/NSExternal/ALEXANDRIA/canon/rules.jsonl")
    rules = _read_last_jsonl(canon_path, n=500)
    return {"ts": datetime.now(timezone.utc).isoformat(),
            "canon_source": canon_path, "rule_count": len(rules),
            "rules_preview": rules[:20],
            "warning": "L10 projection — not authoritative; see L5 Alexandrian Lexicon."}


@ui_router.get("/governance/state")
def governance_state() -> Dict[str, Any]:
    return {
        "ts": datetime.now(timezone.utc).isoformat(),
        "invariants": {
            "I1": "Canon precedes Conversion",
            "I2": "Append-only memory",
            "I3": "No LLM authority over Canon",
            "I4": "Hardware quorum (YubiKey serial 26116460)",
            "I5": "Provenance inertness (SHA-256)",
            "I6": "Sentinel Gate soundness",
            "I7": "Bisimulation with replay (2-safety)",
            "I8": "Distributed eventual consistency",
            "I9": "Byzantine quorum for authority change",
            "I10": "Supersession monotone",
        },
        "quorum_required": 2,
        "quorum_present": None,
        "canon_gate": {
            "score_threshold": 0.82,
            "contradiction_ceiling": 0.25,
            "reconstructability_threshold": 0.90,
            "conditions_six_fold": ["score", "contradiction", "reconstructability",
                                    "lineage_valid", "hic_receipt", "pdp_receipt"],
        },
        "doctrine": "Models propose, NS decides, Violet speaks, Handrail executes, Alexandrian Archive remembers.",
    }
