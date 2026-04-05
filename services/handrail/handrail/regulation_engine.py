# Copyright © 2026 Axiolev. All rights reserved.
"""
Constitutional Regulation Engine v1
=====================================
Unified governance loop — the bloodstream connecting all constitutional organs.

Every sovereign action passes through a TransitionLifecycle:
  begin() → attach_*() → append_delta() → finalize()

The lifecycle record is appended to the ProofRegistry and persisted to
WORKSPACE/.run/transitions.jsonl (append-only, same pattern as proof_registry).

TypedStateDelta domains
-----------------------
epistemic      Knowledge / memory state changes (model registry, capability graph)
operational    Runtime state changes (CPS execution, boot phases, adapter health)
constitutional Governance state changes (YubiKey quorum, ABI freeze, policy)
commercial     Revenue / Stripe / subscription state changes
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import random
import string
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

_log = logging.getLogger("handrail.regulation_engine")

_CHARS = string.ascii_uppercase + string.digits


def _make_sdl_id() -> str:
    return "SDL-" + "".join(random.choices(_CHARS, k=8))


def _make_trn_id() -> str:
    return "TRN-" + "".join(random.choices(_CHARS, k=8))


# ── TypedStateDelta ────────────────────────────────────────────────────────────

DELTA_DOMAINS = {"epistemic", "operational", "constitutional", "commercial"}
SOURCE_SURFACES = {"voice", "text", "console", "api", "system", "boot"}


@dataclass
class TypedStateDelta:
    state_delta_id: str
    transition_id:  str
    delta_domain:   str   # one of DELTA_DOMAINS
    target:         str
    before:         Dict[str, Any]
    after:          Dict[str, Any]
    proof_ref:      Optional[str]
    timestamp:      str


# ── TransitionLifecycle ────────────────────────────────────────────────────────

@dataclass
class TransitionLifecycle:
    transition_id:  str
    source_surface: str   # one of SOURCE_SURFACES
    objective:      str
    sovereign:      bool
    timestamp:      str
    intent_ref:     Optional[str] = None
    decision_ref:   Optional[str] = None
    cps_ref:        Optional[str] = None
    return_ref:     Optional[str] = None
    proof_ref:      Optional[str] = None
    state_deltas:   List[TypedStateDelta] = field(default_factory=list)
    metadata:       Dict[str, Any] = field(default_factory=dict)


# ── Persistence helpers ────────────────────────────────────────────────────────

def _transitions_path() -> Path:
    workspace = Path(os.environ.get("HR_WORKSPACE", "/app"))
    return workspace / ".run" / "transitions.jsonl"


def _lifecycle_to_dict(lc: TransitionLifecycle) -> Dict:
    d = asdict(lc)
    # Convert nested TypedStateDelta dataclasses (already handled by asdict)
    return d


def _append_transition(lc: TransitionLifecycle) -> None:
    path = _transitions_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a") as f:
            f.write(json.dumps(_lifecycle_to_dict(lc)) + "\n")
    except Exception as e:
        _log.warning("_append_transition failed: %s", e)


def _read_transitions() -> List[Dict]:
    path = _transitions_path()
    if not path.exists():
        return []
    try:
        lines = [l.strip() for l in path.read_text().splitlines() if l.strip()]
        return [json.loads(l) for l in lines]
    except Exception as e:
        _log.warning("_read_transitions failed: %s", e)
        return []


# ── RegulationEngine ───────────────────────────────────────────────────────────

class RegulationEngine:
    """
    Stateless class — all state is persisted to transitions.jsonl.

    Usage pattern:
        lc = RegulationEngine.begin("voice", "process voice command", metadata={"call_sid": sid})
        RegulationEngine.attach_cps(lc, cps_id)
        RegulationEngine.append_delta(lc, "operational", "voice.handler", {}, {"transcript": t})
        RegulationEngine.finalize(lc)
    """

    # ── Lifecycle management ───────────────────────────────────────────────────

    @staticmethod
    def begin(
        source_surface: str,
        objective: str,
        metadata: Optional[Dict] = None,
        sovereign: bool = False,
    ) -> TransitionLifecycle:
        """Open a new TransitionLifecycle. Call finalize() when done."""
        return TransitionLifecycle(
            transition_id=_make_trn_id(),
            source_surface=source_surface if source_surface in SOURCE_SURFACES else "api",
            objective=objective,
            sovereign=sovereign,
            timestamp=datetime.now(timezone.utc).isoformat(),
            metadata=metadata or {},
        )

    @staticmethod
    def attach_intent(lc: TransitionLifecycle, intent_ref: str) -> None:
        lc.intent_ref = intent_ref

    @staticmethod
    def attach_decision(lc: TransitionLifecycle, decision_ref: str) -> None:
        lc.decision_ref = decision_ref

    @staticmethod
    def attach_cps(lc: TransitionLifecycle, cps_ref: str) -> None:
        lc.cps_ref = cps_ref

    @staticmethod
    def attach_return(lc: TransitionLifecycle, return_ref: str) -> None:
        lc.return_ref = return_ref

    @staticmethod
    def attach_proof(lc: TransitionLifecycle, proof_ref: str, sovereign: bool = False) -> None:
        lc.proof_ref = proof_ref
        if sovereign:
            lc.sovereign = True

    @staticmethod
    def append_delta(
        lc: TransitionLifecycle,
        delta_domain: str,
        target: str,
        before: Dict,
        after: Dict,
        proof_ref: Optional[str] = None,
    ) -> TypedStateDelta:
        """Append a typed state delta to the lifecycle."""
        delta = TypedStateDelta(
            state_delta_id=_make_sdl_id(),
            transition_id=lc.transition_id,
            delta_domain=delta_domain if delta_domain in DELTA_DOMAINS else "operational",
            target=target,
            before=before,
            after=after,
            proof_ref=proof_ref,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        lc.state_deltas.append(delta)
        return delta

    @staticmethod
    def finalize(lc: TransitionLifecycle) -> TransitionLifecycle:
        """Persist the lifecycle to transitions.jsonl. Returns lc."""
        _append_transition(lc)
        _log.info(
            "regulation_engine: finalized %s [%s] sovereign=%s deltas=%d",
            lc.transition_id, lc.source_surface, lc.sovereign, len(lc.state_deltas),
        )
        return lc

    # ── Read ───────────────────────────────────────────────────────────────────

    @staticmethod
    def latest_transitions(n: int = 10) -> List[Dict]:
        """Return the last n transitions, newest-first."""
        entries = _read_transitions()
        entries.sort(key=lambda e: e.get("timestamp", ""), reverse=True)
        return entries[:n]

    @staticmethod
    def get_transition(transition_id: str) -> Optional[Dict]:
        for e in _read_transitions():
            if e.get("transition_id") == transition_id:
                return e
        return None

    @staticmethod
    def state_summary() -> Dict:
        """Summarize the current state across all constitutional domains."""
        entries = _read_transitions()
        domain_counts: Dict[str, int] = {d: 0 for d in DELTA_DOMAINS}
        surface_counts: Dict[str, int] = {s: 0 for s in SOURCE_SURFACES}
        sovereign_count = 0
        total_deltas = 0

        for e in entries:
            surface = e.get("source_surface", "api")
            if surface in surface_counts:
                surface_counts[surface] += 1
            if e.get("sovereign"):
                sovereign_count += 1
            for delta in e.get("state_deltas", []):
                domain = delta.get("delta_domain", "operational")
                if domain in domain_counts:
                    domain_counts[domain] += 1
                total_deltas += 1

        latest = entries[-3:] if len(entries) >= 3 else entries
        latest = sorted(latest, key=lambda e: e.get("timestamp", ""), reverse=True)

        return {
            "total_transitions": len(entries),
            "total_deltas": total_deltas,
            "sovereign_transitions": sovereign_count,
            "domain_counts": domain_counts,
            "surface_counts": surface_counts,
            "latest_transitions": [
                {
                    "transition_id": e.get("transition_id"),
                    "source_surface": e.get("source_surface"),
                    "objective": e.get("objective"),
                    "sovereign": e.get("sovereign"),
                    "timestamp": e.get("timestamp"),
                    "delta_count": len(e.get("state_deltas", [])),
                }
                for e in latest
            ],
        }

    @staticmethod
    def latest_deltas(n: int = 10) -> List[Dict]:
        """Return the last n state deltas across all transitions, newest-first."""
        all_deltas = []
        for e in _read_transitions():
            for delta in e.get("state_deltas", []):
                all_deltas.append(delta)
        all_deltas.sort(key=lambda d: d.get("timestamp", ""), reverse=True)
        return all_deltas[:n]

    # ── Seeding from ProofRegistry ─────────────────────────────────────────────

    @staticmethod
    def seed_from_proof_registry() -> int:
        """
        Backfill constitutional and boot transitions from the ProofRegistry.
        Idempotent — skips proof_ids already referenced in transitions.jsonl.
        Returns count of new transitions seeded.
        """
        try:
            from handrail.proof_registry import ProofRegistry
        except ImportError:
            _log.warning("seed_from_proof_registry: ProofRegistry not available")
            return 0

        existing = _read_transitions()
        known_proof_refs = {
            e.get("proof_ref")
            for e in existing
            if e.get("proof_ref")
        }

        seeded = 0
        for entry in ProofRegistry.full_chain():
            proof_id = entry.get("proof_id")
            if not proof_id or proof_id in known_proof_refs:
                continue

            proof_type = entry.get("proof_type", "")
            source_map = {
                "BOOT": "boot",
                "SCHEMA_FREEZE": "system",
                "QUORUM_ENROLLMENT": "system",
                "CAPABILITY_PROMOTION": "system",
                "POLICY_CHANGE": "console",
                "FOUNDER_APPROVAL": "console",
            }
            domain_map = {
                "BOOT": "operational",
                "SCHEMA_FREEZE": "constitutional",
                "QUORUM_ENROLLMENT": "constitutional",
                "CAPABILITY_PROMOTION": "epistemic",
                "POLICY_CHANGE": "constitutional",
                "FOUNDER_APPROVAL": "constitutional",
            }

            source = source_map.get(proof_type, "system")
            domain = domain_map.get(proof_type, "operational")

            lc = RegulationEngine.begin(
                source_surface=source,
                objective=f"backfill: {proof_type} proof {proof_id}",
                sovereign=entry.get("sovereign", False),
            )
            lc.timestamp = entry.get("timestamp", lc.timestamp)
            lc.proof_ref = proof_id

            RegulationEngine.append_delta(
                lc,
                delta_domain=domain,
                target=proof_type.lower(),
                before={},
                after=entry.get("metadata", {}),
                proof_ref=proof_id,
            )
            _append_transition(lc)
            known_proof_refs.add(proof_id)
            seeded += 1

        _log.info("seed_from_proof_registry: seeded %d transitions", seeded)
        return seeded


# ── Delta factory helpers ──────────────────────────────────────────────────────

def make_boot_delta(
    lc: TransitionLifecycle,
    boot_mode: str,
    phases_passed: int,
    proof_ref: Optional[str] = None,
) -> TypedStateDelta:
    return RegulationEngine.append_delta(
        lc,
        delta_domain="operational",
        target="sovereign_boot",
        before={"status": "pending"},
        after={"status": "complete", "boot_mode": boot_mode, "phases_passed": phases_passed},
        proof_ref=proof_ref,
    )


def make_quorum_delta(
    lc: TransitionLifecycle,
    slot_id: str,
    serial: str,
    proof_ref: Optional[str] = None,
) -> TypedStateDelta:
    return RegulationEngine.append_delta(
        lc,
        delta_domain="constitutional",
        target=f"yubikey.{slot_id}",
        before={"enrolled": False},
        after={"enrolled": True, "serial": serial},
        proof_ref=proof_ref,
    )


def make_capability_delta(
    lc: TransitionLifecycle,
    capability_name: str,
    from_state: str,
    to_state: str,
    proof_ref: Optional[str] = None,
) -> TypedStateDelta:
    return RegulationEngine.append_delta(
        lc,
        delta_domain="epistemic",
        target=f"capability.{capability_name}",
        before={"state": from_state},
        after={"state": to_state},
        proof_ref=proof_ref,
    )


def make_commercial_delta(
    lc: TransitionLifecycle,
    event: str,
    before: Dict,
    after: Dict,
    proof_ref: Optional[str] = None,
) -> TypedStateDelta:
    return RegulationEngine.append_delta(
        lc,
        delta_domain="commercial",
        target=f"commercial.{event}",
        before=before,
        after=after,
        proof_ref=proof_ref,
    )


def make_schema_freeze_delta(
    lc: TransitionLifecycle,
    schema_name: str,
    freeze_hash: str,
    proof_ref: Optional[str] = None,
) -> TypedStateDelta:
    return RegulationEngine.append_delta(
        lc,
        delta_domain="constitutional",
        target=f"abi.{schema_name}",
        before={"frozen": False},
        after={"frozen": True, "hash": freeze_hash},
        proof_ref=proof_ref,
    )
