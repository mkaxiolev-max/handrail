"""Tests for url.* namespace."""
from __future__ import annotations
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from adapter_core.contract import AdapterRequest, OperationStatus
from url_driver.handlers import url_open, url_fetch, url_qr

def req(params=None):
    return AdapterRequest(method="POST", params=params or {})

@pytest.mark.asyncio
async def test_open_no_url():
    r = await url_open(req({}))
    assert r.status == OperationStatus.FAILURE

@pytest.mark.asyncio
async def test_open_blocked_scheme():
    with pytest.raises(PermissionError):
        await url_open(req({"url": "file:///etc/passwd"}))

@pytest.mark.asyncio
async def test_open_mock():
    with patch("url_driver.handlers.IS_MACOS", False):
        r = await url_open(req({"url": "https://zeroguess.dev"}))
    assert r.data["opened"] is True

@pytest.mark.asyncio
async def test_open_live():
    with patch("url_driver.handlers.IS_MACOS", True), \
         patch("url_driver.handlers._run", new=AsyncMock(return_value=(0, "", ""))):
        r = await url_open(req({"url": "https://zeroguess.dev"}))
    assert r.data["opened"] is True

@pytest.mark.asyncio
async def test_fetch_no_url():
    r = await url_fetch(req({}))
    assert r.status == OperationStatus.FAILURE

@pytest.mark.asyncio
async def test_fetch_blocked():
    with pytest.raises(PermissionError):
        await url_fetch(req({"url": "javascript:alert(1)"}))

@pytest.mark.asyncio
async def test_fetch_live():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = "Hello world " * 200
    with patch("httpx.get", return_value=mock_resp):
        r = await url_fetch(req({"url": "https://example.com", "max_chars": 100}))
    assert r.data["ok"] is True
    assert len(r.data["content"]) <= 100
    assert r.data["truncated"] is True

@pytest.mark.asyncio
async def test_qr_no_url():
    r = await url_qr(req({}))
    assert r.status == OperationStatus.FAILURE

@pytest.mark.asyncio
async def test_qr_blocked():
    with pytest.raises(PermissionError):
        await url_qr(req({"url": "file:///evil"}))

@pytest.mark.asyncio
async def test_qr_no_qrcode_lib():
    # Simulate qrcode not installed by patching the import inside the handler
    import sys
    import unittest.mock as mock
    real_import = __import__
    def mock_import(name, *args, **kwargs):
        if name == "qrcode":
            raise ImportError("no module named qrcode")
        return real_import(name, *args, **kwargs)
    with mock.patch("builtins.__import__", side_effect=mock_import):
        r = await url_qr(req({"url": "https://zeroguess.dev"}))
    assert r.data["ok"] is True
    assert r.data.get("skipped") is True
