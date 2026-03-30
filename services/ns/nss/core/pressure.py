"""
NS Stabilization Theory Layer — Implementation
CANON: CANON_STABILIZATION_THEORY_v1.md

Three architectural objects:
  1. StabilizationPressureField (SPF) — predicts commits
  2. CompetingCommitTrajectories (CCT) — explains provisional dynamics
  3. StabilizationCostSurface (SCS) — explains timing + governance

These three together make NS a general stabilization protocol,
not just a knowledge management or governance tool.

The key axiom: Commit is the irreversible selection of one trajectory
under accumulated pressure at measurable cost.
"""

import json
import hashlib
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from enum import Enum


# ── Constants ─────────────────────────────────────────────────────────────────

class SPFZone(str, Enum):
    LATENT   = "LATENT"    # 0.0 – 0.3  Normal productive tension
    ACTIVE   = "ACTIVE"    # 0.3 – 0.6  Pressure building
    CRITICAL = "CRITICAL"  # 0.6 – 0.85 Commit imminent
    FRACTURE = "FRACTURE"  # 0.85+      Commit unavoidable, form uncertain

SPF_THRESHOLDS = {
    SPFZone.LATENT:   (0.0,  0.3),
    SPFZone.ACTIVE:   (0.3,  0.6),
    SPFZone.CRITICAL: (0.6,  0.85),
    SPFZone.FRACTURE: (0.85, 1.0),
}

class CommitForm(str, Enum):
    CLEAN      = "CLEAN"       # One trajectory dominates cleanly
    CONTESTED  = "CONTESTED"   # Commits under pressure with low support
    FRACTURE   = "FRACTURE"    # Multiple trajectories commit in parallel
    DISSOLVED  = "DISSOLVED"   # All trajectories lose momentum

def _ts() -> str:
    return datetime.now(timezone.utc).isoformat()

def _sid() -> str:
    return hashlib.sha256(f"{time.time_ns()}".encode()).hexdigest()[:12]


# ── Data Classes ──────────────────────────────────────────────────────────────

@dataclass
class PressureSignal:
    signal_type: str       # semantic_drift | epistemic_conflict | authority_ambiguity | temporal | stakes
    value: float           # 0.0 – 1.0
    weight: float          # contribution weight
    description: str
    detected_at: str = field(default_factory=_ts)


@dataclass
class Trajectory:
    id: str = field(default_factory=_sid)
    summary: str = ""
    support_score: float = 0.0       # 0.0 – 1.0
    authority_score: float = 0.0     # 0.0 – 1.0, who is backing this
    momentum: float = 0.0            # rate of support change per day
    evidence_chain: List[str] = field(default_factory=list)  # receipt IDs
    created_at: str = field(default_factory=_ts)
    last_updated: str = field(default_factory=_ts)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class CCTRecord:
    id: str = field(default_factory=_sid)
    domain: str = ""
    topic: str = ""
    trajectories: List[Trajectory] = field(default_factory=list)
    created_at: str = field(default_factory=_ts)
    resolved_at: Optional[str] = None
    winning_trajectory_id: Optional[str] = None
    commit_form: Optional[str] = None
    spf_at_commit: Optional[float] = None
    scs_at_commit: Optional[float] = None

    def to_dict(self) -> dict:
        d = asdict(self)
        return d


@dataclass
class CostSurface:
    domain: str
    confusion_cost: float = 0.0
    trust_cost: float = 0.0
    coordination_cost: float = 0.0
    time_cost: float = 0.0
    opportunity_cost: float = 0.0
    stakes_multiplier: float = 1.0
    computed_at: str = field(default_factory=_ts)

    @property
    def total(self) -> float:
        base = (
            self.confusion_cost * 0.2 +
            self.trust_cost * 0.2 +
            self.coordination_cost * 0.15 +
            self.time_cost * 0.25 +
            self.opportunity_cost * 0.2
        )
        return min(1.0, base * self.stakes_multiplier)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["total"] = self.total
        return d


