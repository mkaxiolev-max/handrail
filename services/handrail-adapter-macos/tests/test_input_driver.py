"""
Tests for input.* namespace — all _run calls monkeypatched.
No real Accessibility permission or system events required.
"""
from __future__ import annotations
from unittest.mock import AsyncMock, patch
import pytest

from adapter_core.contract import AdapterRequest, OperationStatus
from input_driver.handlers import (
    input_type,
    input_click,
    input_key,
    build_input_handlers,
    _BLOCKED_COMBOS,
    _SAFE_KEYS,
)


def _req(method: str = "input.test", **params) -> AdapterRequest:
    return AdapterRequest(method=method, params=params)


def _ok():
    return AsyncMock(return_value=(0, "", ""))


def _err(msg: str):
    return AsyncMock(return_value=(1, "", msg))


# ── input.type ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_type_success():
    with patch("input_driver.handlers.IS_MACOS", True), \
         patch("input_driver.handlers._run", _ok()):
        r = await input_type(_req(text="hello"))
    assert r.status == OperationStatus.SUCCESS
    assert r.data["typed_length"] == 5
    assert r.data["ok"] is True


@pytest.mark.asyncio
async def test_type_non_macos():
    with patch("input_driver.handlers.IS_MACOS", False):
        r = await input_type(_req(text="hello"))
    assert r.status == OperationStatus.SUCCESS
    assert r.data["skipped"] is True
    assert r.data["reason"] == "not_macos"


@pytest.mark.asyncio
async def test_type_missing_text():
    with patch("input_driver.handlers.IS_MACOS", True):
        r = await input_type(_req())
    assert r.status == OperationStatus.FAILURE
    assert "text required" in r.error


@pytest.mark.asyncio
async def test_type_too_long():
    with patch("input_driver.handlers.IS_MACOS", True):
        with pytest.raises(PermissionError, match="500"):
            await input_type(_req(text="x" * 501))


@pytest.mark.asyncio
async def test_type_exactly_500():
    with patch("input_driver.handlers.IS_MACOS", True), \
         patch("input_driver.handlers._run", _ok()):
        r = await input_type(_req(text="a" * 500))
    assert r.status == OperationStatus.SUCCESS
    assert r.data["typed_length"] == 500


@pytest.mark.asyncio
async def test_type_accessibility_denied():
    with patch("input_driver.handlers.IS_MACOS", True), \
         patch("input_driver.handlers._run", _err("osascript: error -1719")):
        r = await input_type(_req(text="hello"))
    assert r.status == OperationStatus.SUCCESS
    assert r.data["skipped"] is True
    assert r.data["reason"] == "accessibility_permission_required"


@pytest.mark.asyncio
async def test_type_osascript_failure():
    with patch("input_driver.handlers.IS_MACOS", True), \
         patch("input_driver.handlers._run", _err("some other error")):
        r = await input_type(_req(text="hello"))
    assert r.status == OperationStatus.FAILURE
    assert "keystroke failed" in r.error


# ── input.click ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_click_success():
    with patch("input_driver.handlers.IS_MACOS", True), \
         patch("input_driver.handlers._run", _ok()):
        r = await input_click(_req(x=100, y=200))
    assert r.status == OperationStatus.SUCCESS
    assert r.data["clicked"] == {"x": 100, "y": 200}


@pytest.mark.asyncio
async def test_click_non_macos():
    with patch("input_driver.handlers.IS_MACOS", False):
        r = await input_click(_req(x=0, y=0))
    assert r.status == OperationStatus.SUCCESS
    assert r.data["skipped"] is True


@pytest.mark.asyncio
async def test_click_missing_coords():
    with patch("input_driver.handlers.IS_MACOS", True):
        r = await input_click(_req())
    assert r.status == OperationStatus.FAILURE
    assert "required" in r.error


@pytest.mark.asyncio
async def test_click_missing_y():
    with patch("input_driver.handlers.IS_MACOS", True):
        r = await input_click(_req(x=100))
    assert r.status == OperationStatus.FAILURE


@pytest.mark.asyncio
async def test_click_out_of_bounds_x():
    with patch("input_driver.handlers.IS_MACOS", True):
        with pytest.raises(PermissionError, match="bounds"):
            await input_click(_req(x=99999, y=0))


