from fastapi import FastAPI
from routes.integrity import router as integrity_router

app = FastAPI(title="Integrity", version="1.0")
app.include_router(integrity_router)

@app.get("/healthz")
async def health():
    return {"status": "ok", "service": "integrity"}
