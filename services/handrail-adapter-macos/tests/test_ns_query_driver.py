"""Tests for ns_query.* namespace."""
from __future__ import annotations
from unittest.mock import patch, MagicMock
import pytest
from adapter_core.contract import AdapterRequest, OperationStatus
from ns_query_driver.handlers import ns_query_health_full, ns_query_context, ns_query_last_error

def req(params=None):
    return AdapterRequest(method="POST", params=params or {})

@pytest.mark.asyncio
async def test_health_full_no_httpx():
    with patch("ns_query_driver.handlers._HAS_HTTPX", False):
        r = await ns_query_health_full(req())
    assert r.data["ok"] is True

@pytest.mark.asyncio
async def test_health_full_all_ok():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"ok": True}
    with patch("ns_query_driver.handlers._HAS_HTTPX", True), \
         patch("httpx.get", return_value=mock_resp):
        r = await ns_query_health_full(req())
    assert r.data["ok"] is True
    assert "subsystems" in r.data

@pytest.mark.asyncio
async def test_context_no_httpx():
    with patch("ns_query_driver.handlers._HAS_HTTPX", False):
        r = await ns_query_context(req())
    assert r.data["ok"] is True

@pytest.mark.asyncio
async def test_last_error_no_ledger():
    with patch("pathlib.Path.exists", return_value=False):
        r = await ns_query_last_error(req())
    assert r.data["ok"] is True
