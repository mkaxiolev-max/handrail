from fastapi import FastAPI
from routes.boot import router as boot_router
from routes.feed import router as feed_router
from routes.packets import router as packets_router

app = FastAPI(title="NS Core", version="1.0")

app.include_router(boot_router)
app.include_router(feed_router)
app.include_router(packets_router)

@app.get("/healthz")
async def health():
    return {"status": "ok", "service": "ns_core"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9000)
