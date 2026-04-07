from fastapi import APIRouter

router = APIRouter(prefix="/canon", tags=["canon"])

@router.get("/healthz")
async def health():
    return {"status": "ok", "service": "canon"}