@dataclass
class ResolutionPrediction:
    likely_winner_id: Optional[str]
    likely_form: CommitForm
    days_to_commit: Optional[float]  # None = cannot predict
    confidence: float                 # 0.0 – 1.0
    premature_commit_risk: bool
    chronic_provisional_risk: bool
    recommended_action: str


# ── Storage ───────────────────────────────────────────────────────────────────

def _get_pressure_dir() -> Path:
    try:
        from nss.core.storage import ALEXANDRIA_ROOT
        d = ALEXANDRIA_ROOT / "pressure"
    except Exception:
        d = Path("/Volumes/NSExternal/ALEXANDRIA/pressure")
    d.mkdir(parents=True, exist_ok=True)
    return d


class _PressureStore:
    """Simple JSON file store for pressure state. One file per domain."""

    def __init__(self):
        self._dir = _get_pressure_dir()

    def _path(self, domain: str) -> Path:
        safe = domain.replace("/", "_").replace(" ", "_")
        return self._dir / f"{safe}.json"

    def load(self, domain: str) -> dict:
        p = self._path(domain)
        if p.exists():
            try:
                return json.loads(p.read_text())
            except Exception:
                return {}
        return {}

    def save(self, domain: str, data: dict) -> None:
        p = self._path(domain)
        p.write_text(json.dumps(data, indent=2))

    def list_domains(self) -> List[str]:
        return [
            f.stem.replace("_", " ")
            for f in self._dir.glob("*.json")
            if not f.stem.startswith("_")
        ]


# ── StabilizationPressureField ─────────────────────────────────────────────

class StabilizationPressureField:
    """
    Tracks and computes SPF for each domain.
    SPF is the leading indicator of commit events.
    """

    def __init__(self, store: Optional[_PressureStore] = None):
        self._store = store or _PressureStore()
        self._signals: Dict[str, List[PressureSignal]] = {}

    def _get_state(self, domain: str) -> dict:
        state = self._store.load(domain)
        if "spf_signals" not in state:
            state["spf_signals"] = []
            state["spf_history"] = []
            state["current_zone"] = SPFZone.LATENT
            state["current_value"] = 0.0
        return state

    def add_signal(self, domain: str, signal: PressureSignal) -> None:
        """Add a pressure signal to a domain."""
        state = self._get_state(domain)
        state["spf_signals"].append(asdict(signal))
        # Keep only last 50 signals
        state["spf_signals"] = state["spf_signals"][-50:]
        self._store.save(domain, state)

    def compute_spf(self, domain: str) -> float:
        """
        Compute current SPF for a domain.
        Weighted sum of recent signals, time-decayed.
        """
        state = self._get_state(domain)
        signals = state.get("spf_signals", [])
        if not signals:
            return 0.0

        now = time.time()
        total_weighted = 0.0
        total_weight = 0.0

        for sig in signals[-20:]:  # last 20 signals
            # Time decay: signals older than 7 days lose 50% weight
            try:
                sig_time = datetime.fromisoformat(sig["detected_at"]).timestamp()
            except Exception:
                sig_time = now
            age_days = (now - sig_time) / 86400
            decay = max(0.1, 1.0 - (age_days / 14))  # halves every 7 days
            weight = sig.get("weight", 0.2) * decay
            total_weighted += sig.get("value", 0.0) * weight
            total_weight += weight

        if total_weight == 0:
            return 0.0

        spf = min(1.0, total_weighted / total_weight)

        # Update stored state
        prev_zone = state.get("current_zone", SPFZone.LATENT)
        new_zone = get_spf_zone(spf)
        state["current_value"] = spf
        state["current_zone"] = new_zone
        state["spf_history"].append({
            "value": spf,
            "zone": new_zone,
            "ts": _ts()
        })
        state["spf_history"] = state["spf_history"][-100:]
        self._store.save(domain, state)

        return spf

    def get_zone(self, domain: str) -> SPFZone:
        state = self._get_state(domain)
        return SPFZone(state.get("current_zone", SPFZone.LATENT))

    def get_pressure_signals(self, domain: str) -> List[dict]:
        state = self._get_state(domain)
        return state.get("spf_signals", [])[-10:]

    def record_from_arbiter(self, domain: str, disagreement_score: float,
                             topic: str = "") -> None:
        """
        Called by arbiter after each route() call.
        High disagreement_score contributes to SPF.
        """
        if disagreement_score > 0.2:
            sig = PressureSignal(
                signal_type="epistemic_conflict",
                value=min(1.0, disagreement_score * 1.5),
                weight=0.25,
                description=f"Arbiter disagreement on: {topic[:80]}"
            )
            self.add_signal(domain, sig)

    def record_cycle(self, domain: str, cycle_count: int) -> None:
        """Called when SFE detects a semantic cycle."""
        sig = PressureSignal(
            signal_type="semantic_drift",
            value=min(1.0, cycle_count * 0.15),
            weight=0.2,
            description=f"Semantic cycle depth: {cycle_count}"
        )
        self.add_signal(domain, sig)

    def record_time_pressure(self, domain: str, days_since_commit: float,
                              stakes: float = 1.0) -> None:
        """Called periodically to record temporal pressure."""
        # Pressure grows: 30 days → 0.3, 60 days → 0.5, 90 days → 0.8
        time_value = min(1.0, days_since_commit / 120)
        sig = PressureSignal(
            signal_type="temporal",
            value=time_value,
            weight=0.25 * stakes,
            description=f"{days_since_commit:.0f} days since last commit"
        )
        self.add_signal(domain, sig)

    def get_all_domains_summary(self) -> List[dict]:
        """Returns pressure summary for all known domains."""
        domains = self._store.list_domains()
        results = []
        for domain in domains:
            spf = self.compute_spf(domain)
            zone = get_spf_zone(spf)
            state = self._get_state(domain)
            results.append({
                "domain": domain,
                "spf": round(spf, 3),
                "zone": zone,
                "signal_count": len(state.get("spf_signals", [])),
            })
        return sorted(results, key=lambda x: x["spf"], reverse=True)

    def reset_domain(self, domain: str, receipt_chain=None) -> None:
        """Called after a clean commit — resets SPF to LATENT."""
        state = self._get_state(domain)
        state["spf_signals"] = []
        state["current_zone"] = SPFZone.LATENT
        state["current_value"] = 0.0
        state["reset_at"] = _ts()
        self._store.save(domain, state)

        if receipt_chain:
            receipt_chain.emit(
                "SPF_RESET",
                {"kind": "pressure", "ref": domain},
                {"domain": domain},
                {"reason": "post_commit_reset"}
            )


