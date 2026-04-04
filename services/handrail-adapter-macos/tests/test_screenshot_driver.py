"""Tests for screenshot.* namespace."""
from __future__ import annotations
from unittest.mock import AsyncMock, patch
import pytest
from adapter_core.contract import AdapterRequest, OperationStatus
from screenshot_driver.handlers import (
    screenshot_region, screenshot_window, screenshot_annotate, screenshot_diff
)

def req(params=None):
    return AdapterRequest(method="POST", params=params or {})

@pytest.mark.asyncio
async def test_region_mock():
    with patch("screenshot_driver.handlers.IS_MACOS", False):
        r = await screenshot_region(req({"x": 0, "y": 0, "w": 800, "h": 600}))
    assert r.data["ok"] is True
    assert r.data["path"] == "/tmp/mock.png"

@pytest.mark.asyncio
async def test_region_no_permission():
    with patch("screenshot_driver.handlers.IS_MACOS", True), \
         patch("screenshot_driver.handlers._run", new=AsyncMock(return_value=(1, "", "denied"))), \
         patch("pathlib.Path.exists", return_value=False):
        r = await screenshot_region(req())
    assert r.data["skipped"] is True

@pytest.mark.asyncio
async def test_window_no_app():
    r = await screenshot_window(req({}))
    assert r.status == OperationStatus.FAILURE

@pytest.mark.asyncio
async def test_window_mock():
    with patch("screenshot_driver.handlers.IS_MACOS", False):
        r = await screenshot_window(req({"app": "Safari"}))
    assert r.data["ok"] is True

@pytest.mark.asyncio
async def test_annotate_mock():
    with patch("screenshot_driver.handlers.IS_MACOS", False):
        r = await screenshot_annotate(req({"label": "test"}))
    assert r.data["ok"] is True

@pytest.mark.asyncio
async def test_diff_mock():
    with patch("screenshot_driver.handlers.IS_MACOS", False):
        r = await screenshot_diff(req())
    assert r.data["changed_pct"] == 0
