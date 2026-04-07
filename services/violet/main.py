from fastapi import FastAPI

app = FastAPI(title="Violet", version="1.0")

@app.get("/healthz")
async def health():
    return {"status": "ok", "service": "violet"}
