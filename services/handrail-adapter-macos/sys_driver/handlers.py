"""
sys.* namespace
===============
macOS system metrics — disk, memory, uptime.

Ops:
  sys.disk_usage   — {total, used, free, pct} for /
  sys.memory       — {total, used, free, pct} via vm_stat
  sys.uptime       — {uptime_str, boot_time}
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


async def sys_disk_usage(req: AdapterRequest) -> AdapterResponse:
    path = (req.params or {}).get("path", "/")
    if not IS_MACOS:
        return AdapterResponse.success(req, {"ok": True, "path": path, "mode": "mock"})
    rc, out, err = await _run(["df", "-H", path])
    if rc != 0:
        return AdapterResponse.failure(req, err)
    lines = out.splitlines()
    if len(lines) < 2:
        return AdapterResponse.failure(req, "unexpected df output")
    parts = lines[1].split()
    return AdapterResponse.success(req, {"ok": True, "path": path,
                                         "total": parts[1] if len(parts) > 1 else "?",
                                         "used": parts[2] if len(parts) > 2 else "?",
                                         "free": parts[3] if len(parts) > 3 else "?",
                                         "pct": parts[4] if len(parts) > 4 else "?"})


async def sys_memory(req: AdapterRequest) -> AdapterResponse:
    if not IS_MACOS:
        return AdapterResponse.success(req, {"ok": True, "mode": "mock"})
    rc, out, err = await _run(["vm_stat"])
    if rc != 0:
        return AdapterResponse.failure(req, err)
    lines = out.splitlines()
    stats = {}
    for line in lines[1:]:
        if ":" in line:
            k, v = line.split(":", 1)
            stats[k.strip()] = v.strip().rstrip(".")
    page_size = 16384
    try:
        free = int(stats.get("Pages free", "0")) * page_size
        active = int(stats.get("Pages active", "0")) * page_size
        wired = int(stats.get("Pages wired down", "0")) * page_size
        used = active + wired
        total = used + free
        pct = round(used / total * 100, 1) if total > 0 else 0
    except (ValueError, ZeroDivisionError):
        free = used = total = pct = 0
    return AdapterResponse.success(req, {"ok": True,
                                          "total_gb": round(total / 1e9, 2),
                                          "used_gb": round(used / 1e9, 2),
                                          "free_gb": round(free / 1e9, 2),
                                          "pct_used": pct})


async def sys_uptime(req: AdapterRequest) -> AdapterResponse:
    if not IS_MACOS:
        return AdapterResponse.success(req, {"ok": True, "uptime_str": "mock", "mode": "mock"})
    rc, out, err = await _run(["uptime"])
    if rc != 0:
        return AdapterResponse.failure(req, err)
    rc2, boot, _ = await _run(["sysctl", "-n", "kern.boottime"])
    return AdapterResponse.success(req, {"ok": True, "uptime_str": out, "boot_raw": boot})


def build_sys_handlers() -> dict:
    return {
        "sys.disk_usage": sys_disk_usage,
        "sys.memory":     sys_memory,
        "sys.uptime":     sys_uptime,
    }
