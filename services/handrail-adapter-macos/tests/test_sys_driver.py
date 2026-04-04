"""Tests for sys.* namespace."""
from __future__ import annotations
from unittest.mock import AsyncMock, patch
import pytest
from adapter_core.contract import AdapterRequest, OperationStatus
from sys_driver.handlers import sys_disk_usage, sys_memory, sys_uptime

def req(params=None):
    return AdapterRequest(method="POST", params=params or {})

@pytest.mark.asyncio
async def test_disk_usage_mock():
    with patch("sys_driver.handlers.IS_MACOS", False):
        r = await sys_disk_usage(req())
    assert r.data["ok"] is True

@pytest.mark.asyncio
async def test_disk_usage_live():
    df_out = "Filesystem   Size  Used Avail Use% Mounted on\n/dev/disk3  460G  220G  240G  48% /"
    with patch("sys_driver.handlers.IS_MACOS", True), \
         patch("sys_driver.handlers._run", new=AsyncMock(return_value=(0, df_out, ""))):
        r = await sys_disk_usage(req({"path": "/"}))
    assert r.data["total"] == "460G"
    assert r.data["pct"] == "48%"

@pytest.mark.asyncio
async def test_memory_mock():
    with patch("sys_driver.handlers.IS_MACOS", False):
        r = await sys_memory(req())
    assert r.data["ok"] is True

@pytest.mark.asyncio
async def test_memory_live():
    vm_out = """Mach Virtual Memory Statistics:
Pages free:                         100000.
Pages active:                       200000.
Pages wired down:                    50000."""
    with patch("sys_driver.handlers.IS_MACOS", True), \
         patch("sys_driver.handlers._run", new=AsyncMock(return_value=(0, vm_out, ""))):
        r = await sys_memory(req())
    assert r.data["ok"] is True
    assert "pct_used" in r.data

@pytest.mark.asyncio
async def test_uptime_mock():
    with patch("sys_driver.handlers.IS_MACOS", False):
        r = await sys_uptime(req())
    assert r.data["ok"] is True

@pytest.mark.asyncio
async def test_uptime_live():
    with patch("sys_driver.handlers.IS_MACOS", True), \
         patch("sys_driver.handlers._run", new=AsyncMock(side_effect=[
             (0, "18:30  up 3 days,  4:12, 2 users, load averages: 1.20 1.15 1.10", ""),
             (0, "{ sec = 1743600000, usec = 0 } Fri Apr  3 15:00:00 2026", "")
         ])):
        r = await sys_uptime(req())
    assert "uptime_str" in r.data
