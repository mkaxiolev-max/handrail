"""
Tests for clipboard.* namespace handlers.
All subprocess calls are monkeypatched — no real clipboard access required.
"""
from __future__ import annotations
from unittest.mock import AsyncMock, patch
import pytest

from adapter_core.contract import AdapterRequest, OperationStatus
from clipboard_driver.handlers import (
    clipboard_read,
    clipboard_write,
    build_clipboard_handlers,
    _SECRET_PATTERN,
    _MAX_WRITE_CHARS,
)


def _req(method: str, **params) -> AdapterRequest:
    return AdapterRequest(method=method, params=params)


# ── clipboard.read ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_clipboard_read_success():
    with patch("clipboard_driver.handlers._run_simple", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = (0, "hello world", "")
        resp = await clipboard_read(_req("clipboard.read"))

    assert resp.status == OperationStatus.SUCCESS
    assert resp.data["content"] == "hello world"
    assert resp.data["length"] == len("hello world")


@pytest.mark.asyncio
async def test_clipboard_read_strips_sk_secret():
    dangerous = "my api key sk_live_abcdef123456 and more text"
    with patch("clipboard_driver.handlers._run_simple", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = (0, dangerous, "")
        resp = await clipboard_read(_req("clipboard.read"))

    assert resp.status == OperationStatus.SUCCESS
    assert "sk_live" not in resp.data["content"]
    assert "[REDACTED]" in resp.data["content"]


@pytest.mark.asyncio
async def test_clipboard_read_strips_whsec_secret():
    dangerous = "webhook secret whsec_abc123XYZ== end"
    with patch("clipboard_driver.handlers._run_simple", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = (0, dangerous, "")
        resp = await clipboard_read(_req("clipboard.read"))

    assert resp.status == OperationStatus.SUCCESS
    assert "whsec_" not in resp.data["content"]
    assert "[REDACTED]" in resp.data["content"]


@pytest.mark.asyncio
async def test_clipboard_read_clean_content_unchanged():
    safe = "this is safe clipboard content with no secrets"
    with patch("clipboard_driver.handlers._run_simple", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = (0, safe, "")
        resp = await clipboard_read(_req("clipboard.read"))

    assert resp.data["content"] == safe


@pytest.mark.asyncio
async def test_clipboard_read_pbpaste_failure():
    with patch("clipboard_driver.handlers._run_simple", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = (1, "", "pbpaste: error")
        resp = await clipboard_read(_req("clipboard.read"))

    assert resp.status == OperationStatus.FAILURE
    assert "pbpaste failed" in resp.error


# ── clipboard.write ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_clipboard_write_success():
    with patch("clipboard_driver.handlers._run_simple", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = (0, "", "")
        resp = await clipboard_write(_req("clipboard.write", content="write this"))

    assert resp.status == OperationStatus.SUCCESS
    assert resp.data["ok"] is True
    assert resp.data["length"] == len("write this")


@pytest.mark.asyncio
async def test_clipboard_write_dignity_guard_too_long():
    big = "x" * _MAX_WRITE_CHARS
    with pytest.raises(PermissionError, match="exceeds maximum"):
        await clipboard_write(_req("clipboard.write", content=big))


@pytest.mark.asyncio
async def test_clipboard_write_empty_string():
    with patch("clipboard_driver.handlers._run_simple", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = (0, "", "")
        resp = await clipboard_write(_req("clipboard.write", content=""))
    assert resp.status == OperationStatus.SUCCESS
    assert resp.data["length"] == 0


@pytest.mark.asyncio
async def test_clipboard_write_just_under_limit():
    content = "y" * (_MAX_WRITE_CHARS - 1)
    with patch("clipboard_driver.handlers._run_simple", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = (0, "", "")
        resp = await clipboard_write(_req("clipboard.write", content=content))
    assert resp.status == OperationStatus.SUCCESS


@pytest.mark.asyncio
async def test_clipboard_write_pbcopy_failure():
    with patch("clipboard_driver.handlers._run_simple", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = (1, "", "pbcopy: error")
        resp = await clipboard_write(_req("clipboard.write", content="test"))

    assert resp.status == OperationStatus.FAILURE
    assert "pbcopy failed" in resp.error


# ── registry ──────────────────────────────────────────────────────────────────

def test_build_clipboard_handlers_keys():
    handlers = build_clipboard_handlers()
    assert set(handlers.keys()) == {"clipboard.read", "clipboard.write"}
    for fn in handlers.values():
        assert callable(fn)
