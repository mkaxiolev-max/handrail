"""NS API — port 9001. Sovereign backend for NS∞ frontend."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ns_api.app.routers import system, engine, programs, memory, governance, replay, omega

app = FastAPI(
    title="NS API",
    version="1.0.0",
    description="NS∞ sovereign backend — system state, engine, programs, memory, governance, replay, omega",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(system.router)
app.include_router(engine.router)
app.include_router(programs.router)
app.include_router(memory.router)
app.include_router(governance.router)
app.include_router(replay.router)
app.include_router(omega.router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "ns_api", "port": 9001, "version": "1.0.0"}
