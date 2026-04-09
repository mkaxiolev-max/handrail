from __future__ import annotations
from .models import HyperObject

PROJECTION_CONTRACTS: dict[str, list[str]] = {
    "ns:internal":           ["epistemic", "identity", "memory", "execution", "temporal"],
    "handrail:exec":         ["execution", "policy", "sensitivity", "exposure", "temporal"],
    "alexandria:ingest":     ["memory", "sensitivity", "temporal"],
    "alexandria:retrieve":   ["memory", "epistemic", "temporal", "sensitivity"],
    "storytime:user":        ["narrative", "temporal", "exposure"],
    "storytime:audit":       ["*"],
    "storytime:developer":   ["*"],
    "adapter:task":          ["execution"],
    "ns:arbiter":            ["epistemic", "narrative", "policy"],
    "ns:evidence_role":      ["epistemic", "memory"],
    "ns:counter_role":       ["epistemic"],
    "ns:narrative_role":     ["narrative", "epistemic"],
}

PROJECTION_DENIALS: dict[str, list[str]] = {
    "storytime:user":    ["sensitivity", "policy", "exposure"],
    "adapter:task":      ["epistemic", "sensitivity", "narrative", "policy"],
    "alexandria:retrieve": ["execution", "policy"],
}

class ProjectionViolationError(Exception):
    pass

class ProjectionService:
    def project(self, obj: HyperObject, projection_name: str) -> dict:
        if projection_name not in PROJECTION_CONTRACTS:
            raise ProjectionViolationError(f"Unknown projection: {projection_name}")
        allowed = PROJECTION_CONTRACTS[projection_name]
        denied = PROJECTION_DENIALS.get(projection_name, [])
        if "*" in allowed:
            return obj.model_dump()
        obj_dict = obj.model_dump()
        result = {"id": obj.id, "version": obj.version, "projection": projection_name}
        for axis in allowed:
            if axis in denied:
                raise ProjectionViolationError(f"axis '{axis}' in both allowed and denied")
            if axis in obj_dict:
                result[axis] = obj_dict[axis]
        for denied_axis in denied:
            if denied_axis in result:
                raise ProjectionViolationError(
                    f"PROJECTION LEAK: '{denied_axis}' in '{projection_name}' output")
        return result

    def verify_no_leak(self, projection_output: dict, projection_name: str) -> bool:
        denied = PROJECTION_DENIALS.get(projection_name, [])
        return not any(d in projection_output for d in denied)

_projector = ProjectionService()
def get_projector() -> ProjectionService:
    return _projector
