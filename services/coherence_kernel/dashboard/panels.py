"""8 NCOM panel data providers — all read-only queries against the ledger."""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
from services.coherence_kernel.storage import ledger
from services.coherence_kernel.branch_registry import list_branches, get_branch
from services.coherence_kernel.imo.gate import _proposals, _decisions

_ALL_TABLES = [
    "branch_state", "interference_pass", "decoherence_event",
    "readiness_score", "promotion", "reversibility_ledger", "receipt",
]


def panel_branch_registry() -> dict:
    ids = list_branches()
    summary = []
    for bid in ids[:20]:
        b = get_branch(bid)
        if b:
            summary.append({"id": b.id, "claim": b.claim[:80]})
        else:
            summary.append({"id": bid, "claim": None})
    return {
        "panel": "branch_registry",
        "count": len(ids),
        "branches": summary,
        "ts": datetime.now(timezone.utc).isoformat(),
    }


def panel_decoherence_status() -> dict:
    conn = ledger.get_conn()
    rows = conn.execute(
        "SELECT payload, created_at FROM decoherence_event ORDER BY rowid DESC LIMIT 10"
    ).fetchall()
    events = []
    for payload_json, ts in rows:
        try:
            d = json.loads(payload_json)
            events.append({"aggregate": d.get("aggregate"), "breached": d.get("breached"), "ts": ts})
        except Exception:
            pass
    total = conn.execute("SELECT COUNT(*) FROM decoherence_event").fetchone()[0]
    return {
        "panel": "decoherence_status",
        "total_breach_events": total,
        "recent": events,
        "ts": datetime.now(timezone.utc).isoformat(),
    }


def panel_readiness_score() -> dict:
    conn = ledger.get_conn()
    row = conn.execute(
        "SELECT branch_id, score_100, payload, created_at FROM readiness_score ORDER BY rowid DESC LIMIT 1"
    ).fetchone()
    if not row:
        return {"panel": "readiness_score", "latest": None, "ts": datetime.now(timezone.utc).isoformat()}
    branch_id, score_100, payload_json, ts = row
    try:
        sub = json.loads(payload_json)
    except Exception:
        sub = {}
    return {
        "panel": "readiness_score",
        "latest": {
            "branch_id": branch_id,
            "score_100": score_100,
            "sub_metrics": {k: sub.get(k) for k in (
                "coherence", "diversity", "interference_quality", "evidence_weight",
                "contradiction_metabolism", "decoherence_resistance", "readout_discipline",
                "receipt_integrity", "reversibility",
            )},
            "ts": ts,
        },
        "ts": datetime.now(timezone.utc).isoformat(),
    }


def panel_imo_queue() -> dict:
    pending = list(_proposals.keys())
    decided = [
        {"proposal_id": pid, "decision": d.gate_decision}
        for pid, d in _decisions.items()
    ]
    return {
        "panel": "imo_queue",
        "pending_count": len(pending),
        "pending_ids": pending[:10],
        "recent_decisions": decided[-10:],
        "ts": datetime.now(timezone.utc).isoformat(),
    }


def panel_interference_results() -> dict:
    conn = ledger.get_conn()
    rows = conn.execute(
        "SELECT payload, created_at FROM interference_pass ORDER BY rowid DESC LIMIT 10"
    ).fetchall()
    results = []
    for payload_json, ts in rows:
        try:
            d = json.loads(payload_json)
            results.append({
                "quality": d.get("interference_quality_score"),
                "outcome": d.get("cancellation_rule") or d.get("reinforcement_rule"),
                "ts": ts,
            })
        except Exception:
            pass
    total = conn.execute("SELECT COUNT(*) FROM interference_pass").fetchone()[0]
    return {
        "panel": "interference_results",
        "total_passes": total,
        "recent": results,
        "ts": datetime.now(timezone.utc).isoformat(),
    }


def panel_ledger_health() -> dict:
    results = {}
    for table in _ALL_TABLES:
        try:
            conn = ledger.get_conn()
            count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            valid = ledger.verify_chain(table)
            results[table] = {"count": count, "chain_valid": valid}
        except Exception as e:
            results[table] = {"count": -1, "chain_valid": False, "error": str(e)}
    all_valid = all(v.get("chain_valid") for v in results.values())
    return {
        "panel": "ledger_health",
        "all_chains_valid": all_valid,
        "tables": results,
        "ts": datetime.now(timezone.utc).isoformat(),
    }


def panel_black_knight_status() -> dict:
    conn = ledger.get_conn()
    rows = conn.execute(
        "SELECT payload, created_at FROM receipt WHERE op IN ('imo.adjudicate','imo.override','imo.archive') "
        "ORDER BY rowid DESC LIMIT 5"
    ).fetchall()
    recent_ops = []
    for payload_json, ts in rows:
        try:
            d = json.loads(payload_json)
            recent_ops.append({"op": d.get("op"), "branch_id": d.get("branch_id"), "ts": ts})
        except Exception:
            pass
    return {
        "panel": "black_knight_status",
        "active_proposals": len(_proposals),
        "recent_gate_ops": recent_ops,
        "ts": datetime.now(timezone.utc).isoformat(),
    }


def panel_receipt_stream() -> dict:
    conn = ledger.get_conn()
    rows = conn.execute(
        "SELECT op, ref_id, created_at FROM receipt ORDER BY rowid DESC LIMIT 20"
    ).fetchall()
    return {
        "panel": "receipt_stream",
        "receipts": [{"op": op, "ref_id": ref_id, "ts": ts} for op, ref_id, ts in rows],
        "ts": datetime.now(timezone.utc).isoformat(),
    }


PANEL_HANDLERS: dict[str, callable] = {
    "branch_registry":    panel_branch_registry,
    "decoherence_status": panel_decoherence_status,
    "readiness_score":    panel_readiness_score,
    "imo_queue":          panel_imo_queue,
    "interference_results": panel_interference_results,
    "ledger_health":      panel_ledger_health,
    "black_knight_status": panel_black_knight_status,
    "receipt_stream":     panel_receipt_stream,
}
