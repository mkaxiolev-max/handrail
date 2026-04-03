"""
audio.* namespace
=================
macOS audio control via AppleScript.

Ops:
  audio.get_volume  — {volume: float, muted: bool}
  audio.set_volume  — {ok: bool, volume_set: float}
  audio.get_playing — {app: str, playing: bool, track: str}

Dignity Guard:
  audio.set_volume: volume must be 0–100 (PermissionError otherwise)

Graceful skip on non-macOS.
"""
from __future__ import annotations
import asyncio, platform
from typing import Any

from adapter_core.contract import AdapterRequest, AdapterResponse

IS_MACOS = platform.system() == "Darwin"

_GET_VOLUME_SCRIPT = 'output volume of (get volume settings)'
_GET_MUTED_SCRIPT  = 'output muted of (get volume settings)'
_GET_TRACK_SCRIPT  = 'tell application "Music" to get name of current track'
_GET_PLAYING_SCRIPT = 'tell application "Music" to get player state'


async def _osascript(expr: str, timeout: float = 5.0) -> tuple[int, str, str]:
    proc = await asyncio.create_subprocess_exec(
        "osascript", "-e", expr,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        return proc.returncode, stdout.decode().strip(), stderr.decode().strip()
    except asyncio.TimeoutError:
        proc.kill()
        return -1, "", "TIMEOUT"


async def audio_get_volume(req: AdapterRequest) -> AdapterResponse:
    if not IS_MACOS:
        return AdapterResponse.success(req, {"volume": 50.0, "muted": False, "skipped": True, "reason": "not_macos"})

    rc_vol, out_vol, err_vol = await _osascript(_GET_VOLUME_SCRIPT)
    if rc_vol != 0:
        return AdapterResponse.failure(req, f"osascript error: {err_vol}")

    rc_mute, out_mute, _ = await _osascript(_GET_MUTED_SCRIPT)

    try:
        volume = float(out_vol)
    except ValueError:
        return AdapterResponse.failure(req, f"unexpected volume output: {out_vol!r}")

    muted = out_mute.lower() == "true" if rc_mute == 0 else False
    return AdapterResponse.success(req, {"volume": volume, "muted": muted})


async def audio_set_volume(req: AdapterRequest) -> AdapterResponse:
    volume_raw = req.params.get("volume")
    if volume_raw is None:
        return AdapterResponse.failure(req, "params.volume required")

    try:
        volume = float(volume_raw)
    except (TypeError, ValueError):
        return AdapterResponse.failure(req, "params.volume must be a number")

    # Dignity Guard
    if not (0 <= volume <= 100):
        raise PermissionError(f"audio.set_volume: volume {volume} out of allowed range 0-100")

    if not IS_MACOS:
        return AdapterResponse.success(req, {"ok": True, "volume_set": volume, "skipped": True, "reason": "not_macos"})

    script = f"set volume output volume {int(volume)}"
    rc, _, err = await _osascript(script)
    if rc != 0:
        return AdapterResponse.failure(req, f"osascript error: {err}")

    return AdapterResponse.success(req, {"ok": True, "volume_set": volume})


async def audio_get_playing(req: AdapterRequest) -> AdapterResponse:
    if not IS_MACOS:
        return AdapterResponse.success(req, {"app": "Music", "playing": False, "track": "", "skipped": True, "reason": "not_macos"})

    rc_state, out_state, _ = await _osascript(_GET_PLAYING_SCRIPT)
    if rc_state != 0:
        # Music not running — graceful skip
        return AdapterResponse.success(req, {"app": "Music", "playing": False, "track": "", "skipped": True, "reason": "music_not_running"})

    playing = out_state.lower() == "playing"

    track = ""
    if playing:
        rc_track, out_track, _ = await _osascript(_GET_TRACK_SCRIPT)
        if rc_track == 0:
            track = out_track

    return AdapterResponse.success(req, {"app": "Music", "playing": playing, "track": track})


def build_audio_handlers() -> dict:
    return {
        "audio.get_volume":  audio_get_volume,
        "audio.set_volume":  audio_set_volume,
        "audio.get_playing": audio_get_playing,
    }
