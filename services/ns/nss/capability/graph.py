# Copyright © 2026 Axiolev. All rights reserved.
"""
Capability Graph — structural honesty layer.
Missingness is explicit state, not silence.
States: desired | unresolved | provisional | implemented |
        validated | blocked_policy | blocked_adapter | blocked_san | deprecated
"""
from __future__ import annotations
import json, time
from dataclasses import dataclass, field
from pathlib import Path

_CAP_SSD   = Path("/Volumes/NSExternal/ALEXANDRIA/capability_graph.json")
_CAP_MOUNT = Path("/app/.runs/capability_graph.json")   # docker volume mount
_CAP_FALL  = Path.home() / ".axiolev" / "capability_graph.json"

VALID_STATES = {
    "desired","unresolved","provisional","implemented","validated",
    "blocked_policy","blocked_adapter","blocked_san","deprecated"
}

def _ts() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

def _cap_path() -> Path:
    if Path("/Volumes/NSExternal/ALEXANDRIA").exists():
        return _CAP_SSD
    if _CAP_MOUNT.parent.exists():
        return _CAP_MOUNT
    p = _CAP_FALL; p.parent.mkdir(parents=True, exist_ok=True); return p

SEED_NODES: list[dict] = [
    {"id":"voice_response","name":"Voice Response","domain":"channels","state":"implemented",
     "description":"Twilio voice, streaming Polly.Matthew, barge-in, memory-backed greeting",
     "proof_refs":["founder-mvp-v1","voice-loop-v1"],"strategic_value":9,
     "lexicon_anchor":"voice_interface","depends_on":[],"conflicts_with":[],"blocked_reason":"",
     "san_position":""},
    {"id":"sms_inbound","name":"SMS Inbound","domain":"channels","state":"implemented",
     "description":"Twilio SMS /sms/inbound + session logging",
     "proof_refs":["founder-mvp-v1"],"strategic_value":7,"lexicon_anchor":"sms_interface",
     "depends_on":[],"conflicts_with":[],"blocked_reason":"","san_position":""},
    {"id":"memory_surfacing","name":"Memory Surfacing","domain":"intelligence","state":"implemented",
     "description":"/memory/context, /memory/recent, /memory/search, /memory/sessions",
     "proof_refs":["founder-mvp-v1"],"strategic_value":9,"lexicon_anchor":"memory",
     "depends_on":[],"conflicts_with":[],"blocked_reason":"","san_position":""},
    {"id":"model_routing","name":"Model Router","domain":"intelligence","state":"implemented",
     "description":"5+1 quorum, intent_class routing, veil gate, outcome receipts",
     "proof_refs":["m2-jarvis-v1","model-router-v1"],"strategic_value":8,
     "lexicon_anchor":"model_council","depends_on":[],"conflicts_with":[],"blocked_reason":"","san_position":""},
    {"id":"program_library","name":"Program Library v1","domain":"execution","state":"implemented",
     "description":"10 namespaces, 100 CPS ops, shared meta-contract",
     "proof_refs":["program-library-v1","m2-jarvis-v1"],"strategic_value":9,
     "lexicon_anchor":"program","depends_on":[],"conflicts_with":[],"blocked_reason":"","san_position":""},
    {"id":"founder_console","name":"Founder Console v2","domain":"channels","state":"implemented",
     "description":"WS live badge, health panel, model status, ops feed, memory feed",
     "proof_refs":["founder-console-v2"],"strategic_value":7,"lexicon_anchor":"console",
     "depends_on":[],"conflicts_with":[],"blocked_reason":"","san_position":""},
    {"id":"failure_classification","name":"Failure Classification","domain":"reliability","state":"implemented",
     "description":"4 failure classes → failure_events.jsonl, structured recovery",
     "proof_refs":["temporal-validity-v1"],"strategic_value":7,"lexicon_anchor":"failure",
     "depends_on":[],"conflicts_with":[],"blocked_reason":"","san_position":""},
    {"id":"temporal_validity","name":"Temporal Validity Gate","domain":"reliability","state":"implemented",
     "description":"_memory_clock, 5-min stale refresh, validity_checked on all receipts",
     "proof_refs":["temporal-validity-v1"],"strategic_value":7,"lexicon_anchor":"temporal_validity",
     "depends_on":[],"conflicts_with":[],"blocked_reason":"","san_position":""},
    {"id":"san_adapter","name":"SAN Adapter","domain":"legal","state":"provisional",
     "description":"8 ops: territory, claim, whitespace, risk, filing, licensing, sync",
     "proof_refs":["san-adapter-v1"],"strategic_value":8,"lexicon_anchor":"san",
     "san_position":"filing","depends_on":[],"conflicts_with":[],"blocked_reason":""},
    {"id":"semantic_binder","name":"Semantic Feedback Binder","domain":"intelligence","state":"provisional",
     "description":"Execution → semantic impact → refinement candidates → canon proposals",
     "proof_refs":["semantic-binder-v1"],"strategic_value":9,"lexicon_anchor":"semantic_binder",
     "depends_on":["memory_surfacing"],"conflicts_with":[],"blocked_reason":"","san_position":""},
    {"id":"yubikey_quorum","name":"YubiKey 2-of-3 Quorum","domain":"security","state":"provisional",
     "description":"Hardware: serial 26116460, R3+ gate, sovereign authority",
     "proof_refs":["yubikey-cloud-live-v1"],"strategic_value":10,"lexicon_anchor":"yubikey",
     "blocked_reason":"2nd YubiKey not yet bound","san_position":"",
     "depends_on":[],"conflicts_with":[]},
    {"id":"stripe_billing","name":"Stripe Live Billing","domain":"commercial","state":"blocked_policy",
     "description":"Ring 5 — live payments, MRR tracking",
     "blocked_reason":"LLC business verification docs pending","strategic_value":10,
     "depends_on":["program_library"],"conflicts_with":[],"san_position":"licensing",
     "lexicon_anchor":"stripe","proof_refs":[]},
    {"id":"mobile_app","name":"Mobile App (HNL PASS)","domain":"channels","state":"desired",
     "description":"SwiftUI iOS + Jetpack Compose Android, KMP, PowerSync offline-first",
     "depends_on":["memory_surfacing","model_routing","voice_response"],
     "strategic_value":7,"conflicts_with":[],"blocked_reason":"","san_position":"",
     "lexicon_anchor":"mobile","proof_refs":[]},
    {"id":"2nd_yubikey","name":"2nd YubiKey Hardware","domain":"security","state":"desired",
     "description":"Complete 2-of-3 quorum — physical hardware purchase required",
     "depends_on":["yubikey_quorum"],"strategic_value":8,"conflicts_with":[],
     "blocked_reason":"","san_position":"","lexicon_anchor":"","proof_refs":[]},
    {"id":"policy_evolution","name":"Policy Evolution Layer","domain":"governance","state":"unresolved",
     "description":"Proposal → validation → quorum → versioning → Canon activation",
     "depends_on":["gov","semantic_binder"],"strategic_value":7,"conflicts_with":[],
     "blocked_reason":"","san_position":"","lexicon_anchor":"policy","proof_refs":[]},
    {"id":"explainability_engine","name":"Explainability Engine","domain":"intelligence","state":"unresolved",
     "description":"Decision trace, model contributions, veto reasons, memory references surfaced",
     "depends_on":["model_routing","memory_surfacing"],"strategic_value":6,
     "conflicts_with":[],"blocked_reason":"","san_position":"","lexicon_anchor":"","proof_refs":[]},
    {"id":"usdl_decoder_live","name":"USDL Decoder Live","domain":"intelligence","state":"unresolved",
     "description":"DNA→USDL 1:1 decoder running live against Lexicon state capsule",
     "depends_on":["semantic_binder","memory_surfacing"],"strategic_value":8,
     "conflicts_with":[],"blocked_reason":"","san_position":"","lexicon_anchor":"usdl_decoder",
     "proof_refs":[]},
    {"id":"cognitive_failover","name":"Cognitive Availability Failover","domain":"reliability","state":"provisional",
     "description":"Full Council → Primary+Critic → Primary → Guardian → Safe Mode",
     "depends_on":["model_routing"],"strategic_value":7,"conflicts_with":[],
     "blocked_reason":"","san_position":"","lexicon_anchor":"","proof_refs":["model-router-v1"]},
    # ── V2 Desired Nodes (Layer D honesty invariant) ──────────────────────────
    {"id":"san_sync_layer","name":"SAN/Legal-Reality Sync","domain":"legal","state":"desired",
     "description":"LLC, Stripe, IP, equity table, YubiKey quorum verified against Alexandria",
     "depends_on":[],"strategic_value":9,"conflicts_with":[],"blocked_reason":"",
     "san_position":"filing","lexicon_anchor":"san_sync","proof_refs":[]},
    {"id":"semantic_feedback_binder","name":"Semantic Feedback Binder V2","domain":"intelligence","state":"desired",
     "description":"Execution outcomes → Lexicon/HIC canon update loop via SemanticFeedbackProcessor",
     "depends_on":["memory_surfacing","model_routing"],"strategic_value":8,"conflicts_with":[],
     "blocked_reason":"","san_position":"","lexicon_anchor":"semantic_feedback","proof_refs":[]},
    {"id":"degradation_kernel","name":"Cognitive Degradation Kernel","domain":"reliability","state":"desired",
     "description":"4-tier: nominal→degraded→minimal→safe-shutdown with formal documented behavior",
     "depends_on":["model_routing","cognitive_failover"],"strategic_value":8,"conflicts_with":[],
     "blocked_reason":"","san_position":"","lexicon_anchor":"degradation","proof_refs":[]},
    {"id":"multi_model_routing","name":"Multi-Model Tier Routing","domain":"intelligence","state":"desired",
     "description":"Haiku/Sonnet/Opus tier routing by task complexity + cost envelope",
     "depends_on":["model_routing"],"strategic_value":7,"conflicts_with":[],
     "blocked_reason":"","san_position":"","lexicon_anchor":"model_routing","proof_refs":[]},
    {"id":"wearable_power_adapter","name":"Wearable Power Consortium Adapter","domain":"commercial","state":"desired",
     "description":"Dean Schlingmann / Wearable Power Consortium CPS integration layer (25% equity)",
     "depends_on":[],"strategic_value":8,"conflicts_with":[],"blocked_reason":"",
     "san_position":"licensing","lexicon_anchor":"wearable","proof_refs":[]},
]


