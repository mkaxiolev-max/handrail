from fastapi import FastAPI
from routes.sources import router as sources_router

app = FastAPI(title="Alexandria", version="1.0")
app.include_router(sources_router)

@app.get("/healthz")
async def health():
    return {"status": "ok", "service": "alexandria"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9001)
