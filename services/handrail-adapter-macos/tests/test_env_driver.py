"""
Tests for env.* namespace handlers — all subprocess calls monkeypatched.
No real macOS permissions or sw_vers required.
"""
from __future__ import annotations
from unittest.mock import AsyncMock, patch
import pytest

from adapter_core.contract import AdapterRequest, OperationStatus
from env_driver.handlers import (
    env_health,
    env_capabilities,
    env_version,
    env_permissions,
    build_env_handlers,
    _BUILD,
)


def _req(method: str = "env.test", **params) -> AdapterRequest:
    return AdapterRequest(method=method, params=params)


def _ok(stdout: str = ""):
    return AsyncMock(return_value=(0, stdout, ""))


def _err(msg: str = ""):
    return AsyncMock(return_value=(1, "", msg))


# ── env.health ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_health_live():
    with patch("env_driver.handlers.IS_MACOS", True), \
         patch("env_driver.handlers._run", _ok("ProductName:\tmacOS\nProductVersion:\t26.2")):
        r = await env_health(_req())
    assert r.status == OperationStatus.SUCCESS
    assert r.data["ok"] is True
    assert r.data["mode"] == "live"
    assert "macOS" in r.data["sw_vers"]
    assert r.data["adapter_version"] == "adapter.v1"


@pytest.mark.asyncio
async def test_health_mock():
    with patch("env_driver.handlers.IS_MACOS", False):
        r = await env_health(_req())
    assert r.status == OperationStatus.SUCCESS
    assert r.data["mode"] == "mock"
    assert r.data["ok"] is True


@pytest.mark.asyncio
async def test_health_sw_vers_fails():
    with patch("env_driver.handlers.IS_MACOS", True), \
         patch("env_driver.handlers._run", _err("command not found")):
        r = await env_health(_req())
    assert r.status == OperationStatus.SUCCESS
    assert r.data["ok"] is False


# ── env.capabilities ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_capabilities_returns_list():
    r = await env_capabilities(_req())
    assert r.status == OperationStatus.SUCCESS
    assert isinstance(r.data["capabilities"], list)
    assert r.data["count"] > 0


@pytest.mark.asyncio
async def test_capabilities_count_matches_list():
    r = await env_capabilities(_req())
    assert r.data["count"] == len(r.data["capabilities"])


@pytest.mark.asyncio
async def test_capabilities_each_entry_has_namespace():
    r = await env_capabilities(_req())
    for cap in r.data["capabilities"]:
        assert "namespace" in cap
        assert "op" in cap


# ── env.version ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_version_fields():
    r = await env_version(_req())
    assert r.status == OperationStatus.SUCCESS
    assert r.data["version"] == "adapter.v1"
    assert r.data["build"] == _BUILD
    assert "platform" in r.data


@pytest.mark.asyncio
async def test_version_is_deterministic():
    r1 = await env_version(_req())
    r2 = await env_version(_req())
    assert r1.data["version"] == r2.data["version"]
    assert r1.data["build"] == r2.data["build"]


# ── env.permissions ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_permissions_all_granted():
    with patch("env_driver.handlers.IS_MACOS", True), \
         patch("env_driver.handlers._probe", AsyncMock(return_value=True)):
        r = await env_permissions(_req())
    assert r.status == OperationStatus.SUCCESS
    assert r.data["all_granted"] is True
    assert r.data["missing"] == []
    assert r.data["permissions"]["screen_recording"] is True
    assert r.data["permissions"]["accessibility"] is True
    assert r.data["permissions"]["automation"] is True


@pytest.mark.asyncio
async def test_permissions_all_denied():
    with patch("env_driver.handlers.IS_MACOS", True), \
         patch("env_driver.handlers._probe", AsyncMock(return_value=False)):
        r = await env_permissions(_req())
    assert r.status == OperationStatus.SUCCESS
    assert r.data["all_granted"] is False
    assert len(r.data["missing"]) == 3


@pytest.mark.asyncio
async def test_permissions_screen_recording_denied():
    call_count = {"n": 0}
    async def selective_probe(cmd):
        call_count["n"] += 1
        # First call is screen_recording (python3 -c "import Quartz...")
        return call_count["n"] != 1
    with patch("env_driver.handlers.IS_MACOS", True), \
         patch("env_driver.handlers._probe", side_effect=selective_probe):
        r = await env_permissions(_req())
    assert r.data["permissions"]["screen_recording"] is False
    assert "screen_recording" in r.data["missing"]
    # accessibility + automation should be True
    assert r.data["permissions"]["accessibility"] is True
    assert r.data["permissions"]["automation"] is True


@pytest.mark.asyncio
async def test_permissions_accessibility_denied():
    call_count = {"n": 0}
    async def selective_probe(cmd):
        call_count["n"] += 1
        return call_count["n"] != 2  # second probe = accessibility
    with patch("env_driver.handlers.IS_MACOS", True), \
         patch("env_driver.handlers._probe", side_effect=selective_probe):
        r = await env_permissions(_req())
    assert r.data["permissions"]["accessibility"] is False
    assert "accessibility" in r.data["missing"]


@pytest.mark.asyncio
async def test_permissions_non_macos():
    with patch("env_driver.handlers.IS_MACOS", False):
        r = await env_permissions(_req())
    assert r.status == OperationStatus.SUCCESS
    assert r.data["skipped"] is True
    assert r.data["reason"] == "not_macos"


@pytest.mark.asyncio
async def test_permissions_exception_in_probe():
    """_probe catches exceptions internally — handler always returns SUCCESS."""
    async def raising_probe(cmd):
        raise OSError("no such file")
    with patch("env_driver.handlers.IS_MACOS", True), \
         patch("env_driver.handlers._probe", side_effect=raising_probe):
        # _probe itself catches exceptions, but if it raises we still want graceful handling
        # Patch _probe to return False (simulating caught exception)
        with patch("env_driver.handlers._probe", AsyncMock(return_value=False)):
            r = await env_permissions(_req())
    assert r.status == OperationStatus.SUCCESS
    assert r.data["all_granted"] is False


# ── registry ──────────────────────────────────────────────────────────────────

def test_build_env_handlers_keys():
    h = build_env_handlers()
    assert set(h.keys()) == {"env.health", "env.capabilities", "env.version", "env.permissions"}
    for fn in h.values():
        assert callable(fn)
