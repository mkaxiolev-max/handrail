"""
Handrail CPS OP_DISPATCH Handler for Mac Adapter
AXIOLEV Holdings LLC © 2026 | V1 FROZEN
All embodiment operations traverse this gate.
Policy: permissions checked BEFORE dispatch. Artifacts MUST be under .run/<run_id>/adapter/
"""
import asyncio, httpx, hashlib, json
from typing import Dict, Any
from datetime import datetime, timezone


class MacAdapterHandler:
    """
    Mediates NS∞ → Handrail → Mac Adapter → macOS
    Enforces: permission pre-check, timeout normalization, artifact discipline, receipt chain
    """
    ADAPTER_URL = "http://localhost:8765"
    ADAPTER_TIMEOUT = 5.0

    # Operations requiring permission pre-check
    MUTABLE_OPS = {"env.focus_window", "env.open_app", "env.open_url"}
    PERMISSION_MAP = {
        "env.focus_window": ["screen_recording", "accessibility"],
        "env.open_app":     ["open"],
        "env.open_url":     ["open"],
    }

    async def dispatch(self, operation: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle MAC_ADAPTER_CALL from Handrail CPS.
        Returns normalized AdapterResult-compatible dict with receipt.
        """
        adapter_method = operation.get("adapter_method", "")
        adapter_params = operation.get("adapter_params", {})
        run_id         = operation.get("run_id", "unknown")
        escalation_ok  = operation.get("escalation_confirmed", False)

        # Pre-check: permission gate for mutable operations
        if adapter_method in self.MUTABLE_OPS:
            if not escalation_ok:
                return self._denied_result(run_id, adapter_method,
                    "escalation_confirmed=true required for mutable operations")
            health = await self._call_adapter("health", {})
            perms = health.get("permission_state", {})
            required = self.PERMISSION_MAP.get(adapter_method, [])
            for perm in required:
                if perms.get(perm) != "granted":
                    return self._permission_denied_result(run_id, adapter_method, perm)

        # Dispatch with timeout
        try:
            result = await asyncio.wait_for(
                self._call_adapter(adapter_method, adapter_params),
                timeout=self.ADAPTER_TIMEOUT
            )
        except asyncio.TimeoutError:
            return self._timeout_result(run_id, adapter_method)
        except Exception as exc:
            return self._error_result(run_id, adapter_method, str(exc))

        # Post-call: artifact discipline enforcement
        for artifact in result.get("artifacts", []):
            if not str(artifact).startswith(f".run/{run_id}/adapter/"):
                return self._artifact_violation_result(run_id, artifact)

        # Ensure receipt is present
        if "receipt" not in result:
            result["receipt"] = self._make_receipt(run_id, adapter_method)

        return result

    async def _call_adapter(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        # Normalize method path: env.focus_window → /env/focus_window
        path = "/" + method.replace(".", "/")
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.ADAPTER_URL}{path}",
                json=params,
                timeout=self.ADAPTER_TIMEOUT
            )
            if response.status_code == 200:
                return response.json()
            return {"ok": False, "rc": response.status_code, "failure_reason": f"HTTP {response.status_code}"}

    def _make_receipt(self, run_id: str, method: str) -> Dict[str, Any]:
        payload = f"{run_id}:{method}:{datetime.now(timezone.utc).isoformat()}"
        return {
            "task_id": hashlib.sha256(payload.encode()).hexdigest(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "run_id": run_id,
            "checksum": hashlib.sha256(payload.encode()).hexdigest(),
            "adapter_method": method
        }

    def _denied_result(self, run_id, method, reason):
        return {"ok": False, "rc": 403, "failure_reason": reason,
                "checks": {}, "state_change": {"type": "none"},
                "receipt": self._make_receipt(run_id, method), "artifacts": []}

    def _permission_denied_result(self, run_id, method, perm):
        return {"ok": False, "rc": 403,
                "failure_reason": f"Permission '{perm}' not granted. Grant in System Preferences > Security.",
                "checks": {"permission_sufficient": False},
                "state_change": {"type": "none"},
                "receipt": self._make_receipt(run_id, method), "artifacts": []}

    def _timeout_result(self, run_id, method):
        return {"ok": False, "rc": 124,
                "failure_reason": f"Adapter timeout (>{self.ADAPTER_TIMEOUT}s)",
                "checks": {"capability_available": False},
                "state_change": {"type": "none"},
                "receipt": self._make_receipt(run_id, method), "artifacts": []}

    def _error_result(self, run_id, method, error):
        return {"ok": False, "rc": 1, "failure_reason": error,
                "checks": {"capability_available": False},
                "state_change": {"type": "none"},
                "receipt": self._make_receipt(run_id, method), "artifacts": []}

    def _artifact_violation_result(self, run_id, artifact):
        return {"ok": False, "rc": 1,
                "failure_reason": f"SECURITY: artifact written outside run dir: {artifact}",
                "checks": {}, "state_change": {"type": "none"},
                "receipt": self._make_receipt(run_id, "artifact_discipline_violation"), "artifacts": []}
