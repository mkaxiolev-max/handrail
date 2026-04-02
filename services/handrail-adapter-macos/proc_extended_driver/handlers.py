"""
proc_extended.* namespace
==========================
Process inspection and signalling.

Methods:
  proc_extended.list_processes   — ps aux, optionally filtered
  proc_extended.kill_pid         — send signal to pid (TERM/KILL/HUP)
  proc_extended.get_memory_usage — per-pid RSS/VSZ or system vm_stat

Safety invariant (Dignity Guard in this handler):
  kill_pid refuses pid <= 100 — these are kernel/system processes.
  The Dignity Kernel pre-check in server.py also gates every call.

Contract: every handler returns AdapterResponse.
"""
from __future__ import annotations
import asyncio, os, platform, signal as _signal, time
from adapter_core.contract import AdapterRequest, AdapterResponse

IS_MACOS = platform.system() == "Darwin"

_ALLOWED_SIGNALS = {
    "TERM": _signal.SIGTERM,
    "KILL": _signal.SIGKILL,
    "HUP":  _signal.SIGHUP,
}

# Minimum safe PID — never signal processes at or below this value
_PID_FLOOR = 100


async def _run(cmd: list[str], timeout: float = 5.0) -> tuple[int, str, str]:
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        return proc.returncode, stdout.decode().strip(), stderr.decode().strip()
    except asyncio.TimeoutError:
        proc.kill()
        return -1, "", "TIMEOUT"


async def proc_list_processes(req: AdapterRequest) -> AdapterResponse:
    limit: int = int(req.params.get("limit", 50))
    filter_str: str = req.params.get("filter", "")

    rc, out, err = await _run(["ps", "aux"])
    if rc != 0:
        return AdapterResponse.failure(req, f"ps_failed: {err}")

    lines = out.splitlines()
    if len(lines) < 2:
        return AdapterResponse.success(req, {"processes": [], "count": 0})

    processes: list[dict] = []
    for line in lines[1:]:  # skip header row
        parts = line.split(None, 10)
        if len(parts) < 11:
            continue
        command = parts[10].strip()
        if filter_str and filter_str.lower() not in command.lower():
            continue
        try:
            processes.append({
                "user":    parts[0],
                "pid":     int(parts[1]),
                "cpu_pct": float(parts[2]),
                "mem_pct": float(parts[3]),
                "command": command[:200],
            })
        except (ValueError, IndexError):
            continue

    total = len(processes)
    return AdapterResponse.success(req, {
        "processes": processes[:limit],
        "count": total,
        "truncated": total > limit,
    })


async def proc_kill_pid(req: AdapterRequest) -> AdapterResponse:
    pid_raw = req.params.get("pid")
    if pid_raw is None:
        return AdapterResponse.failure(req, "params.pid required")

    pid = int(pid_raw)
    sig_name: str = str(req.params.get("signal", "TERM")).upper()

    # Dignity Guard — refuse to signal kernel/system-range PIDs
    if pid <= _PID_FLOOR:
        return AdapterResponse.failure(
            req, f"DIGNITY_GUARD: pid {pid} <= {_PID_FLOOR} is a protected system process"
        )

    sig = _ALLOWED_SIGNALS.get(sig_name)
    if sig is None:
        return AdapterResponse.failure(
            req, f"UNKNOWN_SIGNAL: {sig_name!r}. Allowed: {', '.join(_ALLOWED_SIGNALS)}"
        )

    try:
        os.kill(pid, sig)
    except ProcessLookupError:
        return AdapterResponse.failure(req, f"PROCESS_NOT_FOUND: pid {pid}")
    except PermissionError:
        return AdapterResponse.failure(req, f"PERMISSION_DENIED: cannot signal pid {pid}")

    return AdapterResponse.success(req, {"pid": pid, "signal": sig_name, "killed": True})


async def proc_get_memory_usage(req: AdapterRequest) -> AdapterResponse:
    pid_raw = req.params.get("pid")

    # ── Per-process mode ──────────────────────────────────────────────────────
    if pid_raw is not None:
        pid = int(pid_raw)
        rc, out, err = await _run(["ps", "-p", str(pid), "-o", "pid=,rss=,vsz="])
        if rc != 0:
            return AdapterResponse.failure(req, f"PROCESS_NOT_FOUND: pid {pid}")
        parts = out.strip().split()
        if len(parts) < 3:
            return AdapterResponse.failure(req, f"PROCESS_NOT_FOUND: pid {pid}")
        return AdapterResponse.success(req, {
            "pid":       int(parts[0]),
            "rss_bytes": int(parts[1]) * 1024,
            "vsz_bytes": int(parts[2]) * 1024,
        })

    # ── System mode ───────────────────────────────────────────────────────────
    if not IS_MACOS:
        return AdapterResponse.success(req, {
            "system": True,
            "total_bytes": 0,
            "used_bytes": 0,
            "free_bytes": 0,
            "percent_used": 0.0,
            "mock": True,
        })

    rc, out, err = await _run(["vm_stat"])
    if rc != 0:
        return AdapterResponse.failure(req, f"vm_stat_failed: {err}")

    _PAGE = 4096  # macOS default page size
    stats: dict[str, int] = {}
    for line in out.splitlines():
        if ":" not in line:
            continue
        key, val = line.split(":", 1)
        try:
            stats[key.strip()] = int(val.strip().rstrip("."))
        except ValueError:
            pass

    pages_free     = stats.get("Pages free", 0)
    pages_active   = stats.get("Pages active", 0)
    pages_inactive = stats.get("Pages inactive", 0)
    pages_wired    = stats.get("Pages wired down", 0)

    total_pages = pages_free + pages_active + pages_inactive + pages_wired
    used_pages  = pages_active + pages_inactive + pages_wired

    total_bytes = total_pages * _PAGE
    used_bytes  = used_pages  * _PAGE
    free_bytes  = pages_free  * _PAGE

    return AdapterResponse.success(req, {
        "system":       True,
        "total_bytes":  total_bytes,
        "used_bytes":   used_bytes,
        "free_bytes":   free_bytes,
        "percent_used": round(used_bytes / total_bytes * 100, 1) if total_bytes else 0.0,
    })


def build_proc_extended_handlers() -> dict:
    return {
        "proc_extended.list_processes":  proc_list_processes,
        "proc_extended.kill_pid":        proc_kill_pid,
        "proc_extended.get_memory_usage": proc_get_memory_usage,
    }