class CapabilityGraph:
    def __init__(self):
        self._nodes: dict[str, dict] = {}
        self._load()

    def _load(self) -> None:
        p = _cap_path()
        if p.exists():
            try:
                data = json.loads(p.read_text())
                self._nodes = {n["id"]: n for n in data.get("nodes",[])}
                return
            except Exception:
                pass
        for seed in SEED_NODES:
            self._nodes[seed["id"]] = {**seed, "updated_at": _ts()}
        self._save()

    def _save(self) -> None:
        _cap_path().write_text(json.dumps(
            {"nodes": list(self._nodes.values()), "updated_at": _ts()}, indent=2))

    def all_nodes(self) -> list[dict]:
        return list(self._nodes.values())

    def unresolved_nodes(self) -> list[dict]:
        return sorted(
            [n for n in self._nodes.values() if n.get("state") in ("unresolved", "desired")],
            key=lambda n: -n.get("strategic_value", 0))

    def top_unresolved(self, n: int = 3) -> list[dict]:
        return self.unresolved_nodes()[:n]

    def summary(self) -> dict:
        states: dict[str, int] = {}
        for n in self._nodes.values():
            s = n.get("state", "unknown")
            states[s] = states.get(s, 0) + 1
        return {"total": len(self._nodes), "by_state": states, "ts": _ts()}

    def update_node(self, node_id: str, state: str | None = None,
                    proof_ref: str | None = None, blocked_reason: str | None = None) -> dict:
        if node_id not in self._nodes:
            return {"ok": False, "error": f"node {node_id} not found"}
        node = self._nodes[node_id]
        if state:
            if state not in VALID_STATES:
                return {"ok": False, "error": f"invalid state {state}"}
            node["state"] = state
        if proof_ref:
            node.setdefault("proof_refs", [])
            if proof_ref not in node["proof_refs"]:
                node["proof_refs"].append(proof_ref)
        if blocked_reason is not None:
            node["blocked_reason"] = blocked_reason
        node["updated_at"] = _ts()
        self._nodes[node_id] = node
        self._save()
        return {"ok": True, "node_id": node_id, "state": node["state"], "ts": node["updated_at"]}


_graph: CapabilityGraph | None = None

def get_graph() -> CapabilityGraph:
    global _graph
    if _graph is None:
        _graph = CapabilityGraph()
    return _graph
