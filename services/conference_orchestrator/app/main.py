"""Conference Orchestrator — port 9004."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from conference_orchestrator.app.routers import conference_http, conference_ws

app = FastAPI(title="Conference Orchestrator", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(conference_http.router)
app.include_router(conference_ws.router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "conference_orchestrator", "port": 9004, "version": "1.0.0"}
