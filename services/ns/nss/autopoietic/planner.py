"""
NS∞ CapabilityPlanner — Autopoietic Loop Phase 2
=================================================
Reads a normalized ExecutableSpec from Alexandria and produces
a bounded CapabilityPlan for execution through Handrail.

This is the bridge from spec to action.
It never improvises — it reads structured spec objects only.
"""
from __future__ import annotations
import json, uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


SPECS_SSD  = Path("/Volumes/NSExternal/ALEXANDRIA/specs")
SPECS_FALL = Path(".runs/specs")


def _specs_dir() -> Path:
    return SPECS_SSD if SPECS_SSD.exists() else SPECS_FALL


def list_specs() -> list[dict]:
    d = _specs_dir()
    if not d.exists():
        return []
    specs = []
    for f in d.glob("*.json"):
        try:
            s = json.loads(f.read_text())
            specs.append({
                "spec_id":  s.get("spec_id"),
                "name":     s.get("name"),
                "status":   s.get("status"),
                "domain":   s.get("domain"),
                "mutation_tier": s.get("mutation_tier", 2),
            })
        except Exception:
            pass
    return specs


def load_spec(spec_id: str) -> Optional[dict]:
    d = _specs_dir()
    p = d / f"{spec_id}.json"
    if p.exists():
        return json.loads(p.read_text())
    # Try partial match
    for f in d.glob("*.json"):
        if spec_id in f.stem:
            return json.loads(f.read_text())
    return None


def build_plan(spec_id: str) -> dict:
    """
    Build a CapabilityPlan from an ExecutableSpec.
    Returns the plan dict. Does NOT execute — execution
    is done by Handrail after founder review.
    """
    spec = load_spec(spec_id)
    if not spec:
        return {"ok": False, "error": f"spec not found: {spec_id}"}

    tier = spec.get("mutation_tier", 2)
    if tier > 2:
        return {
            "ok": False,
            "error": f"mutation_tier={tier} exceeds Tier 2 limit for autonomous planning",
            "spec_id": spec_id,
        }

    plan_id = str(uuid.uuid4())[:8]
    ts      = datetime.now(timezone.utc).isoformat()

    # Derive CPS ops from build_actions
    cps_ops = []
    for action in spec.get("build_actions", []):
        a = action.lower()
        if "patch" in a:
            cps_ops.append({
                "op": "fs.apply_patch",
                "args": {
                    "target_file":   _extract_target(action),
                    "patch_content": "",    # filled by executor
                    "dry_run":       True,  # safe default
                },
                "description": action,
            })
        elif "test" in a:
            cps_ops.append({
                "op": "fs.run_tests",
                "args": {"test_path": "tests/", "timeout_sec": 30},
                "description": action,
            })
        elif "rebuild" in a or "docker" in a:
            cps_ops.append({
                "op": "http.health_check",
                "args": {"url": "http://localhost:9000/healthz", "expect_status": 200},
                "description": f"verify after: {action}",
            })

    plan = {
        "plan_id":          plan_id,
        "spec_id":          spec_id,
        "name":             spec.get("name"),
        "ts":               ts,
        "status":           "pending_review",
        "mutation_tier":    tier,
        "review_required":  spec.get("review_required", True),
        "target_files":     _extract_targets(spec),
        "acceptance_tests": spec.get("acceptance_tests", []),
        "cps_ops":          cps_ops,
        "max_retries":      spec.get("max_retries", 1),
        "required_artifacts": ["diff.patch", "test_output.txt", "run_summary.json"],
        "rollback":         spec.get("rollback", "git revert HEAD"),
        "constraints":      spec.get("constraints", []),
    }

    # Save plan
    plans_dir = _specs_dir().parent / "plans"
    plans_dir.mkdir(parents=True, exist_ok=True)
    (plans_dir / f"{plan_id}.json").write_text(json.dumps(plan, indent=2))

    return {"ok": True, "plan": plan}


def _extract_target(action: str) -> str:
    """Extract a file path from an action string like 'patch services/ns/nss/ui/founder.py'"""
    words = action.split()
    for w in words:
        if "/" in w and "." in w:
            return w
    return "services/"


def _extract_targets(spec: dict) -> list[str]:
    targets = []
    for action in spec.get("build_actions", []):
        t = _extract_target(action)
        if t and t not in targets:
            targets.append(t)
    return targets


def list_plans() -> list[dict]:
    plans_dir = _specs_dir().parent / "plans"
    if not plans_dir.exists():
        return []
    plans = []
    for f in plans_dir.glob("*.json"):
        try:
            p = json.loads(f.read_text())
            plans.append({
                "plan_id":  p.get("plan_id"),
                "spec_id":  p.get("spec_id"),
                "status":   p.get("status"),
                "ts":       p.get("ts"),
                "mutation_tier": p.get("mutation_tier"),
            })
        except Exception:
            pass
    return sorted(plans, key=lambda x: x.get("ts",""), reverse=True)
