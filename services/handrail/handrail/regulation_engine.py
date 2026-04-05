"""
Constitutional Regulation Engine v1
====================================
The bloodstream of NS∞. Every consequential action that changes system state
must traverse: ingress → intent → decision → CPS → return → proof → StateDelta.

The 6-component engine chain (from Gnoseogenic Lexicon Tier 5):
  gradient_source → intake → conversion → output → feedback → waste

Maps to:
  ingress surface → IntentPacket → Simulation/Decision → CPSPacket → ReturnBlock → ProofEntry → StateDelta
"""

import json, os, random, hashlib, logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional

_log = logging.getLogger("regulation_engine")

WORKSPACE = Path(os.environ.get("HR_WORKSPACE", "/app"))
_LEDGER_PATH = WORKSPACE / ".run" / "state_transitions.jsonl"
_FALLBACK_LEDGER = Path("/tmp/axiolev_state_transitions.jsonl")

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

def _make_sdl_id() -> str:
    return "SDL-" + "".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=8))

def _make_trn_id() -> str:
    return "TRN-" + "".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=8))


@dataclass
class TypedStateDelta:
    state_delta_id: str
    transition_id: str
    delta_domain: str   # epistemic / operational / constitutional / commercial
    target: str
    before: Dict[str, Any]
    after: Dict[str, Any]
    proof_ref: str
    timestamp: str

    @classmethod
    def make(cls, transition_id: str, delta_domain: str, target: str,
             before: dict, after: dict, proof_ref: str = "") -> "TypedStateDelta":
        return cls(
            state_delta_id=_make_sdl_id(),
            transition_id=transition_id,
            delta_domain=delta_domain,
            target=target,
            before=before,
            after=after,
            proof_ref=proof_ref,
            timestamp=_now(),
        )

    @staticmethod
    def make_boot_delta(transition_id: str, receipt: dict, prev_sovereign: bool = False) -> "TypedStateDelta":
        return TypedStateDelta.make(
            transition_id=transition_id,
            delta_domain="constitutional",
            target="system.boot",
            before={"sovereign": prev_sovereign},
            after={"sovereign": receipt.get("sovereign", False),
                   "receipt_id": receipt.get("receipt_id"),
                   "boot_mode": receipt.get("boot_mode"),
                   "ops_passing": 29},
            proof_ref=receipt.get("receipt_id", ""),
        )

    @staticmethod
    def make_quorum_delta(transition_id: str, slot_id: str,
                          enrolled_before: int, enrolled_after: int) -> "TypedStateDelta":
        return TypedStateDelta.make(
            transition_id=transition_id,
            delta_domain="constitutional",
            target="system.quorum",
            before={"enrolled_count": enrolled_before},
            after={"enrolled_count": enrolled_after, "latest_slot": slot_id},
            proof_ref="",
        )

    @staticmethod
    def make_schema_freeze_delta(transition_id: str, schema_name: str,
                                  fingerprint: str) -> "TypedStateDelta":
        return TypedStateDelta.make(
            transition_id=transition_id,
            delta_domain="epistemic",
            target=f"abi.{schema_name}",
            before={"frozen": False},
            after={"frozen": True, "fingerprint": fingerprint},
            proof_ref="",
        )

    @staticmethod
    def make_commercial_delta(transition_id: str, product: str,
                               event_type: str, metadata: dict = None) -> "TypedStateDelta":
        return TypedStateDelta.make(
            transition_id=transition_id,
            delta_domain="commercial",
            target=f"commerce.{product}",
            before={"status": "pending"},
            after={"status": event_type, **(metadata or {})},
            proof_ref="",
        )

    @staticmethod
    def make_capability_delta(transition_id: str, cap_id: str,
                               before_status: str, after_status: str) -> "TypedStateDelta":
        return TypedStateDelta.make(
            transition_id=transition_id,
            delta_domain="operational",
            target=f"capability.{cap_id}",
            before={"status": before_status},
            after={"status": after_status},
            proof_ref="",
        )


