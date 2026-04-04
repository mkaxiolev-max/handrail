"""
media.* namespace — playback control via AppleScript.
Ops: now_playing / play_pause / next / volume
Dignity Guard: volume range 0-100 enforced.
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


async def media_now_playing(req: AdapterRequest) -> AdapterResponse:
    if not IS_MACOS:
        return AdapterResponse.success(req, {"ok": True, "playing": False, "mode": "mock"})
    for app in ["Music", "Spotify"]:
        rc, out, err = await _run([
            "osascript", "-e",
            f'tell application "{app}" to if player state is playing then '
            f'return (name of current track) & "|" & (artist of current track) & "|" & (album of current track)'
        ])
        if rc == 0 and out and "|" in out:
            parts = out.split("|")
            return AdapterResponse.success(req, {
                "ok": True, "playing": True, "app": app,
                "track": parts[0].strip() if len(parts) > 0 else "",
                "artist": parts[1].strip() if len(parts) > 1 else "",
                "album": parts[2].strip() if len(parts) > 2 else "",
            })
    return AdapterResponse.success(req, {"ok": True, "playing": False, "reason": "no_active_player"})


async def media_play_pause(req: AdapterRequest) -> AdapterResponse:
    app = (req.params or {}).get("app", "Music")
    if not IS_MACOS:
        return AdapterResponse.success(req, {"ok": True, "toggled": True, "mode": "mock"})
    rc, out, err = await _run(["osascript", "-e", f'tell application "{app}" to playpause'])
    return AdapterResponse.success(req, {"ok": True, "toggled": rc == 0})


async def media_next(req: AdapterRequest) -> AdapterResponse:
    app = (req.params or {}).get("app", "Music")
    if not IS_MACOS:
        return AdapterResponse.success(req, {"ok": True, "skipped": True, "mode": "mock"})
    rc, out, err = await _run(["osascript", "-e", f'tell application "{app}" to next track'])
    return AdapterResponse.success(req, {"ok": True, "skipped": rc == 0})


async def media_volume(req: AdapterRequest) -> AdapterResponse:
    vol = (req.params or {}).get("volume")
    if vol is not None:
        vol = max(0, min(100, int(vol)))
        if not IS_MACOS:
            return AdapterResponse.success(req, {"ok": True, "volume": vol, "action": "set", "mode": "mock"})
        rc, out, err = await _run(["osascript", "-e", f"set volume output volume {vol}"])
        return AdapterResponse.success(req, {"ok": rc == 0, "volume": vol, "action": "set"})
    else:
        if not IS_MACOS:
            return AdapterResponse.success(req, {"ok": True, "volume": 50, "action": "get", "mode": "mock"})
        rc, out, err = await _run(["osascript", "-e", "output volume of (get volume settings)"])
        try:
            current = int(out.strip())
        except ValueError:
            current = None
        return AdapterResponse.success(req, {"ok": True, "volume": current, "action": "get"})


def build_media_handlers() -> dict:
    return {
        "media.now_playing": media_now_playing,
        "media.play_pause":  media_play_pause,
        "media.next":        media_next,
        "media.volume":      media_volume,
    }
