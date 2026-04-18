import asyncio
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import httpx
from fastapi import APIRouter

router = APIRouter(prefix="/api/organism", tags=["organism"])

RECEIPTS_DIR = Path("/Volumes/NSExternal/ALEXANDRIA/receipts")
NS_CORE_BASE = os.environ.get("ORGANISM_NS_CORE_URL", "http://127.0.0.1:9000")
STATE_URL = os.environ.get("ORGANISM_STATE_URL", "http://host.docker.internal:9090/state")
OLLAMA_URL = os.environ.get("ORGANISM_OLLAMA_URL", "http://host.docker.internal:11434/api/tags")
MAC_ADAPTER_URL = os.environ.get("ORGANISM_MAC_ADAPTER_URL", "http://host.docker.internal:8765")

SERVICE_TARGETS = [
    {"id": "ns_core", "label": "NS Core", "url": f"{NS_CORE_BASE}/healthz", "kind": "core"},
    {"id": "alexandria", "label": "Alexandria", "url": "http://alexandria:9001/healthz", "kind": "memory"},
    {"id": "model_router", "label": "Model Router", "url": "http://model_router:9002/healthz", "kind": "providers"},
    {"id": "violet", "label": "Violet", "url": "http://violet:9003/healthz", "kind": "voice"},
    {"id": "canon", "label": "Canon", "url": "http://canon:9004/healthz", "kind": "governance"},
    {"id": "integrity", "label": "Integrity", "url": "http://integrity:9005/healthz", "kind": "audit"},
    {"id": "omega", "label": "Omega", "url": "http://omega:9010/healthz", "kind": "omega"},
    {"id": "handrail", "label": "Handrail", "url": "http://handrail:8011/healthz", "kind": "execution"},
    {"id": "continuum", "label": "Continuum", "url": "http://continuum:8788/state", "kind": "continuity"},
    {"id": "state_api", "label": "State API", "url": STATE_URL, "kind": "truth"},
]


async def _fetch_json(client: httpx.AsyncClient, url: str, timeout: float = 3.0) -> dict:
    started = asyncio.get_running_loop().time()
    try:
        response = await client.get(url, timeout=timeout)
        elapsed = int((asyncio.get_running_loop().time() - started) * 1000)
        content_type = response.headers.get("content-type", "")
        payload = None
        if "json" in content_type:
            payload = response.json()
        else:
            try:
                payload = response.json()
            except Exception:
                payload = {"text": response.text[:400]}
        return {
            "ok": response.status_code < 400,
            "status_code": response.status_code,
            "latency_ms": elapsed,
            "payload": payload,
        }
    except Exception as e:
        return {
            "ok": False,
            "status_code": None,
            "latency_ms": None,
            "payload": None,
            "error": str(e),
        }


async def _probe_service(client: httpx.AsyncClient, service: dict) -> dict:
    result = await _fetch_json(client, service["url"])
    detail = ""
    if result["ok"] and isinstance(result["payload"], dict):
        detail = ", ".join(list(result["payload"].keys())[:4])
    elif result.get("error"):
        detail = result["error"]
    return {
        "id": service["id"],
        "label": service["label"],
        "kind": service["kind"],
        "status": "live" if result["ok"] else "down",
        "latency_ms": result.get("latency_ms"),
        "endpoint": service["url"],
        "status_code": result.get("status_code"),
        "detail": detail,
        "payload": result.get("payload"),
    }


def _receipt_snapshot() -> dict:
    if not RECEIPTS_DIR.exists():
        return {"mounted": False, "count": 0, "latest": None}
    receipts = sorted(RECEIPTS_DIR.glob("*.json"), key=lambda path: path.stat().st_mtime, reverse=True)
    latest = receipts[0].name if receipts else None
    return {"mounted": True, "count": len(receipts), "latest": latest}


def _git_commit() -> str:
    try:
        import subprocess

        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], text=True).strip()
    except Exception:
        return "unknown"