@dataclass
class TransitionLifecycle:
    transition_id: str
    source_surface: str
    objective: str
    intent_ref: str = ""
    decision_ref: str = ""
    cps_ref: str = ""
    return_ref: str = ""
    proof_ref: str = ""
    state_deltas: List[str] = field(default_factory=list)
    sovereign: bool = False
    timestamp: str = field(default_factory=_now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def make(cls, source_surface: str, objective: str,
             metadata: dict = None) -> "TransitionLifecycle":
        return cls(
            transition_id=_make_trn_id(),
            source_surface=source_surface,
            objective=objective,
            metadata=metadata or {},
        )


class RegulationEngine:
    """One enforced lifecycle for every consequential NS∞ state transition."""

    @staticmethod
    def _ledger() -> Path:
        for p in (_LEDGER_PATH, _FALLBACK_LEDGER):
            try:
                p.parent.mkdir(parents=True, exist_ok=True)
                return p
            except Exception:
                continue
        return _FALLBACK_LEDGER

    @staticmethod
    def begin(source_surface: str, objective: str,
              metadata: dict = None) -> TransitionLifecycle:
        return TransitionLifecycle.make(source_surface, objective, metadata or {})

    @staticmethod
    def attach_intent(lc: TransitionLifecycle, intent_id: str):
        lc.intent_ref = intent_id

    @staticmethod
    def attach_decision(lc: TransitionLifecycle, decision_id: str):
        lc.decision_ref = decision_id

    @staticmethod
    def attach_cps(lc: TransitionLifecycle, cps_id: str):
        lc.cps_ref = cps_id

    @staticmethod
    def attach_return(lc: TransitionLifecycle, return_id: str):
        lc.return_ref = return_id

    @staticmethod
    def attach_proof(lc: TransitionLifecycle, proof_id: str):
        lc.proof_ref = proof_id
        if proof_id:
            lc.sovereign = True

    @staticmethod
    def append_delta(lc: TransitionLifecycle, delta: TypedStateDelta):
        lc.state_deltas.append(delta.state_delta_id)
        # Persist the delta inline with the lifecycle
        lc.metadata.setdefault("_deltas", []).append(asdict(delta))

    @staticmethod
    def finalize(lc: TransitionLifecycle) -> dict:
        record = asdict(lc)
        try:
            path = RegulationEngine._ledger()
            with open(path, "a") as f:
                f.write(json.dumps(record) + "\n")
        except Exception as e:
            _log.warning("RegulationEngine.finalize: persist failed: %s", e)
        return record

    @staticmethod
    def latest_transitions(n: int = 20) -> List[dict]:
        for path in (_LEDGER_PATH, _FALLBACK_LEDGER):
            if path.exists():
                try:
                    lines = [l.strip() for l in path.read_text().splitlines() if l.strip()]
                    records = [json.loads(l) for l in lines]
                    return list(reversed(records[-n:]))
                except Exception as e:
                    _log.warning("latest_transitions: %s", e)
        return []

    @staticmethod
    def get_transition(transition_id: str) -> Optional[dict]:
        for path in (_LEDGER_PATH, _FALLBACK_LEDGER):
            if path.exists():
                try:
                    for line in path.read_text().splitlines():
                        if not line.strip():
                            continue
                        r = json.loads(line)
                        if r.get("transition_id") == transition_id:
                            return r
                except Exception:
                    pass
        return None

    @staticmethod
    def state_summary() -> dict:
        """Compressed current constitutional truth across all domains."""
        transitions = RegulationEngine.latest_transitions(100)
        all_deltas = []
        for t in transitions:
            for d in t.get("metadata", {}).get("_deltas", []):
                all_deltas.append(d)

        def latest_delta_of_domain(domain: str) -> Optional[dict]:
            for d in reversed(all_deltas):
                if d.get("delta_domain") == domain:
                    return d
            return None

        boot_delta = latest_delta_of_domain("constitutional")
        commercial_delta = latest_delta_of_domain("commercial")
        epistemic_delta = latest_delta_of_domain("epistemic")
        operational_delta = latest_delta_of_domain("operational")

        return {
            "boot_sovereign": (boot_delta or {}).get("after", {}).get("sovereign", False),
            "last_receipt_id": (boot_delta or {}).get("after", {}).get("receipt_id"),
            "quorum_enrolled_count": (boot_delta or {}).get("after", {}).get("enrolled_count"),
            "schemas_frozen": len([d for d in all_deltas if d.get("delta_domain") == "epistemic"]),
            "latest_commercial_event": (commercial_delta or {}).get("after", {}).get("status"),
            "latest_capability_promotion": (operational_delta or {}).get("after", {}).get("status"),
            "latest_founder_action": None,
            "total_transitions": len(transitions),
            "total_state_deltas": len(all_deltas),
        }

    @staticmethod
    def seed_from_proof_registry(freeze_manifest: dict = None):
        """Backfill TransitionLifecycle records from existing ProofRegistry entries on startup."""
        try:
            from handrail.proof_registry import ProofRegistry, ProofType
            existing = {t.get("transition_id") for t in RegulationEngine.latest_transitions(1000)}
            chain = ProofRegistry.full_chain()
            seeded = 0
            for entry in chain:
                ptype = entry.get("proof_type", "")
                if ptype == ProofType.BOOT.value:
                    lc = RegulationEngine.begin("boot", "sovereign boot (backfilled)", {"backfill": True})
                    RegulationEngine.attach_proof(lc, entry.get("proof_id", ""))
                    meta = entry.get("metadata", {})
                    delta = TypedStateDelta.make_boot_delta(
                        lc.transition_id,
                        {"sovereign": entry.get("sovereign", False),
                         "receipt_id": meta.get("receipt_id", ""),
                         "boot_mode": meta.get("boot_mode", "FULL")},
                        prev_sovereign=False,
                    )
                    RegulationEngine.append_delta(lc, delta)
                    RegulationEngine.finalize(lc)
                    seeded += 1
                elif ptype == ProofType.SCHEMA_FREEZE.value and freeze_manifest:
                    for schema_name, fingerprint in freeze_manifest.items():
                        lc = RegulationEngine.begin("system", f"schema freeze: {schema_name} (backfilled)", {"backfill": True})
                        delta = TypedStateDelta.make_schema_freeze_delta(lc.transition_id, schema_name, fingerprint)
                        RegulationEngine.append_delta(lc, delta)
                        RegulationEngine.finalize(lc)
                        seeded += 1
                    break  # only seed schema freezes once
            _log.info("RegulationEngine.seed_from_proof_registry: seeded %d transitions", seeded)
        except Exception as e:
            _log.warning("seed_from_proof_registry failed (non-fatal): %s", e)

    @staticmethod
    def make_system_intent(objective: str) -> str:
        """Generate a system-origin intent reference string."""
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        return f"SYSTEM-INTENT-{ts}-{objective[:20].replace(' ','-').upper()}"
