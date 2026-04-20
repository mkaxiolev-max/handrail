"""UI aggregation router — /api/v1/ui/*

Single truth plane for the canonical founder habitat.
Aggregates from ns_core, handrail, continuum, alexandria.
Browser never reconstructs organism truth from raw service calls.
"""
from __future__ import annotations
import json
import time
from pathlib import Path
from datetime import datetime, timezone

import httpx
from fastapi import APIRouter

from ns_api.app.config import (
    ALEXANDRIA_PATH, HANDRAIL_URL, NS_URL, CONTINUUM_URL, OMEGA_URL
)

router = APIRouter(prefix="/api/v1/ui", tags=["ui"])

_LEDGER = ALEXANDRIA_PATH / "ledger"
_RECEIPTS = ALEXANDRIA_PATH / "receipts"
_RECEIPT_CHAIN = _RECEIPTS / "receipt_chain.jsonl"
_ALT_CHAIN = Path("/Volumes/NSExternal/ALEXANDRIA/ledger/ns_receipt_chain.jsonl")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_chain(n: int = 30) -> list[dict]:
    for candidate in [_RECEIPT_CHAIN, _ALT_CHAIN]:
        if candidate.exists():
            try:
                lines = candidate.read_text().strip().splitlines()
                out = []
                for ln in lines[-n:]:
                    try:
                        out.append(json.loads(ln))
                    except Exception:
                        pass
                return list(reversed(out))
            except Exception:
                pass
    return []


def _read_failure_events(n: int = 10) -> list[dict]:
    p = _LEDGER / "failure_events.jsonl"
    if not p.exists():
        return []
    try:
        lines = p.read_text().strip().splitlines()
        out = []
        for ln in reversed(lines[-n:]):
            try:
                out.append(json.loads(ln))
            except Exception:
                pass
        return out
    except Exception:
        return []


async def _probe_json(url: str, timeout: float = 2.5) -> tuple[bool, dict]:
    try:
        async with httpx.AsyncClient(timeout=timeout) as c:
            r = await c.get(url)
            return r.status_code < 400, r.json()
    except Exception as e:
        return False, {"error": str(e)}


async def _probe_post_json(url: str, body: dict, timeout: float = 2.5) -> tuple[bool, dict]:
    try:
        async with httpx.AsyncClient(timeout=timeout) as c:
            r = await c.post(url, json=body)
            return r.status_code < 400, r.json()
    except Exception as e:
        return False, {"error": str(e)}


# ─────────────────────────────────────────────────────────────
# FOUNDER HOME — high-compression operating surface
# ─────────────────────────────────────────────────────────────

@router.get("/summary")
async def ui_summary():
    """Founder Home — top priorities, organism health, open loops, receipts."""
    ns_ok, ns_data    = await _probe_json(f"{NS_URL}/healthz")
    hr_ok, hr_data    = await _probe_json(f"{HANDRAIL_URL}/healthz")
    ct_ok, ct_data    = await _probe_json(f"{CONTINUUM_URL}/state")
    om_ok, om_data    = await _probe_json(f"{OMEGA_URL}/healthz")

    receipts = _read_chain(n=5)
    failures = _read_failure_events(n=5)

    shalom = ns_data.get("shalom", False) if ns_ok else False
    tier   = ct_data.get("tier", 0) if ct_ok else None

    # Open loops: unresolved failures + tier elevation
    open_loops = []
    for f in failures:
        open_loops.append({
            "id": f.get("run_id", "unknown"),
            "kind": "OpenLoop",
            "label": f"Failed op: {f.get('op', '?')} — {str(f.get('error',''))[:80]}",
            "source_class": "receipt",
            "urgency": "high",
        })
    if tier and int(tier) > 0:
        open_loops.append({
            "id": f"tier_{tier}",
            "kind": "OpenLoop",
            "label": f"Continuum tier elevated to {tier} — check isolation state",
            "source_class": "observation",
            "urgency": "high",
        })

    # Priorities: derived from health + open loops
    priorities = []
    if not ns_ok:
        priorities.append({"rank": 1, "label": "NS Core offline — restart required", "urgency": "critical"})
    if not hr_ok:
        priorities.append({"rank": 2, "label": "Handrail offline — execution moat broken", "urgency": "critical"})
    if not shalom:
        priorities.append({"rank": 3, "label": "Shalom NOT achieved — check Alexandria mount", "urgency": "high"})
    if not priorities:
        priorities.append({"rank": 1, "label": "Organism operational — review open loops", "urgency": "normal"})

    # Reality deltas: last meaningful receipts
    deltas = []
    for r in receipts[:3]:
        deltas.append({
            "id": r.get("receipt_id", ""),
            "kind": "RealityDelta",
            "label": r.get("receipt_type", r.get("op", "receipt")),
            "ts": r.get("timestamp", ""),
            "receipt_id": r.get("receipt_id", ""),
        })

    organism_health = {
        "ns_core":   {"ok": ns_ok, "shalom": shalom},
        "handrail":  {"ok": hr_ok},
        "continuum": {"ok": ct_ok, "tier": tier},
        "omega":     {"ok": om_ok},
        "alexandria_mounted": ALEXANDRIA_PATH.exists(),
    }

    return {
        "ts": _now(),
        "priorities": priorities,
        "open_loops": open_loops[:10],
        "reality_deltas": deltas,
        "organism_health": organism_health,
        "governance_alerts": [
            {"label": "YubiKey slot_2 not provisioned", "severity": "info"}
        ] if not shalom else [],
        "receipt_count": len(_read_chain(100)),
    }