@pytest.mark.asyncio
async def test_click_out_of_bounds_y():
    with patch("input_driver.handlers.IS_MACOS", True):
        with pytest.raises(PermissionError, match="bounds"):
            await input_click(_req(x=0, y=99999))


@pytest.mark.asyncio
async def test_click_max_bounds():
    with patch("input_driver.handlers.IS_MACOS", True), \
         patch("input_driver.handlers._run", _ok()):
        r = await input_click(_req(x=7680, y=4320))
    assert r.status == OperationStatus.SUCCESS


@pytest.mark.asyncio
async def test_click_accessibility_denied():
    with patch("input_driver.handlers.IS_MACOS", True), \
         patch("input_driver.handlers._run", _err("assistive access not granted")):
        r = await input_click(_req(x=10, y=10))
    assert r.status == OperationStatus.SUCCESS
    assert r.data["skipped"] is True
    assert r.data["reason"] == "accessibility_permission_required"


# ── input.key ─────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_key_return():
    with patch("input_driver.handlers.IS_MACOS", True), \
         patch("input_driver.handlers._run", _ok()):
        r = await input_key(_req(key="return"))
    assert r.status == OperationStatus.SUCCESS
    assert r.data["key"] == "return"


@pytest.mark.asyncio
async def test_key_non_macos():
    with patch("input_driver.handlers.IS_MACOS", False):
        r = await input_key(_req(key="return"))
    assert r.status == OperationStatus.SUCCESS
    assert r.data["skipped"] is True


@pytest.mark.asyncio
async def test_key_missing():
    with patch("input_driver.handlers.IS_MACOS", True):
        r = await input_key(_req())
    assert r.status == OperationStatus.FAILURE


@pytest.mark.asyncio
async def test_key_blocked_cmd_q():
    with patch("input_driver.handlers.IS_MACOS", True):
        with pytest.raises(PermissionError, match="blocked"):
            await input_key(_req(key="cmd+q"))


@pytest.mark.asyncio
async def test_key_blocked_ctrl_alt_delete():
    with patch("input_driver.handlers.IS_MACOS", True):
        with pytest.raises(PermissionError, match="blocked"):
            await input_key(_req(key="ctrl+alt+delete"))


@pytest.mark.asyncio
async def test_key_unsafe_combo():
    with patch("input_driver.handlers.IS_MACOS", True):
        with pytest.raises(PermissionError, match="whitelist"):
            await input_key(_req(key="cmd+shift+q"))


@pytest.mark.asyncio
async def test_key_cmd_c():
    with patch("input_driver.handlers.IS_MACOS", True), \
         patch("input_driver.handlers._run", _ok()):
        r = await input_key(_req(key="cmd+c"))
    assert r.status == OperationStatus.SUCCESS


@pytest.mark.asyncio
async def test_key_escape():
    with patch("input_driver.handlers.IS_MACOS", True), \
         patch("input_driver.handlers._run", _ok()):
        r = await input_key(_req(key="escape"))
    assert r.status == OperationStatus.SUCCESS


@pytest.mark.asyncio
async def test_key_single_letter():
    with patch("input_driver.handlers.IS_MACOS", True), \
         patch("input_driver.handlers._run", _ok()):
        r = await input_key(_req(key="a"))
    assert r.status == OperationStatus.SUCCESS


@pytest.mark.asyncio
async def test_key_accessibility_denied():
    with patch("input_driver.handlers.IS_MACOS", True), \
         patch("input_driver.handlers._run", _err("error -1719")):
        r = await input_key(_req(key="return"))
    assert r.status == OperationStatus.SUCCESS
    assert r.data["skipped"] is True


# ── registry ──────────────────────────────────────────────────────────────────

def test_build_input_handlers_keys():
    h = build_input_handlers()
    assert set(h.keys()) == {"input.type", "input.click", "input.key"}
    for fn in h.values():
        assert callable(fn)


def test_blocked_combos_are_disjoint_from_safe():
    """Blocked combos must not appear in safe list."""
    assert _BLOCKED_COMBOS.isdisjoint(_SAFE_KEYS)
