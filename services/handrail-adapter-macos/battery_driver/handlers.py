"""
battery.* namespace
===================
macOS battery status via pmset.

Ops:
  battery.get_status       — {percent: int, charging: bool, time_remaining: str, health: str}
  battery.get_power_source — {source: str, ac_connected: bool}

Graceful skip if no battery (desktop) or not macOS.
"""
from __future__ import annotations
import asyncio, platform, re
from adapter_core.contract import AdapterRequest, AdapterResponse

IS_MACOS = platform.system() == "Darwin"


async def _run(cmd: list[str], timeout: float = 6.0) -> tuple[int, str, str]:
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        return proc.returncode, stdout.decode(errors="replace").strip(), stderr.decode(errors="replace").strip()
    except asyncio.TimeoutError:
        proc.kill()
        return -1, "", "TIMEOUT"


async def battery_get_status(req: AdapterRequest) -> AdapterResponse:
    if not IS_MACOS:
        return AdapterResponse.success(req, {
            "percent": 100, "charging": False, "time_remaining": "N/A", "health": "N/A",
            "skipped": True, "reason": "not_macos",
        })

    rc, out, _ = await _run(["pmset", "-g", "batt"])
    if rc != 0:
        return AdapterResponse.failure(req, "pmset -g batt failed")

    # No battery on desktop macs
    if "No battery" in out or "InternalBattery" not in out:
        return AdapterResponse.success(req, {
            "percent": 100, "charging": False, "time_remaining": "N/A", "health": "N/A",
            "skipped": True, "reason": "no_battery",
        })

    percent = 0
    m_pct = re.search(r"(\d+)%", out)
    if m_pct:
        percent = int(m_pct.group(1))

    charging = "charging" in out.lower() or "AC Power" in out
    if "discharging" in out.lower():
        charging = False

    time_remaining = "unknown"
    m_time = re.search(r"(\d+:\d+) remaining", out)
    if m_time:
        time_remaining = m_time.group(1)
    elif "calculating" in out.lower():
        time_remaining = "calculating"

    # Health from system_profiler (best-effort)
    health = "unknown"
    rc2, out2, _ = await _run(["system_profiler", "SPPowerDataType"])
    if rc2 == 0:
        m_h = re.search(r"Condition:\s*(.+)", out2)
        if m_h:
            health = m_h.group(1).strip()

    return AdapterResponse.success(req, {
        "percent": percent,
        "charging": charging,
        "time_remaining": time_remaining,
        "health": health,
    })


async def battery_get_power_source(req: AdapterRequest) -> AdapterResponse:
    if not IS_MACOS:
        return AdapterResponse.success(req, {
            "source": "AC Power", "ac_connected": True,
            "skipped": True, "reason": "not_macos",
        })

    rc, out, _ = await _run(["pmset", "-g", "ps"])
    if rc != 0:
        return AdapterResponse.failure(req, "pmset -g ps failed")

    ac_connected = "AC Power" in out
    source = "AC Power" if ac_connected else "Battery Power"
    m = re.search(r"'(.+)'", out)
    if m:
        source = m.group(1)

    return AdapterResponse.success(req, {"source": source, "ac_connected": ac_connected})


def build_battery_handlers() -> dict:
    return {
        "battery.get_status":       battery_get_status,
        "battery.get_power_source": battery_get_power_source,
    }
