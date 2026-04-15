"""
Integration test: Handrail ↔ Mac Adapter
AXIOLEV Holdings LLC © 2026
Tests: permission gate, timeout handling, artifact discipline, receipt chain
"""
import asyncio, pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from services.handrail.handlers.mac_adapter_handler import MacAdapterHandler

@pytest.mark.asyncio
async def test_health_call_returns_receipt():
    handler = MacAdapterHandler()
    result = await handler.dispatch({
        "op_type": "MAC_ADAPTER_CALL",
        "adapter_method": "env.health",
        "adapter_params": {},
        "run_id": "test_run_001",
        "policy_version": "v1"
    })
    assert "receipt" in result
    assert result["receipt"]["run_id"] == "test_run_001"
    assert result["receipt"]["adapter_method"] == "env.health"

@pytest.mark.asyncio
async def test_mutable_op_requires_escalation():
    handler = MacAdapterHandler()
    result = await handler.dispatch({
        "op_type": "MAC_ADAPTER_CALL",
        "adapter_method": "env.focus_window",
        "adapter_params": {"window_id": "test"},
        "run_id": "test_run_002",
        "policy_version": "v1",
        "escalation_confirmed": False   # <-- not confirmed
    })
    assert result["ok"] == False
    assert result["rc"] == 403
    assert "escalation_confirmed" in result["failure_reason"]

@pytest.mark.asyncio
async def test_artifact_discipline():
    """Artifacts outside .run/<run_id>/adapter/ must be rejected"""
    handler = MacAdapterHandler()

    # Monkey-patch _call_adapter to return a bad artifact
    async def bad_call(method, params):
        return {"ok": True, "rc": 0, "artifacts": ["/tmp/bad_artifact.txt"],
                "checks": {}, "state_change": {"type": "none"}, "data": {}}
    handler._call_adapter = bad_call

    result = await handler.dispatch({
        "op_type": "MAC_ADAPTER_CALL",
        "adapter_method": "env.health",
        "adapter_params": {},
        "run_id": "test_run_003",
        "policy_version": "v1"
    })
    assert result["ok"] == False
    assert "SECURITY" in result["failure_reason"]

@pytest.mark.asyncio
async def test_timeout_normalization():
    handler = MacAdapterHandler()
    handler.ADAPTER_TIMEOUT = 0.001  # force timeout

    async def slow_call(method, params):
        await asyncio.sleep(1)
        return {}
    handler._call_adapter = slow_call

    result = await handler.dispatch({
        "op_type": "MAC_ADAPTER_CALL",
        "adapter_method": "env.health",
        "adapter_params": {},
        "run_id": "test_run_004",
        "policy_version": "v1"
    })
    assert result["ok"] == False
    assert result["rc"] == 124
    assert "timeout" in result["failure_reason"].lower()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
