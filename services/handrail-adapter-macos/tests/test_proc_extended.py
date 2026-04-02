"""
Tests for proc_extended.* namespace handlers.
subprocess calls are monkeypatched — no live processes harmed.
"""
from __future__ import annotations
import asyncio, signal as _signal
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from adapter_core.contract import AdapterRequest, OperationStatus
from proc_extended_driver.handlers import (
    proc_list_processes,
    proc_kill_pid,
    proc_get_memory_usage,
    build_proc_extended_handlers,
    _PID_FLOOR,
)


def _req(method: str, **params) -> AdapterRequest:
    return AdapterRequest(method=method, params=params)


PS_AUX_OUTPUT = """\
USER         PID  %CPU %MEM      VSZ    RSS   TT  STAT STARTED      TIME COMMAND
root           1   0.0  0.1  4294912  12345   ??  Ss   Mon01AM   0:01.23 /sbin/launchd
axiolevns   5001   1.2  0.4  4194304  50000   s1  S+   10:00AM   0:05.00 /usr/bin/python3 server.py
axiolevns   5002   0.0  0.1   409600   8000   s1  S    10:01AM   0:00.10 bash
"""


async def _fake_run_ps_aux(cmd, timeout=5.0):
    if cmd[0] == "ps" and "aux" in cmd:
        return 0, PS_AUX_OUTPUT.strip(), ""
    return 1, "", "unexpected command"


async def _fake_run_ps_p(cmd, timeout=5.0):
    # ps -p <pid> -o pid=,rss=,vsz=
    if cmd[0] == "ps" and "-p" in cmd:
        pid_idx = cmd.index("-p") + 1
        pid = int(cmd[pid_idx])
        if pid == 5001:
            return 0, "5001  50000 4194304", ""
        return 1, "", "no process"
    return 1, "", "unexpected"


async def _fake_run_vm_stat(cmd, timeout=5.0):
    if cmd == ["vm_stat"]:
        return 0, (
            "Mach Virtual Memory Statistics: (page size of 4096 bytes)\n"
            "Pages free:                           100000.\n"
            "Pages active:                         200000.\n"
            "Pages inactive:                        50000.\n"
            "Pages wired down:                      30000.\n"
        ), ""
    return 1, "", "unexpected"


# ── proc_extended.list_processes ─────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_processes_success():
    with patch("proc_extended_driver.handlers._run", side_effect=_fake_run_ps_aux):
        resp = await proc_list_processes(_req("proc_extended.list_processes"))

    assert resp.status == OperationStatus.SUCCESS
    procs = resp.data["processes"]
    # PID 1 (root launchd) + 5001 + 5002
    assert len(procs) == 3
    pids = [p["pid"] for p in procs]
    assert 5001 in pids
    assert 5002 in pids


@pytest.mark.asyncio
async def test_list_processes_filter():
    with patch("proc_extended_driver.handlers._run", side_effect=_fake_run_ps_aux):
        resp = await proc_list_processes(_req("proc_extended.list_processes", filter="python3"))

    assert resp.status == OperationStatus.SUCCESS
    procs = resp.data["processes"]
    assert len(procs) == 1
    assert procs[0]["pid"] == 5001


@pytest.mark.asyncio
async def test_list_processes_limit():
    with patch("proc_extended_driver.handlers._run", side_effect=_fake_run_ps_aux):
        resp = await proc_list_processes(_req("proc_extended.list_processes", limit=1))

    assert resp.status == OperationStatus.SUCCESS
    assert len(resp.data["processes"]) == 1
    assert resp.data["truncated"] is True


@pytest.mark.asyncio
async def test_list_processes_ps_failure():
    async def _fail(cmd, timeout=5.0):
        return 1, "", "permission denied"

    with patch("proc_extended_driver.handlers._run", side_effect=_fail):
        resp = await proc_list_processes(_req("proc_extended.list_processes"))

    assert resp.status == OperationStatus.FAILURE
    assert "ps_failed" in resp.error


# ── proc_extended.kill_pid ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_kill_pid_success():
    with patch("os.kill") as mock_kill:
        resp = await proc_kill_pid(_req("proc_extended.kill_pid", pid=5001))

    assert resp.status == OperationStatus.SUCCESS
    assert resp.data["pid"] == 5001
    assert resp.data["signal"] == "TERM"
    assert resp.data["killed"] is True
    mock_kill.assert_called_once_with(5001, _signal.SIGTERM)


