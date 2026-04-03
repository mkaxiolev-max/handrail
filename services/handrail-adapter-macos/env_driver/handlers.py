"""
env.* namespace
===============
macOS environment interrogation — health, capabilities, version, permission state.

Ops:
  env.health        — {ok, mode, platform, sw_vers}
  env.capabilities  — {capabilities: list, count: int}
  env.version       — {version, build, platform}
  env.permissions   — {permissions: dict, all_granted: bool, missing: list}

Dignity Guard:
  env.permissions probes screen_recording, accessibility, and automation.
  Graceful skip on non-macOS. All subprocess errors caught individually.
"""
from __future__ import annotations
import asyncio, platform
from adapter_core.contract import AdapterRequest, AdapterResponse

IS_MACOS = platform.system() == "Darwin"
_BUILD = "2026.04.03"


async def _run(cmd: list[str], timeout: float = 5.0) -> tuple[int, str, str]:
    proc = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    try:
        out, err = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        return proc.returncode, out.decode().strip(), err.decode().strip()
    except asyncio.TimeoutError:
        proc.kill()
        return -1, "", "TIMEOUT"


async def _probe(cmd: list[str]) -> bool:
    """Run cmd, return True iff rc == 0. Catches all exceptions."""
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        await proc.wait()
        return proc.returncode == 0
    except Exception:
        return False


async def env_health(req: AdapterRequest) -> AdapterResponse:
    if not IS_MACOS:
        return AdapterResponse.success(req, {
            "ok": True, "mode": "mock",
            "platform": platform.system(), "adapter_version": "adapter.v1",
        })
    rc, sw, _ = await _run(["sw_vers"])
    return AdapterResponse.success(req, {
        "ok": rc == 0, "mode": "live",
        "platform": platform.system(),
        "sw_vers": sw, "adapter_version": "adapter.v1",
    })


async def env_capabilities(req: AdapterRequest) -> AdapterResponse:
    from adapter_core.capability_registry import get_capabilities
    caps = get_capabilities()
    return AdapterResponse.success(req, {
        "capabilities": caps,
        "count": len(caps),
    })


async def env_version(req: AdapterRequest) -> AdapterResponse:
    return AdapterResponse.success(req, {
        "version": "adapter.v1",
        "build": _BUILD,
        "platform": platform.system(),
    })


async def env_permissions(req: AdapterRequest) -> AdapterResponse:
    if not IS_MACOS:
        return AdapterResponse.success(req, {"skipped": True, "reason": "not_macos"})

    # Probe each permission independently — failure of one doesn't abort others
    screen_recording = await _probe([
        "python3", "-c",
        "import Quartz; Quartz.CGDisplayCreateImage(Quartz.CGMainDisplayID())",
    ])
    accessibility = await _probe([
        "osascript", "-e",
        'tell application "System Events" to get name of first process',
    ])
    automation = await _probe(["osascript", "-e", "return 1"])

    perms = {
        "screen_recording": screen_recording,
        "accessibility": accessibility,
        "automation": automation,
    }
    missing = [k for k, v in perms.items() if not v]
    return AdapterResponse.success(req, {
        "permissions": perms,
        "all_granted": len(missing) == 0,
        "missing": missing,
    })


def build_env_handlers() -> dict:
    return {
        "env.health":       env_health,
        "env.capabilities": env_capabilities,
        "env.version":      env_version,
        "env.permissions":  env_permissions,
    }
