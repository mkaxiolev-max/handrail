"""Tests for reminders.* namespace."""
from __future__ import annotations
from unittest.mock import AsyncMock, patch
import pytest
from adapter_core.contract import AdapterRequest, OperationStatus
from reminders_driver.handlers import reminders_list, reminders_add, reminders_complete

def req(params=None):
    return AdapterRequest(method="POST", params=params or {})

@pytest.mark.asyncio
async def test_list_mock():
    with patch("reminders_driver.handlers.IS_MACOS", False):
        r = await reminders_list(req())
    assert r.data["ok"] is True

@pytest.mark.asyncio
async def test_list_live():
    with patch("reminders_driver.handlers.IS_MACOS", True), \
         patch("reminders_driver.handlers._run", new=AsyncMock(
             return_value=(0, "Buy milk, Call doctor, Review PR", ""))):
        r = await reminders_list(req())
    assert r.data["count"] == 3

@pytest.mark.asyncio
async def test_add_no_text():
    r = await reminders_add(req({}))
    assert r.status == OperationStatus.FAILURE

@pytest.mark.asyncio
async def test_add_mock():
    with patch("reminders_driver.handlers.IS_MACOS", False):
        r = await reminders_add(req({"text": "Test reminder"}))
    assert r.data["added"] is True

@pytest.mark.asyncio
async def test_add_live():
    with patch("reminders_driver.handlers.IS_MACOS", True), \
         patch("reminders_driver.handlers._run", new=AsyncMock(return_value=(0, "reminder 1", ""))):
        r = await reminders_add(req({"text": "Deploy NS"}))
    assert r.data["added"] is True

@pytest.mark.asyncio
async def test_complete_no_name():
    r = await reminders_complete(req({}))
    assert r.status == OperationStatus.FAILURE

@pytest.mark.asyncio
async def test_complete_ok():
    with patch("reminders_driver.handlers.IS_MACOS", True), \
         patch("reminders_driver.handlers._run", new=AsyncMock(return_value=(0, "ok", ""))):
        r = await reminders_complete(req({"name": "Deploy NS"}))
    assert r.data["completed"] is True

@pytest.mark.asyncio
async def test_complete_not_found():
    with patch("reminders_driver.handlers.IS_MACOS", True), \
         patch("reminders_driver.handlers._run", new=AsyncMock(return_value=(0, "not_found", ""))):
        r = await reminders_complete(req({"name": "Nonexistent"}))
    assert r.data["completed"] is False
