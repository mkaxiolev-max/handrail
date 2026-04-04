"""Tests for calendar.* namespace."""
from __future__ import annotations
from unittest.mock import AsyncMock, patch
import pytest
from adapter_core.contract import AdapterRequest, OperationStatus
from calendar_driver.handlers import calendar_list, calendar_today, calendar_upcoming

def req(params=None):
    return AdapterRequest(method="POST", params=params or {})

@pytest.mark.asyncio
async def test_list_mock():
    with patch("calendar_driver.handlers.IS_MACOS", False):
        r = await calendar_list(req())
    assert r.data["ok"] is True
    assert r.data["calendars"] == []

@pytest.mark.asyncio
async def test_list_live():
    with patch("calendar_driver.handlers.IS_MACOS", True), \
         patch("calendar_driver.handlers._run", new=AsyncMock(return_value=(0, "Work, Personal, Home", ""))):
        r = await calendar_list(req())
    assert r.data["count"] == 3
    assert "Work" in r.data["calendars"]

@pytest.mark.asyncio
async def test_list_denied():
    with patch("calendar_driver.handlers.IS_MACOS", True), \
         patch("calendar_driver.handlers._run", new=AsyncMock(return_value=(1, "", "not allowed"))):
        r = await calendar_list(req())
    assert r.data["skipped"] is True

@pytest.mark.asyncio
async def test_today_mock():
    with patch("calendar_driver.handlers.IS_MACOS", False):
        r = await calendar_today(req())
    assert r.data["ok"] is True

@pytest.mark.asyncio
async def test_today_live():
    with patch("calendar_driver.handlers.IS_MACOS", True), \
         patch("calendar_driver.handlers._run", new=AsyncMock(return_value=(0, "Team standup @ Friday 10am, Lunch @ 12pm", ""))):
        r = await calendar_today(req())
    assert r.data["ok"] is True
    assert r.data["count"] >= 1

@pytest.mark.asyncio
async def test_upcoming_mock():
    with patch("calendar_driver.handlers.IS_MACOS", False):
        r = await calendar_upcoming(req({"n": 3}))
    assert r.data["ok"] is True

@pytest.mark.asyncio
async def test_upcoming_live():
    with patch("calendar_driver.handlers.IS_MACOS", True), \
         patch("calendar_driver.handlers._run", new=AsyncMock(return_value=(0, "Meeting|Mon 9am, Review|Tue 2pm", ""))):
        r = await calendar_upcoming(req({"n": 5}))
    assert r.data["count"] <= 5