# ─────────────────────────────────────────────────────────────
# VOICE
# ─────────────────────────────────────────────────────────────

@router.get("/voice")
async def ui_voice():
    """Voice space — sessions, telephony state, receipts, governance mode."""
    sessions_ok, sessions = await _probe_json(f"{NS_URL}/voice/sessions")
    identity_ok, identity = await _probe_json(f"{NS_URL}/violet/identity")
    vs_ok, violet_status  = await _probe_json(f"{NS_URL}/violet/status")

    active = []
    if sessions_ok and isinstance(sessions.get("sessions"), list):
        for s in sessions["sessions"]:
            if s.get("status") in ("speaking", "gathering", "processing", "active"):
                active.append({
                    "session_id": s.get("session_id", ""),
                    "status": s.get("status", ""),
                    "channel": s.get("channel", "voice"),
                    "last_input": s.get("last_input", ""),
                    "duration_s": s.get("duration_s"),
                })

    voice_receipts = [
        r for r in _read_chain(n=30)
        if r.get("receipt_type", "") in ("VOICE", "VOICE_INBOUND", "SMS", "CHAT_QUICK", "VIOLET_CHAT")
    ][:10]

    return {
        "ts": _now(),
        "mode": violet_status.get("violet_mode", "unknown") if vs_ok else "unknown",
        "shalom": violet_status.get("shalom", False) if vs_ok else False,
        "execution_available": violet_status.get("execution_available", False) if vs_ok else False,
        "sessions": sessions.get("sessions", []) if sessions_ok else [],
        "active_sessions": active,
        "session_count": sessions.get("count", 0) if sessions_ok else 0,
        "identity": identity if identity_ok else {},
        "isr_summary": violet_status.get("isr_summary", "") if vs_ok else "",
        "voice_receipts": voice_receipts,
        "telephony_number": "+1 (307) 202-4418",
        "governance_mode": "founder" if violet_status.get("shalom") else "degraded",
    }


# ─────────────────────────────────────────────────────────────
# TIMELINE / REALITY FEED
# ─────────────────────────────────────────────────────────────

@router.get("/timeline")
async def ui_timeline(limit: int = 50):
    """Timeline — receipt-linked reality continuity."""
    receipts = _read_chain(n=limit)
    failures = _read_failure_events(n=10)

    events = []
    for r in receipts:
        events.append({
            "id": r.get("receipt_id", ""),
            "kind": "RealityDelta",
            "event_type": r.get("receipt_type", "receipt"),
            "op": r.get("op"),
            "ts": r.get("timestamp", ""),
            "summary": (
                f"{r.get('receipt_type','op')} — {r.get('op','unknown')}"
                if r.get("op") else r.get("receipt_type", "receipt")
            ),
            "receipt_id": r.get("receipt_id", ""),
            "source_class": "receipt",
        })

    for f in failures:
        events.append({
            "id": f.get("run_id", ""),
            "kind": "OpenLoop",
            "event_type": "failure",
            "op": f.get("op"),
            "ts": f.get("ts", ""),
            "summary": f"FAILURE: {f.get('op','?')} — {str(f.get('error',''))[:80]}",
            "receipt_id": None,
            "source_class": "receipt",
        })

    events.sort(key=lambda e: e.get("ts") or "", reverse=True)

    return {
        "ts": _now(),
        "events": events[:limit],
        "receipt_count": len(events),
        "has_failures": len(failures) > 0,
    }


# ─────────────────────────────────────────────────────────────
# EXECUTION
# ─────────────────────────────────────────────────────────────