@router.get("/overview")
async def organism_overview():
    async with httpx.AsyncClient() as client:
        services = await asyncio.gather(*[_probe_service(client, service) for service in SERVICE_TARGETS])

        state_result = await _fetch_json(client, STATE_URL)
        state_payload = state_result["payload"] if isinstance(state_result.get("payload"), dict) else {}

        provider_result = await _fetch_json(client, "http://model_router:9002/providers")
        provider_payload = provider_result["payload"] if isinstance(provider_result.get("payload"), dict) else {}
        ollama_result = await _fetch_json(client, OLLAMA_URL)

        memory_now = await _fetch_json(client, f"{NS_CORE_BASE}/system/now")
        memory_atoms = await _fetch_json(client, "http://alexandria:9001/atoms?limit=1")
        handrail_status = await _fetch_json(client, "http://handrail:8011/system/status")
        hic_status = await _fetch_json(client, f"{NS_CORE_BASE}/hic/gates")
        pdp_health = await _fetch_json(client, f"{NS_CORE_BASE}/healthz")
        violet_status = await _fetch_json(client, f"{NS_CORE_BASE}/violet/status")
        voice_sessions = await _fetch_json(client, f"{NS_CORE_BASE}/voice/sessions")
        mac_gateway = await _fetch_json(client, f"{NS_CORE_BASE}/mac_adapter/status")
        mac_local = await _fetch_json(client, f"{MAC_ADAPTER_URL}/healthz")
        if not mac_local["ok"]:
            mac_local = await _fetch_json(client, f"{MAC_ADAPTER_URL}/env/health")
        omega_health = await _fetch_json(client, f"{NS_CORE_BASE}/api/v1/omega/healthz")
        omega_runs = await _fetch_json(client, f"{NS_CORE_BASE}/api/v1/omega/runs")

    providers = []
    router_providers = provider_payload.get("providers", {}) if provider_payload else {}
    for provider_id, payload in router_providers.items():
        providers.append(
            {
                "id": provider_id,
                "status": "live" if payload.get("live") else "down",
                "local": bool(payload.get("local")),
                "configured": bool(payload.get("key_present")) or bool(payload.get("local")),
                "model": payload.get("primary_model") or payload.get("model"),
                "model_count": payload.get("model_count", 0),
                "models": payload.get("models", []),
                "endpoint": payload.get("base_url") or "http://127.0.0.1:9002/providers",
                "detail": payload.get("error") or "",
            }
        )

    if not any(provider["id"] == "ollama" for provider in providers):
        ollama_payload = ollama_result["payload"] if isinstance(ollama_result.get("payload"), dict) else {}
        providers.append(
            {
                "id": "ollama",
                "status": "live" if ollama_result["ok"] else "down",
                "local": True,
                "configured": True,
                "model": (ollama_payload.get("models") or [{}])[0].get("name") if ollama_payload.get("models") else None,
                "model_count": len(ollama_payload.get("models", [])),
                "models": [model.get("name") for model in ollama_payload.get("models", []) if model.get("name")],
                "endpoint": OLLAMA_URL,
                "detail": ollama_result.get("error") or "",
            }
        )

    memory_payload = memory_now["payload"] if isinstance(memory_now.get("payload"), dict) else {}
    atoms_payload = memory_atoms["payload"] if isinstance(memory_atoms.get("payload"), dict) else {}
    voice_payload = voice_sessions["payload"] if isinstance(voice_sessions.get("payload"), dict) else {}
    omega_runs_payload = omega_runs["payload"] if isinstance(omega_runs.get("payload"), dict) else {}
    receipt_snapshot = _receipt_snapshot()
    state_alexandria = state_payload.get("alexandria", {}) if isinstance(state_payload, dict) else {}

    return {
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "system_state": {
            "state": state_payload.get("state", "UNKNOWN"),
            "boot_mode": state_payload.get("boot_mode", "UNKNOWN"),
            "degraded": state_payload.get("degraded", []),
            "git_commit": state_payload.get("git", {}).get("commit") or _git_commit(),
            "source": STATE_URL,
        },
        "services": services,
        "providers": providers,
        "memory": {
            "system_now": memory_payload.get("memory", {}),
            "atoms_total": atoms_payload.get("total"),
            "receipt_files": receipt_snapshot["count"],
            "latest_receipt": receipt_snapshot["latest"],
            "alexandria_mounted": state_alexandria.get("mounted", receipt_snapshot["mounted"]),
        },
        "execution": {
            "status": "live" if handrail_status["ok"] else "down",
            "endpoint": "http://handrail:8011/system/status",
            "payload": handrail_status.get("payload"),
        },
        "governance": {
            "hic": {"status": "live" if hic_status["ok"] else "down", "payload": hic_status.get("payload")},
            "pdp": {"status": "live" if pdp_health["ok"] else "down", "payload": pdp_health.get("payload")},
        },
        "voice": {
            "status": "live" if violet_status["ok"] else "down",
            "violet": violet_status.get("payload"),
            "sessions_count": voice_payload.get("count"),
        },
        "body": {
            "gateway": {"status": "live" if mac_gateway["ok"] else "down", "payload": mac_gateway.get("payload")},
            "adapter": {"status": "live" if mac_local["ok"] else "down", "payload": mac_local.get("payload")},
        },
        "omega": {
            "status": "live" if omega_health["ok"] else "down",
            "health": omega_health.get("payload"),
            "runs_count": len(omega_runs_payload) if isinstance(omega_runs_payload, list) else omega_runs_payload.get("count"),
            "runs_payload": omega_runs_payload,
        },
    }
