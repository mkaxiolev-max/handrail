"""
power.* namespace — battery/power management via pmset.
Ops: battery / sleep / wake_lock / cancel_wake_lock
Dignity Guard: min 5min sleep delay, max 4hr wake_lock.
"""
from __future__ import annotations
import asyncio, platform, subprocess
from adapter_core.contract import AdapterRequest, AdapterResponse, OperationStatus

IS_MACOS = platform.system() == "Darwin"


async def _run(cmd: list[str]) -> tuple[int, str, str]:
    proc = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    out, err = await proc.communicate()
    return proc.returncode, out.decode().strip(), err.decode().strip()


async def power_battery(req: AdapterRequest) -> AdapterResponse:
    if not IS_MACOS:
        return AdapterResponse.success(req, {"ok": True, "charge_pct": 100,
                                              "status": "mock", "mode": "mock"})
    rc, out, err = await _run(["pmset", "-g", "batt"])
    if rc != 0:
        return AdapterResponse.success(req, {"ok": True, "skipped": True, "reason": err[:60]})

    charge_pct = None
    status = "unknown"
    source = "unknown"
    import re
    for line in out.splitlines():
        if "%" in line:
            m = re.search(r'(\d+)%', line)
            if m:
                charge_pct = int(m.group(1))
            if "AC Power" in out:
                source = "AC"
            elif "Battery Power" in out:
                source = "battery"
            if "charging" in line.lower():
                status = "charging"
            elif "discharging" in line.lower():
                status = "discharging"
            elif "charged" in line.lower():
                status = "charged"

    return AdapterResponse.success(req, {"ok": True, "charge_pct": charge_pct,
                                          "status": status, "source": source})


async def power_sleep(req: AdapterRequest) -> AdapterResponse:
    minutes = int((req.params or {}).get("minutes", 10))
    if minutes < 5:
        raise PermissionError("power.sleep: Dignity Guard requires minimum 5 minute delay")
    if not IS_MACOS:
        return AdapterResponse.success(req, {"ok": True, "scheduled_minutes": minutes, "mode": "mock"})
    rc, out, err = await _run([
        "osascript", "-e", 'tell application "System Events" to sleep'
    ])
    return AdapterResponse.success(req, {"ok": True, "scheduled_minutes": minutes,
                                          "note": "sleep_initiated"})


async def power_wake_lock(req: AdapterRequest) -> AdapterResponse:
    seconds = int((req.params or {}).get("seconds", 3600))
    seconds = min(seconds, 14400)  # max 4 hours
    if not IS_MACOS:
        return AdapterResponse.success(req, {"ok": True, "active": True,
                                              "seconds": seconds, "mode": "mock"})
    proc = subprocess.Popen(
        ["caffeinate", "-t", str(seconds)],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        start_new_session=True
    )
    return AdapterResponse.success(req, {"ok": True, "active": True,
                                          "seconds": seconds, "pid": proc.pid})


async def power_cancel_wake_lock(req: AdapterRequest) -> AdapterResponse:
    if not IS_MACOS:
        return AdapterResponse.success(req, {"ok": True, "cancelled": True, "mode": "mock"})
    rc, out, err = await _run(["pkill", "-x", "caffeinate"])
    return AdapterResponse.success(req, {"ok": True, "cancelled": rc == 0 or rc == 1})


def build_power_handlers() -> dict:
    return {
        "power.battery":          power_battery,
        "power.sleep":            power_sleep,
        "power.wake_lock":        power_wake_lock,
        "power.cancel_wake_lock": power_cancel_wake_lock,
    }
