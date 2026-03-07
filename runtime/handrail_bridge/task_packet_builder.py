from __future__ import annotations

from typing import Any, Dict

from runtime.state.schemas import OperatingFrame


def build_execution_packet(operating_frame: OperatingFrame, objective: str) -> Dict[str, Any]:
    return {
        "task_id": operating_frame.run_id + ":boot_bundle_diff",
        "mission_mode": operating_frame.mission_mode,
        "objective": objective,
        "action_intent": "inspect runtime, collect health, compare current run artifacts, produce bounded execution output",
        "operating_frame_run_id": operating_frame.run_id,
        "hard_constraints": operating_frame.hard_constraints,
        "allowed_action_bands": operating_frame.allowed_actions,
        "verification_policy": {
            "pre_exec_checks": True,
            "post_exec_checks": True,
            "rollback_required": False,
        },
        "risk_class": "low" if operating_frame.instability_score < 0.3 else "medium",
        "instability_score": operating_frame.instability_score,
        "contradiction_flags": operating_frame.contradiction_flags,
        "expected_outputs": [
            "runtime_snapshot",
            "health_summary",
            "artifact_diff_stub",
        ],
    }
