from fastapi import FastAPI
from routes.canon import router as canon_router

app = FastAPI(title="Canon", version="1.0")
app.include_router(canon_router)

@app.get("/healthz")
async def health():
    return {"status": "ok", "service": "canon"}
