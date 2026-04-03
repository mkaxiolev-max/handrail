"""Policy Evolution Layer — safe, versioned, quorum-gated policy change."""
from __future__ import annotations
import json
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

# ── Storage root ──────────────────────────────────────────────────────────────
def _root() -> Path:
    ssd = Path("/Volumes/NSExternal/ALEXANDRIA/policy")
    if ssd.parent.parent.exists():
        return ssd
    return Path.home() / ".axiolev" / "policy"

def _proposals_dir() -> Path:
    d = _root() / "proposals"
    d.mkdir(parents=True, exist_ok=True)
    return d

def _versions_dir() -> Path:
    d = _root() / "versions"
    d.mkdir(parents=True, exist_ok=True)
    return d

def _audit_path() -> Path:
    _root().mkdir(parents=True, exist_ok=True)
    return _root() / "audit.jsonl"

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

# ── Quorum rules ─────────────────────────────────────────────────────────────
QUORUM_RULES = {
    "R0": {"votes_required": 1, "wait_hours": 0,  "yubikey": False},
    "R1": {"votes_required": 1, "wait_hours": 0,  "yubikey": False},
    "R2": {"votes_required": 1, "wait_hours": 24, "yubikey": False},
    "R3": {"votes_required": 2, "wait_hours": 0,  "yubikey": True},
    "R4": {"votes_required": 2, "wait_hours": 0,  "yubikey": True},
}

