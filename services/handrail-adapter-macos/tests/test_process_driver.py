"""Tests for process.* namespace."""
from __future__ import annotations
from unittest.mock import AsyncMock, patch
import pytest
from adapter_core.contract import AdapterRequest, OperationStatus
from process_driver.handlers import process_list, process_info, process_kill

def req(params=None):
    return AdapterRequest(method="POST", params=params or {})

@pytest.mark.asyncio
async def test_process_list_mock():
    with patch("process_driver.handlers.IS_MACOS", False):
        r = await process_list(req())
    assert r.status == OperationStatus.SUCCESS
    assert r.data["ok"] is True

@pytest.mark.asyncio
async def test_process_list_live():
    ps_out = "USER PID %CPU %MEM VSZ RSS TT STAT STARTED TIME COMMAND\naxiolev 1234 0.5 1.2 100 50 ?? S 0:00 /usr/bin/python3 test"
    with patch("process_driver.handlers.IS_MACOS", True), \
         patch("process_driver.handlers._run", new=AsyncMock(return_value=(0, ps_out, ""))):
        r = await process_list(req())
    assert r.status == OperationStatus.SUCCESS
    assert isinstance(r.data["processes"], list)

@pytest.mark.asyncio
async def test_process_info_no_pid():
    r = await process_info(req({}))
    assert r.status == OperationStatus.FAILURE

@pytest.mark.asyncio
async def test_process_info_found():
    ps_out = "PID PPID USER %CPU %MEM COMM\n1234 1 axiolev 0.1 0.5 python3"
    with patch("process_driver.handlers.IS_MACOS", True), \
         patch("process_driver.handlers._run", new=AsyncMock(return_value=(0, ps_out, ""))):
        r = await process_info(req({"pid": 1234}))
    assert r.status == OperationStatus.SUCCESS
    assert r.data["found"] is True

@pytest.mark.asyncio
async def test_process_info_not_found():
    with patch("process_driver.handlers.IS_MACOS", True), \
         patch("process_driver.handlers._run", new=AsyncMock(return_value=(1, "", "no process"))):
        r = await process_info(req({"pid": 99999}))
    assert r.status == OperationStatus.SUCCESS
    assert r.data["found"] is False

@pytest.mark.asyncio
async def test_process_kill_system_pid_blocked():
    with pytest.raises(PermissionError):
        await process_kill(req({"pid": 1}))

@pytest.mark.asyncio
async def test_process_kill_ok():
    with patch("process_driver.handlers.IS_MACOS", True), \
         patch("process_driver.handlers._run", new=AsyncMock(return_value=(0, "", ""))):
        r = await process_kill(req({"pid": 5000}))
    assert r.status == OperationStatus.SUCCESS
    assert r.data["killed"] is True

@pytest.mark.asyncio
async def test_process_kill_mock():
    with patch("process_driver.handlers.IS_MACOS", False):
        r = await process_kill(req({"pid": 5000}))
    assert r.data["killed"] is True

@pytest.mark.asyncio
async def test_process_kill_invalid_pid():
    r = await process_kill(req({"pid": "bad"}))
    assert r.status == OperationStatus.FAILURE
