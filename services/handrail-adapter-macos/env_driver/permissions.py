# Copyright © 2026 Axiolev. All rights reserved.
"""env.permissions — report macOS entitlement state (screen recording, accessibility, automation)."""
from __future__ import annotations
import asyncio, platform
from adapter_core.contract import AdapterRequest, AdapterResponse, OperationStatus

IS_MACOS = platform.system() == "Darwin"


async def env_permissions(req: AdapterRequest) -> AdapterResponse:
    if not IS_MACOS:
        return AdapterResponse.success(req, {"skipped": True, "reason": "not_macos",
                                             "permissions": {}, "all_granted": False, "missing": []})

    perms: dict[str, bool] = {}

    # screen_recording — try Quartz CGDisplayCreateImage
    try:
        proc = await asyncio.create_subprocess_exec(
            "python3", "-c",
            "import Quartz; Quartz.CGDisplayCreateImage(Quartz.CGMainDisplayID())",
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        await proc.wait()
        perms["screen_recording"] = proc.returncode == 0
    except Exception:
        perms["screen_recording"] = False

    # accessibility — try System Events via osascript
    try:
        proc = await asyncio.create_subprocess_exec(
            "osascript", "-e",
            'tell application "System Events" to get name of first process',
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        await proc.wait()
        perms["accessibility"] = proc.returncode == 0
    except Exception:
        perms["accessibility"] = False

    # automation — basic osascript execution
    try:
        proc = await asyncio.create_subprocess_exec(
            "osascript", "-e", "return 1",
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        await proc.wait()
        perms["automation"] = proc.returncode == 0
    except Exception:
        perms["automation"] = False

    missing = [k for k, v in perms.items() if not v]
    return AdapterResponse.success(req, {
        "permissions": perms,
        "all_granted": len(missing) == 0,
        "missing": missing,
    })
