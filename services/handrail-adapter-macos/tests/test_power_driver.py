"""Tests for power.* namespace."""
from __future__ import annotations
from unittest.mock import AsyncMock, patch, MagicMock
import pytest
from adapter_core.contract import AdapterRequest, OperationStatus
from power_driver.handlers import power_battery, power_sleep, power_wake_lock, power_cancel_wake_lock

def req(params=None):
    return AdapterRequest(method="POST", params=params or {})

@pytest.mark.asyncio
async def test_battery_mock():
    with patch("power_driver.handlers.IS_MACOS", False):
        r = await power_battery(req())
    assert r.data["charge_pct"] == 100

@pytest.mark.asyncio
async def test_battery_live():
    pmset_out = "Now drawing from 'AC Power'\n -InternalBattery-0 (id=1234)    89%; charging; 1:30 remaining"
    with patch("power_driver.handlers.IS_MACOS", True), \
         patch("power_driver.handlers._run", new=AsyncMock(return_value=(0, pmset_out, ""))):
        r = await power_battery(req())
    assert r.data["ok"] is True
    assert r.data["charge_pct"] == 89

@pytest.mark.asyncio
async def test_sleep_dignity_guard():
    with pytest.raises(PermissionError):
        await power_sleep(req({"minutes": 2}))

@pytest.mark.asyncio
async def test_sleep_ok_mock():
    with patch("power_driver.handlers.IS_MACOS", False):
        r = await power_sleep(req({"minutes": 10}))
    assert r.data["scheduled_minutes"] == 10

@pytest.mark.asyncio
async def test_wake_lock_mock():
    with patch("power_driver.handlers.IS_MACOS", False):
        r = await power_wake_lock(req({"seconds": 3600}))
    assert r.data["active"] is True

@pytest.mark.asyncio
async def test_wake_lock_max_capped():
    with patch("power_driver.handlers.IS_MACOS", False):
        r = await power_wake_lock(req({"seconds": 999999}))
    assert r.data["seconds"] == 14400

@pytest.mark.asyncio
async def test_cancel_wake_lock_mock():
    with patch("power_driver.handlers.IS_MACOS", False):
        r = await power_cancel_wake_lock(req())
    assert r.data["cancelled"] is True
