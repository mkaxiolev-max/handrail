from fastapi import APIRouter

router = APIRouter(prefix="/omega", tags=["omega"])


@router.get("/healthz")
async def omega_health():
    return {"status": "ok", "service": "omega", "route": "omega_healthz"}
