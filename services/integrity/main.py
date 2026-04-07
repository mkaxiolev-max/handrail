from fastapi import FastAPI
from routes.integrity import router as integrity_router
from routes.receipt_chain import router as receipt_chain_router

app = FastAPI(title="Integrity", version="1.0")
app.include_router(integrity_router)
app.include_router(receipt_chain_router)

@app.get("/healthz")
async def health():
    return {"status": "ok", "service": "integrity"}
