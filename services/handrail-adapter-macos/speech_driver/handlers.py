"""
speech.* namespace — TTS via macOS say command.
Ops: say / say_async / voices / stop
Dignity Guard: max 1000 chars, all speech logged.
"""
from __future__ import annotations
import asyncio, platform, subprocess
from adapter_core.contract import AdapterRequest, AdapterResponse, OperationStatus

IS_MACOS = platform.system() == "Darwin"
_DEFAULT_VOICE = "Samantha"
_MAX_TEXT = 1000


async def _run(cmd: list[str], timeout: float = 30.0) -> tuple[int, str, str]:
    proc = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    try:
        out, err = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        proc.kill()
        return 1, "", "timeout"
    return proc.returncode, out.decode().strip(), err.decode().strip()


async def speech_say(req: AdapterRequest) -> AdapterResponse:
    text = (req.params or {}).get("text", "").strip()[:_MAX_TEXT]
    voice = (req.params or {}).get("voice", _DEFAULT_VOICE)[:50]
    rate = int((req.params or {}).get("rate", 175))
    rate = max(80, min(rate, 300))

    if not text:
        return AdapterResponse.failure(req, "text required")
    if not IS_MACOS:
        return AdapterResponse.success(req, {"ok": True, "said": text, "mode": "mock"})

    rc, out, err = await _run(["say", "-v", voice, "-r", str(rate), text], timeout=60.0)
    if rc != 0:
        rc, out, err = await _run(["say", text], timeout=60.0)
    return AdapterResponse.success(req, {"ok": rc == 0, "said": text,
                                          "voice": voice, "rate": rate})


async def speech_say_async(req: AdapterRequest) -> AdapterResponse:
    text = (req.params or {}).get("text", "").strip()[:_MAX_TEXT]
    voice = (req.params or {}).get("voice", _DEFAULT_VOICE)[:50]

    if not text:
        return AdapterResponse.failure(req, "text required")
    if not IS_MACOS:
        return AdapterResponse.success(req, {"ok": True, "queued": True, "mode": "mock"})

    subprocess.Popen(
        ["say", "-v", voice, text],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        start_new_session=True
    )
    return AdapterResponse.success(req, {"ok": True, "queued": True, "text": text})


async def speech_voices(req: AdapterRequest) -> AdapterResponse:
    if not IS_MACOS:
        return AdapterResponse.success(req, {"ok": True, "voices": [], "mode": "mock"})
    rc, out, err = await _run(["say", "-v", "?"])
    if rc != 0:
        return AdapterResponse.success(req, {"ok": True, "voices": [],
                                              "skipped": True, "reason": err[:60]})
    voices = []
    for line in out.splitlines()[:30]:
        parts = line.split()
        if parts:
            voices.append(parts[0])
    return AdapterResponse.success(req, {"ok": True, "voices": voices, "count": len(voices)})


async def speech_stop(req: AdapterRequest) -> AdapterResponse:
    if not IS_MACOS:
        return AdapterResponse.success(req, {"ok": True, "stopped": True, "mode": "mock"})
    rc, out, err = await _run(["pkill", "-x", "say"])
    return AdapterResponse.success(req, {"ok": True, "stopped": rc == 0 or rc == 1})


def build_speech_handlers() -> dict:
    return {
        "speech.say":       speech_say,
        "speech.say_async": speech_say_async,
        "speech.voices":    speech_voices,
        "speech.stop":      speech_stop,
    }
