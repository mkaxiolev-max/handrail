"""
Tests for battery.* namespace handlers.
All subprocess calls are monkeypatched — no real battery required.
"""
from __future__ import annotations
from unittest.mock import AsyncMock, patch
import pytest

from adapter_core.contract import AdapterRequest, OperationStatus
from battery_driver.handlers import (
    battery_get_status,
    battery_get_power_source,
    build_battery_handlers,
)


def _req(method: str, **params) -> AdapterRequest:
    return AdapterRequest(method=method, params=params)

_PMSET_BATT_CHARGING = (
    "Now drawing from 'AC Power'\n"
    " -InternalBattery-0 (id=12345678)\t78%; charging; 1:23 remaining present: true"
)

_PMSET_BATT_DISCHARGING = (
    "Now drawing from 'Battery Power'\n"
    " -InternalBattery-0 (id=12345678)\t54%; discharging; 2:45 remaining present: true"
)

_PMSET_BATT_NO_BATTERY = "Now drawing from 'AC Power'\n No battery"

_SYSTEM_PROFILER_POWER = (
    "Power:\n"
    "  Battery Information:\n"
    "    Model Information:\n"
    "    Condition: Normal\n"
)


# ── battery.get_status ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_battery_status_charging():
    with patch("battery_driver.handlers.IS_MACOS", True), \
         patch("battery_driver.handlers._run", new_callable=AsyncMock) as mock_run:
        mock_run.side_effect = [
            (0, _PMSET_BATT_CHARGING, ""),
            (0, _SYSTEM_PROFILER_POWER, ""),
        ]
        resp = await battery_get_status(_req("battery.get_status"))

    assert resp.status == OperationStatus.SUCCESS
    assert resp.data["percent"] == 78
    assert resp.data["charging"] is True
    assert resp.data["time_remaining"] == "1:23"
    assert resp.data["health"] == "Normal"


@pytest.mark.asyncio
async def test_battery_status_discharging():
    with patch("battery_driver.handlers.IS_MACOS", True), \
         patch("battery_driver.handlers._run", new_callable=AsyncMock) as mock_run:
        mock_run.side_effect = [
            (0, _PMSET_BATT_DISCHARGING, ""),
            (0, _SYSTEM_PROFILER_POWER, ""),
        ]
        resp = await battery_get_status(_req("battery.get_status"))

    assert resp.status == OperationStatus.SUCCESS
    assert resp.data["percent"] == 54
    assert resp.data["charging"] is False
    assert resp.data["time_remaining"] == "2:45"


@pytest.mark.asyncio
async def test_battery_status_no_battery():
    with patch("battery_driver.handlers.IS_MACOS", True), \
         patch("battery_driver.handlers._run", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = (0, _PMSET_BATT_NO_BATTERY, "")
        resp = await battery_get_status(_req("battery.get_status"))

    assert resp.status == OperationStatus.SUCCESS
    assert resp.data["skipped"] is True
    assert resp.data["reason"] == "no_battery"


@pytest.mark.asyncio
async def test_battery_status_non_macos():
    with patch("battery_driver.handlers.IS_MACOS", False):
        resp = await battery_get_status(_req("battery.get_status"))

    assert resp.status == OperationStatus.SUCCESS
    assert resp.data["skipped"] is True
    assert resp.data["reason"] == "not_macos"


@pytest.mark.asyncio
async def test_battery_status_pmset_failure():
    with patch("battery_driver.handlers.IS_MACOS", True), \
         patch("battery_driver.handlers._run", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = (1, "", "pmset error")
        resp = await battery_get_status(_req("battery.get_status"))

    assert resp.status == OperationStatus.FAILURE
    assert "pmset" in resp.error


# ── battery.get_power_source ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_power_source_ac():
    with patch("battery_driver.handlers.IS_MACOS", True), \
         patch("battery_driver.handlers._run", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = (0, "Now drawing from 'AC Power'", "")
        resp = await battery_get_power_source(_req("battery.get_power_source"))

    assert resp.status == OperationStatus.SUCCESS
    assert resp.data["ac_connected"] is True
    assert resp.data["source"] == "AC Power"


@pytest.mark.asyncio
async def test_power_source_battery():
    with patch("battery_driver.handlers.IS_MACOS", True), \
         patch("battery_driver.handlers._run", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = (0, "Now drawing from 'Battery Power'", "")
        resp = await battery_get_power_source(_req("battery.get_power_source"))

    assert resp.status == OperationStatus.SUCCESS
    assert resp.data["ac_connected"] is False
    assert resp.data["source"] == "Battery Power"


@pytest.mark.asyncio
async def test_power_source_non_macos():
    with patch("battery_driver.handlers.IS_MACOS", False):
        resp = await battery_get_power_source(_req("battery.get_power_source"))

    assert resp.status == OperationStatus.SUCCESS
    assert resp.data["skipped"] is True
    assert resp.data["reason"] == "not_macos"


@pytest.mark.asyncio
async def test_power_source_pmset_failure():
    with patch("battery_driver.handlers.IS_MACOS", True), \
         patch("battery_driver.handlers._run", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = (1, "", "error")
        resp = await battery_get_power_source(_req("battery.get_power_source"))

    assert resp.status == OperationStatus.FAILURE
    assert "pmset" in resp.error


# ── registry ──────────────────────────────────────────────────────────────────

def test_build_battery_handlers_keys():
    handlers = build_battery_handlers()
    assert set(handlers.keys()) == {"battery.get_status", "battery.get_power_source"}
    for fn in handlers.values():
        assert callable(fn)