@pytest.mark.asyncio
async def test_kill_pid_sigkill():
    with patch("os.kill") as mock_kill:
        resp = await proc_kill_pid(_req("proc_extended.kill_pid", pid=5001, signal="KILL"))

    assert resp.status == OperationStatus.SUCCESS
    mock_kill.assert_called_once_with(5001, _signal.SIGKILL)


@pytest.mark.asyncio
async def test_kill_pid_dignity_guard_rejects_low_pid():
    """Dignity Guard: must refuse any pid <= _PID_FLOOR."""
    for protected_pid in [1, 50, _PID_FLOOR]:
        with patch("os.kill") as mock_kill:
            resp = await proc_kill_pid(_req("proc_extended.kill_pid", pid=protected_pid))
        assert resp.status == OperationStatus.FAILURE
        assert "DIGNITY_GUARD" in resp.error
        mock_kill.assert_not_called()


@pytest.mark.asyncio
async def test_kill_pid_missing_pid():
    resp = await proc_kill_pid(_req("proc_extended.kill_pid"))
    assert resp.status == OperationStatus.FAILURE
    assert "params.pid required" in resp.error


@pytest.mark.asyncio
async def test_kill_pid_unknown_signal():
    resp = await proc_kill_pid(_req("proc_extended.kill_pid", pid=5001, signal="NUKE"))
    assert resp.status == OperationStatus.FAILURE
    assert "UNKNOWN_SIGNAL" in resp.error


@pytest.mark.asyncio
async def test_kill_pid_process_not_found():
    with patch("os.kill", side_effect=ProcessLookupError):
        resp = await proc_kill_pid(_req("proc_extended.kill_pid", pid=9999))
    assert resp.status == OperationStatus.FAILURE
    assert "PROCESS_NOT_FOUND" in resp.error


@pytest.mark.asyncio
async def test_kill_pid_permission_denied():
    with patch("os.kill", side_effect=PermissionError):
        resp = await proc_kill_pid(_req("proc_extended.kill_pid", pid=5001))
    assert resp.status == OperationStatus.FAILURE
    assert "PERMISSION_DENIED" in resp.error


# ── proc_extended.get_memory_usage ───────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_memory_usage_per_pid():
    with patch("proc_extended_driver.handlers._run", side_effect=_fake_run_ps_p):
        resp = await proc_get_memory_usage(_req("proc_extended.get_memory_usage", pid=5001))

    assert resp.status == OperationStatus.SUCCESS
    assert resp.data["pid"] == 5001
    assert resp.data["rss_bytes"] == 50000 * 1024
    assert resp.data["vsz_bytes"] == 4194304 * 1024


@pytest.mark.asyncio
async def test_get_memory_usage_pid_not_found():
    with patch("proc_extended_driver.handlers._run", side_effect=_fake_run_ps_p):
        resp = await proc_get_memory_usage(_req("proc_extended.get_memory_usage", pid=9999))
    assert resp.status == OperationStatus.FAILURE
    assert "PROCESS_NOT_FOUND" in resp.error


@pytest.mark.asyncio
async def test_get_memory_usage_system_macos():
    with patch("proc_extended_driver.handlers.IS_MACOS", True), \
         patch("proc_extended_driver.handlers._run", side_effect=_fake_run_vm_stat):
        resp = await proc_get_memory_usage(_req("proc_extended.get_memory_usage"))

    assert resp.status == OperationStatus.SUCCESS
    assert resp.data["system"] is True
    assert resp.data["total_bytes"] > 0
    assert 0.0 <= resp.data["percent_used"] <= 100.0


@pytest.mark.asyncio
async def test_get_memory_usage_system_mock_mode():
    with patch("proc_extended_driver.handlers.IS_MACOS", False):
        resp = await proc_get_memory_usage(_req("proc_extended.get_memory_usage"))

    assert resp.status == OperationStatus.SUCCESS
    assert resp.data["mock"] is True


# ── registry ─────────────────────────────────────────────────────────────────

def test_build_proc_extended_handlers_keys():
    handlers = build_proc_extended_handlers()
    assert set(handlers.keys()) == {
        "proc_extended.list_processes",
        "proc_extended.kill_pid",
        "proc_extended.get_memory_usage",
    }
    for fn in handlers.values():
        assert callable(fn)
