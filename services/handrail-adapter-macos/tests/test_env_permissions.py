"""Tests for env.permissions handler — all subprocess calls monkeypatched."""
from __future__ import annotations
from unittest.mock import AsyncMock, patch, MagicMock
import pytest
from adapter_core.contract import AdapterRequest, OperationStatus
from env_driver.permissions import env_permissions


def _req(**params) -> AdapterRequest:
    return AdapterRequest(method="env.permissions", params=params)


def _mock_proc(returncode: int):
    proc = MagicMock()
    proc.returncode = returncode
    proc.wait = AsyncMock(return_value=returncode)
    return proc


@pytest.mark.asyncio
async def test_permissions_all_granted():
    good_proc = _mock_proc(0)
    with patch("env_driver.permissions.IS_MACOS", True), \
         patch("asyncio.create_subprocess_exec", return_value=good_proc):
        resp = await env_permissions(_req())
    assert resp.status == OperationStatus.SUCCESS
    assert resp.data["all_granted"] is True
    assert resp.data["missing"] == []
    assert isinstance(resp.data["permissions"], dict)


@pytest.mark.asyncio
async def test_permissions_screen_recording_denied():
    call_count = {"n": 0}

    def side_effect(*args, **kwargs):
        call_count["n"] += 1
        # First call is Quartz (screen_recording) — fail it
        if call_count["n"] == 1:
            return _mock_proc(1)
        return _mock_proc(0)

    with patch("env_driver.permissions.IS_MACOS", True), \
         patch("asyncio.create_subprocess_exec", side_effect=side_effect):
        resp = await env_permissions(_req())

    assert resp.status == OperationStatus.SUCCESS
    assert resp.data["permissions"]["screen_recording"] is False
    assert "screen_recording" in resp.data["missing"]
    assert resp.data["all_granted"] is False


@pytest.mark.asyncio
async def test_permissions_skipped_non_macos():
    with patch("env_driver.permissions.IS_MACOS", False):
        resp = await env_permissions(_req())
    assert resp.status == OperationStatus.SUCCESS
    assert resp.data["skipped"] is True
    assert resp.data["reason"] == "not_macos"


@pytest.mark.asyncio
async def test_permissions_exception_falls_back_to_false():
    with patch("env_driver.permissions.IS_MACOS", True), \
         patch("asyncio.create_subprocess_exec", side_effect=OSError("no binary")):
        resp = await env_permissions(_req())
    assert resp.status == OperationStatus.SUCCESS
    assert resp.data["all_granted"] is False
    for v in resp.data["permissions"].values():
        assert v is False


@pytest.mark.asyncio
async def test_permissions_all_three_keys_present():
    good_proc = _mock_proc(0)
    with patch("env_driver.permissions.IS_MACOS", True), \
         patch("asyncio.create_subprocess_exec", return_value=good_proc):
        resp = await env_permissions(_req())
    perms = resp.data["permissions"]
    assert "screen_recording" in perms
    assert "accessibility" in perms
    assert "automation" in perms


@pytest.mark.asyncio
async def test_permissions_accessibility_denied():
    call_count = {"n": 0}

    def side_effect(*args, **kwargs):
        call_count["n"] += 1
        # Second call is accessibility
        if call_count["n"] == 2:
            return _mock_proc(1)
        return _mock_proc(0)

    with patch("env_driver.permissions.IS_MACOS", True), \
         patch("asyncio.create_subprocess_exec", side_effect=side_effect):
        resp = await env_permissions(_req())

    assert resp.data["permissions"]["accessibility"] is False
    assert "accessibility" in resp.data["missing"]


@pytest.mark.asyncio
async def test_permissions_state_hash_present():
    good_proc = _mock_proc(0)
    with patch("env_driver.permissions.IS_MACOS", True), \
         patch("asyncio.create_subprocess_exec", return_value=good_proc):
        resp = await env_permissions(_req())
    assert resp.state_hash.startswith("sha256:")
