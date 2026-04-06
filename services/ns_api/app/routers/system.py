"""System state router — /api/v1/system/*"""
import httpx
from fastapi import APIRouter
from shared.models.system import SystemState, TimelineEvent, FocusState, FailureOverlay, ServiceHealth
from shared.models.enums import SystemTier, RiskTier
from ns_api.app.config import HANDRAIL_URL, NS_URL, CONTINUUM_URL, ATOMLEX_URL

router = APIRouter(prefix="/api/v1/system", tags=["system"])

SERVICES = [
    ("handrail", f"{HANDRAIL_URL}/healthz"),
    ("ns", f"{NS_URL}/healthz"),
    ("continuum", f"{CONTINUUM_URL}/state"),
    ("atomlex", f"{ATOMLEX_URL}/healthz"),
]


async def _probe(name: str, url: str) -> ServiceHealth:
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            r = await client.get(url)
            return ServiceHealth(service=name, healthy=r.status_code < 400, url=url, latency_ms=r.elapsed.total_seconds() * 1000)
    except Exception as e:
        return ServiceHealth(service=name, healthy=False, url=url, error=str(e))


@router.get("/state", response_model=SystemState)
async def get_state():
    services = [await _probe(name, url) for name, url in SERVICES]
    return SystemState(
        tier=SystemTier.ACTIVE,
        services=services,
        ops_loaded=125,
        programs_loaded=10,
        yubikey_serials=["26116460"],
        alexandria_mounted=True,
    )


@router.get("/timeline", response_model=list[TimelineEvent])
async def get_timeline():
    return [
        TimelineEvent(
            event_id="evt_boot_001",
            event_type="boot",
            summary="NS∞ sovereign boot complete — 12/12",
            risk_tier=RiskTier.R0,
        )
    ]


@router.get("/focus", response_model=FocusState)
async def get_focus():
    return FocusState(
        active_program=None,
        active_intent=None,
        pending_approvals=[],
        unresolved_risks=[],
    )


@router.get("/failure-overlay", response_model=list[FailureOverlay])
async def get_failure_overlay():
    import json
    from pathlib import Path
    from ns_api.app.config import ALEXANDRIA_PATH
    failure_file = ALEXANDRIA_PATH / "ledger" / "failure_events.jsonl"
    if not failure_file.exists():
        return []
    results = []
    lines = failure_file.read_text().strip().splitlines()
    for line in lines[-20:]:
        try:
            d = json.loads(line)
            results.append(FailureOverlay(
                failure_id=d.get("run_id", "unknown"),
                op=d.get("op", "unknown"),
                error=d.get("error", ""),
                resolved=False,
            ))
        except Exception:
            continue
    return list(reversed(results))