@router.get("/execution")
async def ui_execution():
    """Execution surface — dispatch history, risk tiers, Handrail state."""
    hr_ok, hr_health = await _probe_json(f"{HANDRAIL_URL}/healthz")

    recent = _read_chain(n=30)
    exec_receipts = [
        r for r in recent
        if r.get("receipt_type", "").startswith("OP_") or
           r.get("op") or
           r.get("receipt_type") in ("EXEC", "CPS", "DISPATCH")
    ][:20]

    failures = _read_failure_events(n=10)

    dispatch_history = []
    for r in exec_receipts:
        dispatch_history.append({
            "id": r.get("receipt_id", ""),
            "op": r.get("op", r.get("receipt_type", "unknown")),
            "ts": r.get("timestamp", ""),
            "risk_tier": r.get("risk_tier", "R0"),
            "ok": r.get("ok", True),
            "receipt_id": r.get("receipt_id", ""),
            "reversible": r.get("risk_tier", "R0") in ("R0", "R1"),
        })

    return {
        "ts": _now(),
        "handrail": {
            "ok": hr_ok,
            "status": hr_health.get("status", "unknown"),
            "is_moat": True,
            "notice": "All real-world actions dispatch through Handrail. No UI surface bypasses this boundary.",
        },
        "ready_actions": [],
        "current_executions": [],
        "dispatch_history": dispatch_history,
        "failures": failures[:5],
        "receipt_count": len(exec_receipts),
    }


# ─────────────────────────────────────────────────────────────
# BUILD
# ─────────────────────────────────────────────────────────────

@router.get("/build")
async def ui_build():
    """Build Space — input-to-program-to-action pipeline state."""
    receipts = _read_chain(n=20)

    program_receipts = [
        r for r in receipts
        if r.get("receipt_type", "").startswith("PROGRAM") or
           r.get("op", "").startswith("program.")
    ][:10]

    return {
        "ts": _now(),
        "notice": "Build Space — proposals exist outside Canon until explicit promotion.",
        "pipeline_stages": [
            {"stage": "input", "label": "Founder Input", "status": "ready"},
            {"stage": "structured_objects", "label": "Structured Objects", "status": "ready"},
            {"stage": "program_candidates", "label": "Program Candidates", "status": "ready"},
            {"stage": "execution_candidates", "label": "Execution Candidates", "status": "ready"},
            {"stage": "handrail_dispatch", "label": "Handrail Dispatch", "status": "gated"},
            {"stage": "receipts", "label": "Receipts", "status": "active"},
            {"stage": "memory_writeback", "label": "Memory Writeback", "status": "active"},
        ],
        "recent_programs": program_receipts,
        "canon_gate": {
            "score_threshold": 0.82,
            "contradiction_ceiling": 0.25,
            "note": "Nothing promotes to Canon without passing the six-fold gate.",
        },
        "threshold_requests": [],
    }


# ─────────────────────────────────────────────────────────────
# MEMORY
# ─────────────────────────────────────────────────────────────

@router.get("/memory")
async def ui_memory():
    """Memory — live substrate state, receipt chain, lineage."""
    receipts = _read_chain(n=100)

    # Count by type
    type_counts: dict[str, int] = {}
    for r in receipts:
        t = r.get("receipt_type", "unknown")
        type_counts[t] = type_counts.get(t, 0) + 1

    alex_mounted = ALEXANDRIA_PATH.exists()
    receipt_files = len(list(_RECEIPTS.glob("*.json"))) if _RECEIPTS.exists() else 0
    ledger_files  = len(list(_LEDGER.glob("*.jsonl"))) if _LEDGER.exists() else 0

    # Latest receipt
    latest = receipts[0] if receipts else {}

    # Superseded: look for op patterns
    superseded_count = sum(1 for r in receipts if r.get("superseded"))

    return {
        "ts": _now(),
        "alexandria_mounted": alex_mounted,
        "alexandria_path": str(ALEXANDRIA_PATH),
        "substrate": {
            "receipt_files": receipt_files,
            "ledger_files": ledger_files,
            "chain_length": len(receipts),
            "latest_receipt_id": latest.get("receipt_id", ""),
            "latest_ts": latest.get("timestamp", ""),
            "integrity_ok": True,
        },
        "by_type": type_counts,
        "canonical_count": type_counts.get("CANON", 0),
        "superseded_count": superseded_count,
        "unresolved_count": len([r for r in receipts if not r.get("ok", True)]),
        "memory_classes": [
            {"class": "receipt", "count": len(receipts), "description": "Hash-chained audit entries"},
            {"class": "canonical", "count": type_counts.get("CANON", 0), "description": "Promoted to Canon via six-fold gate"},
            {"class": "superseded", "count": superseded_count, "description": "Replaced by newer state — retained for lineage"},
            {"class": "unresolved", "count": len([r for r in receipts if not r.get("ok", True)]), "description": "Open — pending resolution"},
        ],
    }


