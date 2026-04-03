"""
Tests for window.* namespace — all _run calls monkeypatched.
No real Accessibility permission required.
"""
from __future__ import annotations
from unittest.mock import AsyncMock, patch
import pytest

from adapter_core.contract import AdapterRequest, OperationStatus
from window_driver.handlers import (
    window_list,
    window_focus,
    window_get_focused,
    build_window_handlers,
)


def _req(method: str = "window.test", **params) -> AdapterRequest:
    return AdapterRequest(method=method, params=params)


def _ok(stdout: str = ""):
    return AsyncMock(return_value=(0, stdout, ""))


def _err(msg: str):
    return AsyncMock(return_value=(1, "", msg))


# ── window.list ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_success():
    with patch("window_driver.handlers.IS_MACOS", True), \
         patch("window_driver.handlers._run", _ok("Terminal, Safari, Finder")):
        r = await window_list(_req())
    assert r.status == OperationStatus.SUCCESS
    assert r.data["count"] == 3
    names = {w["app"] for w in r.data["windows"]}
    assert names == {"Terminal", "Safari", "Finder"}


@pytest.mark.asyncio
async def test_list_non_macos():
    with patch("window_driver.handlers.IS_MACOS", False):
        r = await window_list(_req())
    assert r.status == OperationStatus.SUCCESS
    assert r.data["windows"] == []
    assert r.data["skipped"] is True


@pytest.mark.asyncio
async def test_list_accessibility_denied():
    with patch("window_driver.handlers.IS_MACOS", True), \
         patch("window_driver.handlers._run", _err("error -1719")):
        r = await window_list(_req())
    assert r.status == OperationStatus.SUCCESS
    assert r.data["skipped"] is True
    assert r.data["reason"] == "accessibility_permission_required"
    assert r.data["windows"] == []


@pytest.mark.asyncio
async def test_list_assistive_error():
    with patch("window_driver.handlers.IS_MACOS", True), \
         patch("window_driver.handlers._run", _err("assistive access not granted")):
        r = await window_list(_req())
    assert r.status == OperationStatus.SUCCESS
    assert r.data["skipped"] is True


@pytest.mark.asyncio
async def test_list_empty():
    with patch("window_driver.handlers.IS_MACOS", True), \
         patch("window_driver.handlers._run", _ok("")):
        r = await window_list(_req())
    assert r.status == OperationStatus.SUCCESS
    assert r.data["count"] == 0
    assert r.data["windows"] == []


@pytest.mark.asyncio
async def test_list_osascript_failure():
    with patch("window_driver.handlers.IS_MACOS", True), \
         patch("window_driver.handlers._run", _err("some other error")):
        r = await window_list(_req())
    assert r.status == OperationStatus.FAILURE
    assert "window.list failed" in r.error


# ── window.focus ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_focus_success():
    with patch("window_driver.handlers.IS_MACOS", True), \
         patch("window_driver.handlers._run", _ok()):
        r = await window_focus(_req(app="Terminal"))
    assert r.status == OperationStatus.SUCCESS
    assert r.data["focused_app"] == "Terminal"
    assert r.data["ok"] is True


@pytest.mark.asyncio
async def test_focus_non_macos():
    with patch("window_driver.handlers.IS_MACOS", False):
        r = await window_focus(_req(app="Terminal"))
    assert r.status == OperationStatus.SUCCESS
    assert r.data["skipped"] is True


@pytest.mark.asyncio
async def test_focus_missing_app():
    with patch("window_driver.handlers.IS_MACOS", True):
        r = await window_focus(_req())
    assert r.status == OperationStatus.FAILURE
    assert "app required" in r.error


@pytest.mark.asyncio
async def test_focus_osascript_failure():
    with patch("window_driver.handlers.IS_MACOS", True), \
         patch("window_driver.handlers._run", _err("can't activate")):
        r = await window_focus(_req(app="NonExistent"))
    assert r.status == OperationStatus.FAILURE
    assert "focus failed" in r.error


# ── window.get_focused ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_focused_success():
    with patch("window_driver.handlers.IS_MACOS", True), \
         patch("window_driver.handlers._run", _ok("Terminal|axiolev_runtime")):
        r = await window_get_focused(_req())
    assert r.status == OperationStatus.SUCCESS
    assert r.data["app"] == "Terminal"
    assert r.data["title"] == "axiolev_runtime"


@pytest.mark.asyncio
async def test_get_focused_no_title():
    with patch("window_driver.handlers.IS_MACOS", True), \
         patch("window_driver.handlers._run", _ok("Finder|")):
        r = await window_get_focused(_req())
    assert r.status == OperationStatus.SUCCESS
    assert r.data["app"] == "Finder"
    assert r.data["title"] == ""


@pytest.mark.asyncio
async def test_get_focused_non_macos():
    with patch("window_driver.handlers.IS_MACOS", False):
        r = await window_get_focused(_req())
    assert r.status == OperationStatus.SUCCESS
    assert r.data["skipped"] is True


@pytest.mark.asyncio
async def test_get_focused_accessibility_1719():
    with patch("window_driver.handlers.IS_MACOS", True), \
         patch("window_driver.handlers._run", _err("error -1719")):
        r = await window_get_focused(_req())
    assert r.status == OperationStatus.SUCCESS
    assert r.data["skipped"] is True
    assert r.data["reason"] == "accessibility_permission_required"


@pytest.mark.asyncio
async def test_get_focused_osascript_failure():
    with patch("window_driver.handlers.IS_MACOS", True), \
         patch("window_driver.handlers._run", _err("no frontmost process")):
        r = await window_get_focused(_req())
    assert r.status == OperationStatus.FAILURE
    assert "get_focused failed" in r.error


# ── registry ──────────────────────────────────────────────────────────────────

def test_build_window_handlers_keys():
    h = build_window_handlers()
    assert set(h.keys()) == {"window.list", "window.focus", "window.get_focused"}
    for fn in h.values():
        assert callable(fn)