def get_spf_zone(value: float) -> SPFZone:
    if value >= 0.85: return SPFZone.FRACTURE
    if value >= 0.60: return SPFZone.CRITICAL
    if value >= 0.30: return SPFZone.ACTIVE
    return SPFZone.LATENT


# ── CompetingCommitTrajectories ────────────────────────────────────────────

class CompetingCommitTrajectories:
    """
    Tracks multiple candidate realities competing for commit authority.
    Trajectories are dynamic (gaining/losing momentum).
    Cycles are structural. Trajectory competition is dynamic. Different thing.
    """

    def __init__(self, store: Optional[_PressureStore] = None):
        self._store = store or _PressureStore()

    def _cct_key(self, domain: str) -> str:
        return f"cct_{domain}"

    def _get_ccts(self, domain: str) -> List[dict]:
        state = self._store.load(self._cct_key(domain))
        return state.get("ccts", [])

    def _save_ccts(self, domain: str, ccts: List[dict]) -> None:
        self._store.save(self._cct_key(domain), {"ccts": ccts, "updated_at": _ts()})

    def get_or_create_cct(self, domain: str, topic: str) -> CCTRecord:
        """Get an existing open CCT for this topic, or create one."""
        ccts = self._get_ccts(domain)
        for c in ccts:
            if c.get("topic") == topic and c.get("resolved_at") is None:
                return self._dict_to_cct(c)

        # Create new
        cct = CCTRecord(domain=domain, topic=topic)
        ccts.append(cct.to_dict())
        self._save_ccts(domain, ccts)
        return cct

    def add_trajectory(self, domain: str, cct_id: str,
                        summary: str, initial_support: float = 0.1,
                        receipt_chain=None) -> Trajectory:
        """Add a new candidate trajectory to a CCT."""
        ccts = self._get_ccts(domain)
        t = Trajectory(summary=summary, support_score=initial_support)

        for c in ccts:
            if c.get("id") == cct_id:
                c.setdefault("trajectories", []).append(t.to_dict())
                break

        self._save_ccts(domain, ccts)

        if receipt_chain:
            receipt_chain.emit(
                "CCT_TRAJECTORY_ADDED",
                {"kind": "pressure", "ref": domain},
                {"cct_id": cct_id, "trajectory_id": t.id, "summary": summary[:100]},
                {"support_score": initial_support}
            )
        return t

    def update_trajectory(self, domain: str, cct_id: str,
                           trajectory_id: str, evidence: dict,
                           support_delta: float = 0.05) -> Optional[CCTRecord]:
        """Update trajectory support based on new evidence."""
        ccts = self._get_ccts(domain)
        for c in ccts:
            if c.get("id") == cct_id:
                for t in c.get("trajectories", []):
                    if t.get("id") == trajectory_id:
                        old_support = t.get("support_score", 0.0)
                        new_support = max(0.0, min(1.0, old_support + support_delta))
                        t["support_score"] = new_support
                        t["momentum"] = support_delta  # simplification
                        t["evidence_chain"].append(evidence.get("receipt_id", _sid()))
                        t["last_updated"] = _ts()
                        break
                break

        self._save_ccts(domain, ccts)
        return self.get_cct(domain, cct_id)

    def get_cct(self, domain: str, cct_id: str) -> Optional[CCTRecord]:
        for c in self._get_ccts(domain):
            if c.get("id") == cct_id:
                return self._dict_to_cct(c)
        return None

    def get_active_ccts(self, domain: str) -> List[CCTRecord]:
        return [
            self._dict_to_cct(c)
            for c in self._get_ccts(domain)
            if c.get("resolved_at") is None
        ]

    def predict_resolution(self, domain: str, cct_id: str) -> ResolutionPrediction:
        """Predict how and when a CCT will resolve."""
        cct = self.get_cct(domain, cct_id)
        if not cct or not cct.trajectories:
            return ResolutionPrediction(
                likely_winner_id=None,
                likely_form=CommitForm.DISSOLVED,
                days_to_commit=None,
                confidence=0.1,
                premature_commit_risk=False,
                chronic_provisional_risk=True,
                recommended_action="No active trajectories. Domain may dissolve."
            )

        # Sort by support score
        sorted_t = sorted(cct.trajectories, key=lambda t: t.support_score, reverse=True)
        top = sorted_t[0]
        second = sorted_t[1] if len(sorted_t) > 1 else None

        # Determine likely form
        if top.support_score > 0.7 and top.authority_score > 0.5:
            form = CommitForm.CLEAN
            confidence = 0.8
        elif top.support_score > 0.5:
            form = CommitForm.CLEAN
            confidence = 0.6
        elif second and (top.support_score - second.support_score) < 0.1:
            form = CommitForm.FRACTURE
            confidence = 0.65
        else:
            form = CommitForm.CONTESTED
            confidence = 0.5

        # Estimate days to commit (rough: each 0.1 support increase takes ~2 days)
        support_needed = max(0.0, 0.7 - top.support_score)
        momentum = max(0.01, top.momentum) if top.momentum > 0 else 0.01
        days = (support_needed / momentum) * 2 if momentum > 0 else None

        # Premature commit risk: SCS rising faster than SPF-based timeline
        premature_risk = top.momentum < 0.02 and top.support_score > 0.4

        # Chronic provisional: no trajectory has meaningful momentum
        chronic_risk = all(t.momentum < 0.01 for t in cct.trajectories)

        if form == CommitForm.CLEAN:
            action = f"Support trajectory '{top.summary[:50]}'. Prepare governance for commit in ~{int(days or 10)} days."
        elif form == CommitForm.FRACTURE:
            action = "URGENT: Two trajectories within 0.1 support. Governance must intervene to prevent fracture."
        elif form == CommitForm.CONTESTED:
            action = "Contested commit likely. Review authority scores. Consider requesting more evidence."
        else:
            action = "No dominant trajectory. Consider dissolving CCT and reframing the domain."

        return ResolutionPrediction(
            likely_winner_id=top.id,
            likely_form=form,
            days_to_commit=days,
            confidence=confidence,
            premature_commit_risk=premature_risk,
            chronic_provisional_risk=chronic_risk,
            recommended_action=action
        )

    def commit_trajectory(self, domain: str, cct_id: str,
                           winning_trajectory_id: str,
                           spf_at_commit: float = 0.0,
                           scs_at_commit: float = 0.0,
                           receipt_chain=None) -> Optional[CCTRecord]:
        """Commit one trajectory as the winner. Archives others."""
        ccts = self._get_ccts(domain)
        for c in ccts:
            if c.get("id") == cct_id:
                traj = [t for t in c.get("trajectories", [])
                        if t.get("id") == winning_trajectory_id]
                if not traj:
                    return None

                support = traj[0].get("support_score", 0.0)
                if support < 0.5:
                    form = CommitForm.CONTESTED
                else:
                    form = CommitForm.CLEAN

                c["resolved_at"] = _ts()
                c["winning_trajectory_id"] = winning_trajectory_id
                c["commit_form"] = form
                c["spf_at_commit"] = spf_at_commit
                c["scs_at_commit"] = scs_at_commit
                break

        self._save_ccts(domain, ccts)

        if receipt_chain:
            receipt_chain.emit(
                "CCT_COMMITTED",
                {"kind": "pressure", "ref": domain},
                {"cct_id": cct_id, "winning_trajectory_id": winning_trajectory_id},
                {"commit_form": form, "spf_at_commit": spf_at_commit,
                 "scs_at_commit": scs_at_commit}
            )
        return self.get_cct(domain, cct_id)

    def detect_fracture(self, domain: str, cct_id: str) -> bool:
        """True if multiple trajectories are within 0.1 support with high SPF."""
        cct = self.get_cct(domain, cct_id)
        if not cct or len(cct.trajectories) < 2:
            return False
        sorted_t = sorted(cct.trajectories, key=lambda t: t.support_score, reverse=True)
        return (sorted_t[0].support_score - sorted_t[1].support_score) < 0.1 \
            and sorted_t[1].support_score > 0.3

    def _dict_to_cct(self, d: dict) -> CCTRecord:
        trajs = [Trajectory(**{
            k: v for k, v in t.items() if k in Trajectory.__dataclass_fields__
        }) for t in d.get("trajectories", [])]
        return CCTRecord(
            id=d.get("id", _sid()),
            domain=d.get("domain", ""),
            topic=d.get("topic", ""),
            trajectories=trajs,
            created_at=d.get("created_at", _ts()),
            resolved_at=d.get("resolved_at"),
            winning_trajectory_id=d.get("winning_trajectory_id"),
            commit_form=d.get("commit_form"),
            spf_at_commit=d.get("spf_at_commit"),
            scs_at_commit=d.get("scs_at_commit"),
        )


