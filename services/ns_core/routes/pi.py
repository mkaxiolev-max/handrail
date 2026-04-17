"""POST /pi/check — Π admissibility endpoint."""
from fastapi import APIRouter
from pi.engine import PiCheckRequest, PiEngine

router = APIRouter(tags=["pi"])
_engine = PiEngine()


@router.post("/pi/check")
async def pi_check(body: dict):
    req = PiCheckRequest(
        candidate=body.get("candidate", body),
        context=body.get("context"),
    )
    return _engine.check(req).model_dump()
