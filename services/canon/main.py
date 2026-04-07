from fastapi import FastAPI

app = FastAPI(title="Canon", version="1.0")

@app.get("/healthz")
async def health():
    return {"status": "ok", "service": "canon"}
