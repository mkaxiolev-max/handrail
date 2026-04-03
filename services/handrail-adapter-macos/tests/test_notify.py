"""
Tests for notify.* namespace handlers.
All osascript calls are monkeypatched — no real macOS notifications required.
"""
from __future__ import annotations
from unittest.mock import AsyncMock, patch
import pytest

from adapter_core.contract import AdapterRequest, OperationStatus
from notify_driver.handlers import (
    notify_send,
    notify_badge,
    build_notify_handlers,
)


def _req(method: str, **params) -> AdapterRequest:
    return AdapterRequest(method=method, params=params)


# ── notify.send ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_notify_send_success():
    with patch("notify_driver.handlers.IS_MACOS", True), \
         patch("notify_driver.handlers._osascript", new_callable=AsyncMock) as mock_osa:
        mock_osa.return_value = (0, "", "")
        resp = await notify_send(_req("notify.send", title="NS∞", message="Boot complete"))

    assert resp.status == OperationStatus.SUCCESS
    assert resp.data["ok"] is True
    assert resp.data["delivered"] is True


@pytest.mark.asyncio
async def test_notify_send_non_macos():
    with patch("notify_driver.handlers.IS_MACOS", False):
        resp = await notify_send(_req("notify.send", title="Test", message="hello"))

    assert resp.status == OperationStatus.SUCCESS
    assert resp.data["skipped"] is True
    assert resp.data["delivered"] is False
    assert resp.data["reason"] == "not_macos"


@pytest.mark.asyncio
async def test_notify_send_missing_message():
    resp = await notify_send(_req("notify.send", title="NS∞"))
    assert resp.status == OperationStatus.FAILURE
    assert "params.message required" in resp.error


@pytest.mark.asyncio
async def test_notify_send_osascript_error():
    with patch("notify_driver.handlers.IS_MACOS", True), \
         patch("notify_driver.handlers._osascript", new_callable=AsyncMock) as mock_osa:
        mock_osa.return_value = (1, "", "execution error: not allowed")
        resp = await notify_send(_req("notify.send", title="NS∞", message="test"))

    assert resp.status == OperationStatus.FAILURE
    assert "osascript error" in resp.error


@pytest.mark.asyncio
async def test_notify_send_default_title():
    """Message with no explicit title should use NS∞ default."""
    with patch("notify_driver.handlers.IS_MACOS", True), \
         patch("notify_driver.handlers._osascript", new_callable=AsyncMock) as mock_osa:
        mock_osa.return_value = (0, "", "")
        resp = await notify_send(_req("notify.send", message="hello"))

    assert resp.status == OperationStatus.SUCCESS
    # Verify the osascript call included the default title
    call_args = mock_osa.call_args[0][0]
    assert 'NS∞' in call_args


@pytest.mark.asyncio
async def test_notify_send_escapes_quotes():
    with patch("notify_driver.handlers.IS_MACOS", True), \
         patch("notify_driver.handlers._osascript", new_callable=AsyncMock) as mock_osa:
        mock_osa.return_value = (0, "", "")
        resp = await notify_send(_req("notify.send", message='say "hello"', title='Test "title"'))

    assert resp.status == OperationStatus.SUCCESS
    call_args = mock_osa.call_args[0][0]
    assert '\\"hello\\"' in call_args


# ── notify.badge ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_notify_badge_success():
    with patch("notify_driver.handlers.IS_MACOS", True), \
         patch("notify_driver.handlers._osascript", new_callable=AsyncMock) as mock_osa:
        mock_osa.return_value = (0, "", "")
        resp = await notify_badge(_req("notify.badge", count=3))

    assert resp.status == OperationStatus.SUCCESS
    assert resp.data["ok"] is True


@pytest.mark.asyncio
async def test_notify_badge_zero_clears():
    with patch("notify_driver.handlers.IS_MACOS", True), \
         patch("notify_driver.handlers._osascript", new_callable=AsyncMock) as mock_osa:
        mock_osa.return_value = (0, "", "")
        resp = await notify_badge(_req("notify.badge", count=0))

    assert resp.status == OperationStatus.SUCCESS
    assert resp.data["ok"] is True


@pytest.mark.asyncio
async def test_notify_badge_non_macos():
    with patch("notify_driver.handlers.IS_MACOS", False):
        resp = await notify_badge(_req("notify.badge", count=5))

    assert resp.status == OperationStatus.SUCCESS
    assert resp.data["skipped"] is True
    assert resp.data["reason"] == "not_macos"


@pytest.mark.asyncio
async def test_notify_badge_invalid_count():
    resp = await notify_badge(_req("notify.badge", count="bad"))
    assert resp.status == OperationStatus.FAILURE
    assert "params.count must be an integer" in resp.error


@pytest.mark.asyncio
async def test_notify_badge_osascript_error():
    with patch("notify_driver.handlers.IS_MACOS", True), \
         patch("notify_driver.handlers._osascript", new_callable=AsyncMock) as mock_osa:
        mock_osa.return_value = (1, "", "not authorized")
        resp = await notify_badge(_req("notify.badge", count=1))

    assert resp.status == OperationStatus.FAILURE
    assert "osascript error" in resp.error


# ── registry ──────────────────────────────────────────────────────────────────

def test_build_notify_handlers_keys():
    handlers = build_notify_handlers()
    assert set(handlers.keys()) == {"notify.send", "notify.badge"}
    for fn in handlers.values():
        assert callable(fn)
