"""
Tests for display.* namespace handlers.
All subprocess/osascript calls are monkeypatched — no real display hardware required.
"""
from __future__ import annotations
from unittest.mock import AsyncMock, patch
import pytest

from adapter_core.contract import AdapterRequest, OperationStatus
from display_driver.handlers import (
    display_get_info,
    display_set_brightness,
    display_screenshot_info,
    build_display_handlers,
)


def _req(method: str, **params) -> AdapterRequest:
    return AdapterRequest(method=method, params=params)


# ── display.get_info ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_display_get_info_macos():
    profiler_out = (
        "Graphics/Displays:\n"
        "  Display:\n"
        "    Resolution: 2560 x 1600 Retina\n"
        "    Resolution: 1920 x 1080\n"
    )
    with patch("display_driver.handlers.IS_MACOS", True), \
         patch("display_driver.handlers._run", new_callable=AsyncMock) as mock_run:
        mock_run.side_effect = [
            (0, profiler_out, ""),   # system_profiler
            (0, "0.85", ""),         # osascript brightness
        ]
        resp = await display_get_info(_req("display.get_info"))

    assert resp.status == OperationStatus.SUCCESS
    assert resp.data["screens"] == 2
    assert "2560" in resp.data["main_resolution"]
    assert resp.data["brightness"] == 0.85


@pytest.mark.asyncio
async def test_display_get_info_non_macos():
    with patch("display_driver.handlers.IS_MACOS", False):
        resp = await display_get_info(_req("display.get_info"))

    assert resp.status == OperationStatus.SUCCESS
    assert resp.data["skipped"] is True
    assert resp.data["reason"] == "not_macos"


@pytest.mark.asyncio
async def test_display_get_info_profiler_failure():
    with patch("display_driver.handlers.IS_MACOS", True), \
         patch("display_driver.handlers._run", new_callable=AsyncMock) as mock_run:
        mock_run.side_effect = [
            (1, "", "error"),   # system_profiler fails
            (0, "0.5", ""),     # brightness still works
        ]
        resp = await display_get_info(_req("display.get_info"))

    assert resp.status == OperationStatus.SUCCESS
    assert resp.data["screens"] == 1   # falls back to max(0,1)
    assert resp.data["brightness"] == 0.5


# ── display.set_brightness ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_set_brightness_success():
    with patch("display_driver.handlers.IS_MACOS", True), \
         patch("display_driver.handlers._run", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = (0, "", "")
        resp = await display_set_brightness(_req("display.set_brightness", brightness=0.7))

    assert resp.status == OperationStatus.SUCCESS
    assert resp.data["ok"] is True
    assert resp.data["brightness_set"] == 0.7


@pytest.mark.asyncio
async def test_set_brightness_non_macos():
    with patch("display_driver.handlers.IS_MACOS", False):
        resp = await display_set_brightness(_req("display.set_brightness", brightness=0.5))

    assert resp.status == OperationStatus.SUCCESS
    assert resp.data["skipped"] is True


@pytest.mark.asyncio
async def test_set_brightness_dignity_guard_over():
    with pytest.raises(PermissionError, match="out of allowed range"):
        await display_set_brightness(_req("display.set_brightness", brightness=1.1))


@pytest.mark.asyncio
async def test_set_brightness_dignity_guard_under():
    with pytest.raises(PermissionError, match="out of allowed range"):
        await display_set_brightness(_req("display.set_brightness", brightness=-0.1))


@pytest.mark.asyncio
async def test_set_brightness_boundary_zero():
    with patch("display_driver.handlers.IS_MACOS", True), \
         patch("display_driver.handlers._run", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = (0, "", "")
        resp = await display_set_brightness(_req("display.set_brightness", brightness=0.0))
    assert resp.status == OperationStatus.SUCCESS
    assert resp.data["brightness_set"] == 0.0


@pytest.mark.asyncio
async def test_set_brightness_boundary_one():
    with patch("display_driver.handlers.IS_MACOS", True), \
         patch("display_driver.handlers._run", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = (0, "", "")
        resp = await display_set_brightness(_req("display.set_brightness", brightness=1.0))
    assert resp.status == OperationStatus.SUCCESS
    assert resp.data["brightness_set"] == 1.0


@pytest.mark.asyncio
async def test_set_brightness_missing_param():
    resp = await display_set_brightness(_req("display.set_brightness"))
    assert resp.status == OperationStatus.FAILURE
    assert "params.brightness required" in resp.error


@pytest.mark.asyncio
async def test_set_brightness_osascript_error():
    with patch("display_driver.handlers.IS_MACOS", True), \
         patch("display_driver.handlers._run", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = (1, "", "not authorized")
        resp = await display_set_brightness(_req("display.set_brightness", brightness=0.5))
    assert resp.status == OperationStatus.FAILURE
    assert "osascript error" in resp.error


# ── display.screenshot_info ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_screenshot_info_quartz_success():
    with patch("display_driver.handlers.IS_MACOS", True), \
         patch("display_driver.handlers._run", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = (0, "2560,1600,2.0", "")
        resp = await display_screenshot_info(_req("display.screenshot_info"))

    assert resp.status == OperationStatus.SUCCESS
    assert resp.data["width"] == 2560
    assert resp.data["height"] == 1600
    assert resp.data["scale"] == 2.0


@pytest.mark.asyncio
async def test_screenshot_info_quartz_not_available():
    with patch("display_driver.handlers.IS_MACOS", True), \
         patch("display_driver.handlers._run", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = (1, "", "No module named 'Quartz'")
        resp = await display_screenshot_info(_req("display.screenshot_info"))

    assert resp.status == OperationStatus.SUCCESS
    assert resp.data["skipped"] is True
    assert resp.data["reason"] == "quartz_not_available"


@pytest.mark.asyncio
async def test_screenshot_info_non_macos():
    with patch("display_driver.handlers.IS_MACOS", False):
        resp = await display_screenshot_info(_req("display.screenshot_info"))

    assert resp.status == OperationStatus.SUCCESS
    assert resp.data["skipped"] is True
    assert resp.data["reason"] == "not_macos"


# ── registry ──────────────────────────────────────────────────────────────────

def test_build_display_handlers_keys():
    handlers = build_display_handlers()
    assert set(handlers.keys()) == {
        "display.get_info", "display.set_brightness", "display.screenshot_info"
    }
    for fn in handlers.values():
        assert callable(fn)
