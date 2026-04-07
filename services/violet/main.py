from fastapi import FastAPI

app = FastAPI(title="Violet", version="1.0")

@app.get("/healthz")
async def health():
    return {"status": "ok", "service": "violet"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9003)