# ── Engine ────────────────────────────────────────────────────────────────────
class PolicyEvolutionEngine:
    """Proposal → Vote → Activate → Rollback lifecycle for policy definitions."""

    def _write_proposal(self, p: dict) -> None:
        (_proposals_dir() / f"{p['id']}.json").write_text(json.dumps(p, indent=2))

    def _read_proposal(self, proposal_id: str) -> Optional[dict]:
        path = _proposals_dir() / f"{proposal_id}.json"
        if not path.exists():
            return None
        return json.loads(path.read_text())

    def _write_version(self, v: dict) -> None:
        name = v["policy_name"].replace("/", "_")
        (_versions_dir() / f"{name}_v{v['version']}.json").write_text(json.dumps(v, indent=2))

    def _active_version(self, policy_name: str) -> Optional[dict]:
        name = policy_name.replace("/", "_")
        candidates = sorted((_versions_dir()).glob(f"{name}_v*.json"))
        if not candidates:
            return None
        versions = [json.loads(p.read_text()) for p in candidates]
        active = [v for v in versions if v.get("superseded_by") is None]
        if not active:
            return None
        return sorted(active, key=lambda v: v["version"])[-1]

    def _append_audit(self, entry: dict) -> None:
        with open(_audit_path(), "a") as f:
            f.write(json.dumps(entry) + "\n")

    # ── Public API ────────────────────────────────────────────────────────────

    def submit_proposal(self, title: str, description: str, proposer: str,
                        risk_tier: str) -> dict:
        risk_tier = risk_tier.upper()
        if risk_tier not in QUORUM_RULES:
            raise ValueError(f"Invalid risk_tier: {risk_tier}")
        rules = QUORUM_RULES[risk_tier]
        proposal = {
            "id": str(uuid.uuid4()),
            "title": title,
            "description": description,
            "proposer": proposer,
            "risk_tier": risk_tier,
            "status": "open",
            "created_at": _now(),
            "votes_for": [],
            "votes_against": [],
            "quorum_required": rules["votes_required"],
            "wait_hours": rules["wait_hours"],
            "yubikey_required": rules["yubikey"],
        }
        self._write_proposal(proposal)
        self._append_audit({
            "id": str(uuid.uuid4()),
            "policy_name": title,
            "action": "proposal_submitted",
            "actor": proposer,
            "from_version": None,
            "to_version": None,
            "ts": _now(),
        })
        return proposal

    def vote(self, proposal_id: str, actor: str, vote: bool) -> dict:
        p = self._read_proposal(proposal_id)
        if p is None:
            return {"ok": False, "error": "proposal not found"}
        if p["status"] != "open":
            return {"ok": False, "error": f"proposal is {p['status']}"}
        if vote:
            if actor not in p["votes_for"]:
                p["votes_for"].append(actor)
            if actor in p["votes_against"]:
                p["votes_against"].remove(actor)
        else:
            if actor not in p["votes_against"]:
                p["votes_against"].append(actor)
            if actor in p["votes_for"]:
                p["votes_for"].remove(actor)
        quorum_met = len(p["votes_for"]) >= p["quorum_required"]
        # Check wait period
        wait_ok = True
        if p["wait_hours"] > 0:
            created = datetime.fromisoformat(p["created_at"])
            elapsed = datetime.now(timezone.utc) - created
            wait_ok = elapsed >= timedelta(hours=p["wait_hours"])
        p["quorum_met"] = quorum_met and wait_ok
        self._write_proposal(p)
        self._append_audit({
            "id": str(uuid.uuid4()),
            "policy_name": p["title"],
            "action": f"vote_{'for' if vote else 'against'}",
            "actor": actor,
            "from_version": None,
            "to_version": None,
            "ts": _now(),
        })
        return {
            "ok": True,
            "votes_for": len(p["votes_for"]),
            "votes_against": len(p["votes_against"]),
            "quorum_met": p.get("quorum_met", False),
            "wait_ok": wait_ok,
        }

    def activate(self, proposal_id: str, actor: str,
                 yubikey_verified: bool = False) -> dict:
        p = self._read_proposal(proposal_id)
        if p is None:
            return {"ok": False, "error": "proposal not found"}
        if p["status"] != "open":
            return {"ok": False, "error": f"proposal already {p['status']}"}
        if actor not in ["founder"]:
            return {"ok": False, "error": "only founder may activate"}
        quorum_met = len(p["votes_for"]) >= p["quorum_required"]
        if not quorum_met:
            return {"ok": False, "error": "quorum not met"}
        if p.get("yubikey_required") and not yubikey_verified:
            return {"ok": False, "error": "YubiKey verification required for this risk tier"}
        if p["wait_hours"] > 0:
            created = datetime.fromisoformat(p["created_at"])
            elapsed = datetime.now(timezone.utc) - created
            if elapsed < timedelta(hours=p["wait_hours"]):
                remaining = p["wait_hours"] - elapsed.total_seconds() / 3600
                return {"ok": False, "error": f"wait period: {remaining:.1f}h remaining"}

        # Determine next version number
        policy_name = p["title"]
        name = policy_name.replace("/", "_")
        existing = sorted(_versions_dir().glob(f"{name}_v*.json"))
        next_ver = len(existing) + 1

        version = {
            "id": str(uuid.uuid4()),
            "policy_name": policy_name,
            "version": next_ver,
            "content": {"description": p["description"], "proposal_id": proposal_id,
                        "risk_tier": p["risk_tier"]},
            "activated_at": _now(),
            "superseded_by": None,
            "rollback_available": next_ver > 1,
        }
        self._write_version(version)
        p["status"] = "activated"
        p["activated_version"] = next_ver
        self._write_proposal(p)
        self._append_audit({
            "id": str(uuid.uuid4()),
            "policy_name": policy_name,
            "action": "activated",
            "actor": actor,
            "from_version": next_ver - 1 if next_ver > 1 else None,
            "to_version": next_ver,
            "ts": _now(),
        })
        return {"ok": True, "version": version}

    def rollback(self, policy_name: str, actor: str) -> dict:
        name = policy_name.replace("/", "_")
        versions = sorted(
            [json.loads(p.read_text()) for p in _versions_dir().glob(f"{name}_v*.json")],
            key=lambda v: v["version"]
        )
        active = [v for v in versions if v.get("superseded_by") is None]
        if not active:
            return {"ok": False, "error": "no active version"}
        current = sorted(active, key=lambda v: v["version"])[-1]
        prev_versions = [v for v in versions if v["version"] < current["version"]]
        if not prev_versions:
            return {"ok": False, "error": "no previous version to roll back to"}
        prev = sorted(prev_versions, key=lambda v: v["version"])[-1]
        # Supersede current
        current["superseded_by"] = prev["version"]
        self._write_version(current)
        # Reinstate previous
        prev["superseded_by"] = None
        self._write_version(prev)
        self._append_audit({
            "id": str(uuid.uuid4()),
            "policy_name": policy_name,
            "action": "rollback",
            "actor": actor,
            "from_version": current["version"],
            "to_version": prev["version"],
            "ts": _now(),
        })
        return {"ok": True, "rolled_back_to_version": prev["version"]}

    def get_active_policy(self, policy_name: str) -> Optional[dict]:
        return self._active_version(policy_name)

    def list_proposals(self, status: Optional[str] = None) -> list:
        proposals = []
        for path in _proposals_dir().glob("*.json"):
            try:
                p = json.loads(path.read_text())
                if status is None or p.get("status") == status:
                    proposals.append(p)
            except Exception:
                pass
        return sorted(proposals, key=lambda p: p.get("created_at", ""), reverse=True)

    def audit_log(self, policy_name: str) -> list:
        path = _audit_path()
        if not path.exists():
            return []
        entries = []
        for line in path.read_text().splitlines():
            try:
                e = json.loads(line)
                if e.get("policy_name") == policy_name:
                    entries.append(e)
            except Exception:
                pass
        return entries


# ── Singleton ─────────────────────────────────────────────────────────────────
_engine: Optional[PolicyEvolutionEngine] = None

def get_engine() -> PolicyEvolutionEngine:
    global _engine
    if _engine is None:
        _engine = PolicyEvolutionEngine()
    return _engine