# ── StabilizationCostSurface ───────────────────────────────────────────────

class StabilizationCostSurface:
    """
    Models the cost of remaining provisional vs. committing.
    Determines when governance must act to prevent premature commits or fractures.

    Without SCS, timing logic is permanently incomplete.
    """

    def __init__(self, store: Optional[_PressureStore] = None):
        self._store = store or _PressureStore()

    def _scs_key(self, domain: str) -> str:
        return f"scs_{domain}"

    def compute_scs(self, domain: str,
                    days_provisional: float = 0.0,
                    active_cct_count: int = 0,
                    stakes_level: float = 1.0,
                    receipt_chain=None) -> CostSurface:
        """
        Compute the Stabilization Cost Surface for a domain.

        Args:
            domain: Which domain to compute for
            days_provisional: How long since last commit
            active_cct_count: Number of competing trajectories active
            stakes_level: Consequence weight (1.0 = normal, 2.0+ = high-stakes)
        """
        # Confusion cost: rises with active CCTs (people don't know what's true)
        confusion_cost = min(1.0, active_cct_count * 0.15)

        # Trust cost: rises slowly then accelerates after 30 days provisional
        trust_cost = min(1.0, (days_provisional / 90) ** 1.5)

        # Coordination cost: rises with CCT count AND time
        coordination_cost = min(1.0, (active_cct_count * 0.1) + (days_provisional / 120))

        # Time cost: linear rise, primary driver in most domains
        time_cost = min(1.0, days_provisional / 60)

        # Opportunity cost: accelerates after 14 days (window closing)
        opportunity_cost = min(1.0, max(0.0, (days_provisional - 14) / 60))

        scs = CostSurface(
            domain=domain,
            confusion_cost=round(confusion_cost, 3),
            trust_cost=round(trust_cost, 3),
            coordination_cost=round(coordination_cost, 3),
            time_cost=round(time_cost, 3),
            opportunity_cost=round(opportunity_cost, 3),
            stakes_multiplier=stakes_level,
        )

        # Save
        state = {"current": scs.to_dict(), "history": []}
        prev = self._store.load(self._scs_key(domain))
        history = prev.get("history", [])
        history.append(scs.to_dict())
        state["history"] = history[-50:]
        self._store.save(self._scs_key(domain), state)

        # Emit receipt on threshold crossing
        if receipt_chain and scs.total > 0.7:
            receipt_chain.emit(
                "SCS_THRESHOLD_CROSSED",
                {"kind": "pressure", "ref": domain},
                {"domain": domain, "days_provisional": days_provisional},
                {"total": scs.total, "threshold": 0.7}
            )

        return scs

    def days_to_governance_action(self, scs: CostSurface) -> Optional[int]:
        """
        Estimate days remaining before governance must act.
        Returns None if action is immediate.
        """
        if scs.total > 0.85:
            return None  # Act now
        if scs.total > 0.7:
            return 3
        if scs.total > 0.5:
            return int((0.7 - scs.total) / 0.015)  # ~13 days from 0.5 to 0.7
        return None  # Not urgent

    def detect_premature_commit_risk(self, domain: str, scs: CostSurface,
                                      spf_value: float) -> bool:
        """
        Premature commit risk: time_cost OR opportunity_cost spikes
        while trust_cost and confusion_cost are still manageable.
        Creates a local minimum that feels like resolution but isn't.
        """
        time_driven = scs.time_cost > 0.6 or scs.opportunity_cost > 0.6
        underlying_unresolved = scs.confusion_cost < 0.4 and scs.trust_cost < 0.4
        spf_still_active = spf_value > 0.3
        return time_driven and underlying_unresolved and spf_still_active

    def detect_chronic_provisional(self, domain: str, scs: CostSurface) -> bool:
        """
        Chronic provisional: cost of remaining provisional is tolerable.
        SPF rises but SCS stays low. No commit occurs.
        """
        return scs.total < 0.3 and scs.time_cost > 0.4

    def get_governance_recommendation(self, scs: CostSurface, spf_value: float,
                                       spf_zone: SPFZone,
                                       premature_risk: bool) -> str:
        total = scs.total
        if spf_zone == SPFZone.FRACTURE:
            return "EMERGENCY: Fracture-level pressure. Convene founder immediately."
        if spf_zone == SPFZone.CRITICAL and total > 0.7:
            return "URGENT: Governance must act within 3 days. SCS and SPF both critical."
        if premature_risk:
            return "WARNING: Premature commit risk detected. Time pressure high but underlying tension unresolved. Do not commit yet."
        if total > 0.5:
            days = self.days_to_governance_action(scs)
            return f"Surface to Sentinel. Governance action recommended within {days} days."
        if self.detect_chronic_provisional("", scs):
            return "ALERT: Chronic provisional state. Domain may never resolve without intervention."
        return "Monitor. No immediate action required."


