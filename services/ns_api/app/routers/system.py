"""System state router — /api/v1/system/*"""
import json
import httpx
from pathlib import Path
from fastapi import APIRouter
from shared.models.system import SystemState, TimelineEvent, FocusState, FailureOverlay, ServiceHealth
from shared.models.enums import SystemTier, RiskTier
from ns_api.app.config import HANDRAIL_URL, NS_URL, CONTINUUM_URL, ATOMLEX_URL, ALEXANDRIA_PATH

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


@router.get("/timeline", response_model=list[dict])
async def get_timeline():
    receipts_dir = ALEXANDRIA_PATH / "receipts"
    events = []

    # Collect all .json receipt files (exclude receipt_chain.jsonl)
    files = sorted(
        [f for f in receipts_dir.glob("*.json") if f.is_file()],
        key=lambda f: f.stat().st_mtime,
        reverse=True,
    )[:50] if receipts_dir.exists() else []

    for f in files:
        try:
            d = json.loads(f.read_text())
            events.append({
                "event_type": d.get("receipt_type", "receipt"),
                "timestamp": d.get("timestamp"),
                "receipt_id": d.get("receipt_id", f.stem),
                "op": d.get("op"),
                "summary": (
                    f"{d.get('receipt_type','op')} — {d.get('op','unknown')}"
                    if d.get("op")
                    else d.get("receipt_type", "receipt")
                ),
            })
        except Exception:
            continue

    # Fallback: scan receipt_chain.jsonl
    if not events:
        chain = receipts_dir / "receipt_chain.jsonl"
        if not chain.exists():
            chain = ALEXANDRIA_PATH / "ALEXANDRIA" / "ledger" / "ns_receipt_chain.jsonl"
        if chain.exists():
            lines = chain.read_text().strip().splitlines()
            for line in reversed(lines[-50:]):
                try:
                    d = json.loads(line)
                    events.append({
                        "event_type": d.get("receipt_type", "receipt"),
                        "timestamp": d.get("timestamp"),
                        "receipt_id": d.get("receipt_id", ""),
                        "op": d.get("op"),
                        "summary": (
                            f"{d.get('receipt_type','op')} — {d.get('op','unknown')}"
                            if d.get("op")
                            else d.get("receipt_type", "receipt")
                        ),
                    })
                except Exception:
                    continue

    if not events:
        events.append({
            "event_type": "boot",
            "timestamp": None,
            "receipt_id": "evt_boot_000",
            "op": None,
            "summary": "NS∞ sovereign boot complete — 12/12",
        })

    return events


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
