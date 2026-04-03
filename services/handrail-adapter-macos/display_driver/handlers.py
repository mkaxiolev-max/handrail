"""
display.* namespace
===================
macOS display info and brightness control.

Ops:
  display.get_info          — {screens: int, main_resolution: str, brightness: float}
  display.set_brightness    — {ok: bool, brightness_set: float}
  display.screenshot_info   — {width: int, height: int, scale: float}

Dignity Guard:
  display.set_brightness: brightness must be 0.0–1.0 (PermissionError otherwise)

Graceful skip on non-macOS or missing Quartz.
"""
from __future__ import annotations
import asyncio, platform, re
from adapter_core.contract import AdapterRequest, AdapterResponse

IS_MACOS = platform.system() == "Darwin"

_BRIGHTNESS_SCRIPT = 'tell application "System Events" to get brightness of (first desktop)'
_SET_BRIGHTNESS_SCRIPT = 'tell application "System Events" to set brightness of (first desktop) to {value}'


async def _run(cmd: list[str], timeout: float = 8.0) -> tuple[int, str, str]:
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


async def display_get_info(req: AdapterRequest) -> AdapterResponse:
    if not IS_MACOS:
        return AdapterResponse.success(req, {
            "screens": 1, "main_resolution": "1920x1080", "brightness": 0.8,
            "skipped": True, "reason": "not_macos",
        })

    rc, out, err = await _run(["system_profiler", "SPDisplaysDataType"])
    screens = 0
    main_resolution = ""
    if rc == 0:
        screens = out.count("Resolution:")
        m = re.search(r"Resolution:\s*(\d+)\s*x\s*(\d+)", out)
        if m:
            main_resolution = f"{m.group(1)}x{m.group(2)}"

    # Get brightness via osascript (best-effort)
    rc_b, out_b, _ = await _run(["osascript", "-e", _BRIGHTNESS_SCRIPT])
    brightness = 0.0
    if rc_b == 0:
        try:
            brightness = float(out_b)
        except ValueError:
            brightness = 0.0

    return AdapterResponse.success(req, {
        "screens": max(screens, 1),
        "main_resolution": main_resolution or "unknown",
        "brightness": brightness,
    })


async def display_set_brightness(req: AdapterRequest) -> AdapterResponse:
    brightness_raw = req.params.get("brightness")
    if brightness_raw is None:
        return AdapterResponse.failure(req, "params.brightness required")

    try:
        brightness = float(brightness_raw)
    except (TypeError, ValueError):
        return AdapterResponse.failure(req, "params.brightness must be a float")

    # Dignity Guard
    if not (0.0 <= brightness <= 1.0):
        raise PermissionError(f"display.set_brightness: {brightness} out of allowed range 0.0–1.0")

    if not IS_MACOS:
        return AdapterResponse.success(req, {"ok": True, "brightness_set": brightness, "skipped": True, "reason": "not_macos"})

    script = _SET_BRIGHTNESS_SCRIPT.replace("{value}", str(brightness))
    rc, _, err = await _run(["osascript", "-e", script])
    if rc != 0:
        return AdapterResponse.failure(req, f"osascript error: {err}")

    return AdapterResponse.success(req, {"ok": True, "brightness_set": brightness})


async def display_screenshot_info(req: AdapterRequest) -> AdapterResponse:
    if not IS_MACOS:
        return AdapterResponse.success(req, {
            "width": 1920, "height": 1080, "scale": 1.0,
            "skipped": True, "reason": "not_macos",
        })

    quartz_script = (
        "import Quartz; "
        "m = Quartz.CGDisplayBounds(Quartz.CGMainDisplayID()); "
        "s = Quartz.CGDisplayScreenSize(Quartz.CGMainDisplayID()); "
        "b = Quartz.CGDisplayBounds(Quartz.CGMainDisplayID()); "
        "sw = int(b.size.width); sh = int(b.size.height); "
        "scale = Quartz.CGDisplayScaleFactor(Quartz.CGMainDisplayID()); "
        "print(f'{sw},{sh},{scale}')"
    )
    rc, out, err = await _run(["python3", "-c", quartz_script])
    if rc != 0:
        return AdapterResponse.success(req, {
            "width": 0, "height": 0, "scale": 1.0,
            "skipped": True, "reason": "quartz_not_available",
        })

    parts = out.split(",")
    if len(parts) != 3:
        return AdapterResponse.failure(req, f"unexpected Quartz output: {out!r}")

    try:
        return AdapterResponse.success(req, {
            "width": int(parts[0]),
            "height": int(parts[1]),
            "scale": float(parts[2]),
        })
    except ValueError:
        return AdapterResponse.failure(req, f"could not parse Quartz output: {out!r}")


def build_display_handlers() -> dict:
    return {
        "display.get_info":         display_get_info,
        "display.set_brightness":   display_set_brightness,
        "display.screenshot_info":  display_screenshot_info,
    }