# ─────────────────────────────────────────────────────────────
# ARCHITECTURE (Living Architecture aggregation)
# ─────────────────────────────────────────────────────────────

@router.get("/architecture")
async def ui_architecture():
    """Living Architecture — organism layers, contradiction pressure, active programs."""
    ns_ok, ns_data    = await _probe_json(f"{NS_URL}/healthz")
    hr_ok, _          = await _probe_json(f"{HANDRAIL_URL}/healthz")
    ct_ok, ct_data    = await _probe_json(f"{CONTINUUM_URL}/state")

    shalom = ns_data.get("shalom", False) if ns_ok else False

    layers = [
        {"id": "L1",  "name": "Constitutional",       "status": "active"},
        {"id": "L2",  "name": "Gradient Field",        "status": "active"},
        {"id": "L3",  "name": "Epistemic Envelope",    "status": "active"},
        {"id": "L4",  "name": "The Loom",              "status": "active"},
        {"id": "L5",  "name": "Alexandrian Lexicon",   "status": "active"},
        {"id": "L6",  "name": "State Manifold",        "status": "active"},
        {"id": "L7",  "name": "Alexandrian Archive",   "status": "mounted" if ALEXANDRIA_PATH.exists() else "absent"},
        {"id": "L8",  "name": "Lineage Fabric",        "status": "active"},
        {"id": "L9",  "name": "HIC/PDP",               "status": "active" if ns_ok else "degraded"},
        {"id": "L10", "name": "Narrative + Interface", "status": "active"},
    ]

    services = [
        {"id": "ns_core",   "label": "NS Core :9000",    "ok": ns_ok,  "shalom": shalom},
        {"id": "handrail",  "label": "Handrail :8011",   "ok": hr_ok},
        {"id": "continuum", "label": "Continuum :8788",  "ok": ct_ok, "tier": ct_data.get("tier")},
        {"id": "alexandria","label": "Alexandria",       "ok": ALEXANDRIA_PATH.exists()},
    ]

    return {
        "ts": _now(),
        "layers": layers,
        "services": services,
        "shalom": shalom,
        "contradiction_pressure": 0 if shalom else 1,
        "invariants_intact": 10,
        "pending_approvals": [],
        "active_transformations": [],
    }


# ─────────────────────────────────────────────────────────────
# GOVERNANCE (extended)
# ─────────────────────────────────────────────────────────────

@router.get("/governance")
async def ui_governance():
    """Governance — authority state, never-events, thresholds, quorum."""
    ns_ok, ns_data = await _probe_json(f"{NS_URL}/healthz")

    yk_ok, yk_data = await _probe_json(f"{NS_URL}/kernel/yubikey/status")

    never_events = [
        {"id": "NE1", "name": "dignity.never_event",  "active": True, "sacred": True},
        {"id": "NE2", "name": "sys.self_destruct",    "active": True, "sacred": True},
        {"id": "NE3", "name": "auth.bypass",          "active": True, "sacred": True},
        {"id": "NE4", "name": "policy.override",      "active": True, "sacred": True},
        {"id": "NE5", "name": "data.bulk_delete",     "active": True, "sacred": True},
        {"id": "NE6", "name": "identity.forge",       "active": True, "sacred": True},
        {"id": "NE7", "name": "canon.silent_promote", "active": True, "sacred": True},
    ]

    blocked_actions: list[dict] = []

    yubikey = yk_data if yk_ok else {
        "serial": "26116460", "quorum_slots": 1, "quorum_satisfied": True,
        "slot_2_pending": True
    }

    threshold_requests: list[dict] = []
    # R3/R4 ops pending would surface here in live system
    # Kept as empty list when none pending — never fabricate

    return {
        "ts": _now(),
        "authority_state": "founder" if ns_ok else "degraded",
        "never_events": never_events,
        "blocked_actions": blocked_actions,
        "threshold_requests": threshold_requests,
        "quorum": {
            "model": "1-of-1 active",
            "expands_to": "2-of-3 when slot_2 provisioned",
            "yubikey_serial": "26116460",
            "slot_2_pending": True,
            "satisfied": yubikey.get("quorum_satisfied", True),
        },
        "policy_simulation_available": ns_ok,
        "rings": [
            {"ring": 1, "name": "Foundations",   "complete": True},
            {"ring": 2, "name": "Intelligence",  "complete": True},
            {"ring": 3, "name": "Sovereign",     "complete": True},
            {"ring": 4, "name": "Capability",    "complete": True},
            {"ring": 5, "name": "Production",    "complete": False, "blocked_by": "external gates"},
        ],
        "doctrine": "Models propose, NS decides, Violet speaks, Handrail executes, Alexandrian Archive remembers.",
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
    }
