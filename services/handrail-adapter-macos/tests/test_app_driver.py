"""Tests for app.* namespace."""
from __future__ import annotations
from unittest.mock import AsyncMock, patch
import pytest
from adapter_core.contract import AdapterRequest, OperationStatus
from app_driver.handlers import app_launch, app_quit, app_is_running, app_list_open

def req(params=None):
    return AdapterRequest(method="POST", params=params or {})

@pytest.mark.asyncio
async def test_launch_mock():
    with patch("app_driver.handlers.IS_MACOS", False):
        r = await app_launch(req({"app": "Safari"}))
    assert r.data["launched"] is True

@pytest.mark.asyncio
async def test_launch_blocked():
    with pytest.raises(PermissionError):
        await app_launch(req({"app": "Terminal"}))

@pytest.mark.asyncio
async def test_launch_no_app():
    r = await app_launch(req({}))
    assert r.status == OperationStatus.FAILURE

@pytest.mark.asyncio
async def test_launch_live():
    with patch("app_driver.handlers.IS_MACOS", True), \
         patch("app_driver.handlers._run", new=AsyncMock(return_value=(0, "", ""))):
        r = await app_launch(req({"app": "Safari"}))
    assert r.data["launched"] is True

@pytest.mark.asyncio
async def test_quit_mock():
    with patch("app_driver.handlers.IS_MACOS", False):
        r = await app_quit(req({"app": "Safari"}))
    assert r.data["ok"] is True

@pytest.mark.asyncio
async def test_quit_live():
    with patch("app_driver.handlers.IS_MACOS", True), \
         patch("app_driver.handlers._run", new=AsyncMock(return_value=(0, "", ""))):
        r = await app_quit(req({"app": "Safari"}))
    assert r.data["quit"] is True

@pytest.mark.asyncio
async def test_is_running_mock():
    with patch("app_driver.handlers.IS_MACOS", False):
        r = await app_is_running(req({"app": "Safari"}))
    assert r.data["running"] is False

@pytest.mark.asyncio
async def test_is_running_true():
    with patch("app_driver.handlers.IS_MACOS", True), \
         patch("app_driver.handlers._run", new=AsyncMock(return_value=(0, "true", ""))):
        r = await app_is_running(req({"app": "Safari"}))
    assert r.data["running"] is True

@pytest.mark.asyncio
async def test_list_open_mock():
    with patch("app_driver.handlers.IS_MACOS", False):
        r = await app_list_open(req())
    assert r.data["ok"] is True

@pytest.mark.asyncio
async def test_list_open_live():
    with patch("app_driver.handlers.IS_MACOS", True), \
         patch("app_driver.handlers._run", new=AsyncMock(return_value=(0, "Safari, Finder, Mail", ""))):
        r = await app_list_open(req())
    assert r.data["count"] == 3
    assert "Safari" in r.data["apps"]
