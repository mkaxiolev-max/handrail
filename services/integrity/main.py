from fastapi import FastAPI

app = FastAPI(title="Integrity", version="1.0")

@app.get("/healthz")
async def health():
    return {"status": "ok", "service": "integrity"}
