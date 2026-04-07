from fastapi import FastAPI
from routes.router import router as router_router

app = FastAPI(title="Model Router", version="1.0")
app.include_router(router_router)

@app.get("/healthz")
async def health():
    return {"status": "ok", "service": "model_router"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9002)
