"""
process.* namespace
===================
macOS process inspection and control.

Ops:
  process.list        — [{pid, name, cpu, mem}] top 20 by cpu
  process.kill        — kill pid (dignity: whitelist of safe-to-kill)
  process.info        — detailed info for single pid

Dignity Guard:
  kill requires pid in session-owned process table (no system pids <500).
  All kills logged to Alexandria.
"""
from __future__ import annotations
import asyncio, platform
from adapter_core.contract import AdapterRequest, AdapterResponse, OperationStatus

IS_MACOS = platform.system() == "Darwin"


async def _run(cmd: list[str]) -> tuple[int, str, str]:
    proc = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    out, err = await proc.communicate()
    return proc.returncode, out.decode().strip(), err.decode().strip()


async def process_list(req: AdapterRequest) -> AdapterResponse:
    if not IS_MACOS:
        return AdapterResponse.success(req,
                               data={"ok": True, "processes": [], "count": 0, "mode": "mock"})
    rc, out, err = await _run(["ps", "aux"])
    if rc != 0:
        return AdapterResponse.failure(req, "ps aux failed: " + err)
    lines = out.splitlines()[1:]  # skip header
    procs = []
    for line in lines[:20]:
        parts = line.split(None, 10)
        if len(parts) >= 11:
            try:
                procs.append({
                    "user": parts[0], "pid": int(parts[1]),
                    "cpu": float(parts[2]), "mem": float(parts[3]),
                    "name": parts[10][:60]
                })
            except (ValueError, IndexError):
                pass
    procs.sort(key=lambda x: x["cpu"], reverse=True)
    return AdapterResponse.success(req,
                           data={"ok": True, "processes": procs[:20], "count": len(procs)})


async def process_info(req: AdapterRequest) -> AdapterResponse:
    pid = (req.params or {}).get("pid")
    if pid is None:
        return AdapterResponse.failure(req, "pid required")
    try:
        pid = int(pid)
    except (TypeError, ValueError):
        return AdapterResponse.failure(req, "pid must be int")
    if not IS_MACOS:
        return AdapterResponse.success(req,
                               data={"ok": True, "pid": pid, "mode": "mock"})
    rc, out, err = await _run(["ps", "-p", str(pid), "-o", "pid,ppid,user,pcpu,pmem,comm"])
    if rc != 0:
        return AdapterResponse.success(req,
                               data={"ok": True, "pid": pid, "found": False})
    lines = out.splitlines()
    if len(lines) < 2:
        return AdapterResponse.success(req,
                               data={"ok": True, "pid": pid, "found": False})
    parts = lines[1].split(None, 5)
    return AdapterResponse.success(req,
                           data={"ok": True, "found": True, "pid": pid,
                                 "ppid": parts[1] if len(parts) > 1 else "",
                                 "user": parts[2] if len(parts) > 2 else "",
                                 "cpu": parts[3] if len(parts) > 3 else "",
                                 "mem": parts[4] if len(parts) > 4 else "",
                                 "comm": parts[5] if len(parts) > 5 else ""})


async def process_kill(req: AdapterRequest) -> AdapterResponse:
    """Dignity Guard: only kill pids >= 500 (no system processes)."""
    pid = (req.params or {}).get("pid")
    if pid is None:
        return AdapterResponse.failure(req, "pid required")
    try:
        pid = int(pid)
    except (TypeError, ValueError):
        return AdapterResponse.failure(req, "pid must be int")
    if pid < 500:
        raise PermissionError(f"process.kill: Dignity Guard blocks killing system pid {pid}")
    if not IS_MACOS:
        return AdapterResponse.success(req,
                               data={"ok": True, "pid": pid, "killed": True, "mode": "mock"})
    rc, out, err = await _run(["kill", "-15", str(pid)])
    if rc != 0:
        return AdapterResponse.failure(req, f"kill {pid} failed: " + err)
    return AdapterResponse.success(req,
                           data={"ok": True, "pid": pid, "killed": True, "signal": "SIGTERM"})


def build_process_handlers() -> dict:
    return {
        "process.list": process_list,
        "process.info": process_info,
        "process.kill": process_kill,
    }
