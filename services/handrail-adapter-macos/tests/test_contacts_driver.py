"""Tests for contacts.* namespace."""
from __future__ import annotations
from unittest.mock import AsyncMock, patch
import pytest
from adapter_core.contract import AdapterRequest, OperationStatus
from contacts_driver.handlers import contacts_search, contacts_count, contacts_vcard

def req(params=None):
    return AdapterRequest(method="POST", params=params or {})

@pytest.mark.asyncio
async def test_search_no_query():
    r = await contacts_search(req({}))
    assert r.status == OperationStatus.FAILURE

@pytest.mark.asyncio
async def test_search_mock():
    with patch("contacts_driver.handlers.IS_MACOS", False):
        r = await contacts_search(req({"query": "Mike"}))
    assert r.data["ok"] is True

@pytest.mark.asyncio
async def test_search_live():
    with patch("contacts_driver.handlers.IS_MACOS", True), \
         patch("contacts_driver.handlers._run", new=AsyncMock(
             return_value=(0, "Mike Kenworthy|mike@axiolev.com|+15551234567", ""))):
        r = await contacts_search(req({"query": "Mike"}))
    assert r.data["count"] >= 1
    assert r.data["contacts"][0]["name"] == "Mike Kenworthy"

@pytest.mark.asyncio
async def test_count_mock():
    with patch("contacts_driver.handlers.IS_MACOS", False):
        r = await contacts_count(req())
    assert r.data["ok"] is True

@pytest.mark.asyncio
async def test_count_live():
    with patch("contacts_driver.handlers.IS_MACOS", True), \
         patch("contacts_driver.handlers._run", new=AsyncMock(return_value=(0, "42", ""))):
        r = await contacts_count(req())
    assert r.data["count"] == 42

@pytest.mark.asyncio
async def test_vcard_no_name():
    r = await contacts_vcard(req({}))
    assert r.status == OperationStatus.FAILURE

@pytest.mark.asyncio
async def test_vcard_mock():
    with patch("contacts_driver.handlers.IS_MACOS", False):
        r = await contacts_vcard(req({"name": "Mike"}))
    assert r.data["ok"] is True