# ── StabilizationEngine (Orchestrator) ────────────────────────────────────

class StabilizationEngine:
    """
    Orchestrates SPF, CCT, and SCS together.
    This is what boots at startup and what the server calls.
    """

    def __init__(self, receipt_chain=None):
        self._store = _PressureStore()
        self.spf = StabilizationPressureField(self._store)
        self.cct = CompetingCommitTrajectories(self._store)
        self.scs = StabilizationCostSurface(self._store)
        self._receipt_chain = receipt_chain

    def process_arbiter_result(self, domain: str, topic: str,
                                disagreement_score: float,
                                result_metadata: dict = None) -> dict:
        """
        Called after every arbiter.route() call.
        Updates SPF, potentially creates/updates CCT.
        Returns stabilization context to append to arbiter response.
        """
        # Update SPF
        self.spf.record_from_arbiter(domain, disagreement_score, topic)
        spf_value = self.spf.compute_spf(domain)
        spf_zone = get_spf_zone(spf_value)

        context = {
            "spf_value": round(spf_value, 3),
            "spf_zone": spf_zone,
            "action_required": spf_zone in (SPFZone.CRITICAL, SPFZone.FRACTURE),
        }

        # If disagreement is high, create/update CCT
        if disagreement_score > 0.4:
            cct = self.cct.get_or_create_cct(domain, topic)
            context["active_cct_id"] = cct.id
            context["active_trajectories"] = len(cct.trajectories)

            if self._receipt_chain and spf_zone == SPFZone.CRITICAL:
                self._receipt_chain.emit(
                    "SPF_ZONE_CRITICAL",
                    {"kind": "pressure", "ref": domain},
                    {"domain": domain, "topic": topic},
                    {"spf_value": spf_value, "disagreement_score": disagreement_score}
                )

        return context

    def get_domain_dashboard(self, domain: str,
                              days_provisional: float = 0,
                              active_cct_count: int = 0,
                              stakes_level: float = 1.0) -> dict:
        """
        Full stabilization status for one domain.
        Used by the console pressure dashboard.
        """
        spf_value = self.spf.compute_spf(domain)
        spf_zone = get_spf_zone(spf_value)
        scs = self.scs.compute_scs(domain, days_provisional, active_cct_count,
                                    stakes_level, self._receipt_chain)
        active_ccts = self.cct.get_active_ccts(domain)
        premature_risk = self.scs.detect_premature_commit_risk(domain, scs, spf_value)
        chronic_risk = self.scs.detect_chronic_provisional(domain, scs)
        recommendation = self.scs.get_governance_recommendation(
            scs, spf_value, spf_zone, premature_risk)

        predictions = []
        for cct in active_ccts:
            pred = self.cct.predict_resolution(domain, cct.id)
            predictions.append({
                "cct_id": cct.id,
                "topic": cct.topic,
                "trajectory_count": len(cct.trajectories),
                "likely_form": pred.likely_form,
                "days_to_commit": pred.days_to_commit,
                "confidence": pred.confidence,
                "premature_risk": pred.premature_commit_risk,
                "recommended_action": pred.recommended_action,
            })

        return {
            "domain": domain,
            "spf": {"value": round(spf_value, 3), "zone": spf_zone},
            "scs": scs.to_dict(),
            "active_ccts": len(active_ccts),
            "predictions": predictions,
            "governance": {
                "recommendation": recommendation,
                "premature_commit_risk": premature_risk,
                "chronic_provisional_risk": chronic_risk,
                "days_to_action": self.scs.days_to_governance_action(scs),
            }
        }

    def get_all_domains_overview(self) -> List[dict]:
        return self.spf.get_all_domains_summary()

    def post_commit_reset(self, domain: str, winning_summary: str = "") -> None:
        """Call after a clean commit to reset pressure for a domain."""
        self.spf.reset_domain(domain, self._receipt_chain)
        if self._receipt_chain:
            self._receipt_chain.emit(
                "DOMAIN_COMMITTED",
                {"kind": "pressure", "ref": domain},
                {"domain": domain},
                {"winning_summary": winning_summary[:200]}
            )


# ── Module-level singleton ─────────────────────────────────────────────────

_engine: Optional[StabilizationEngine] = None

def get_stabilization_engine(receipt_chain=None) -> StabilizationEngine:
    global _engine
    if _engine is None:
        _engine = StabilizationEngine(receipt_chain=receipt_chain)
    elif receipt_chain and _engine._receipt_chain is None:
        _engine._receipt_chain = receipt_chain
    return _engine
