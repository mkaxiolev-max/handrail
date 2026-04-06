"""Telephony Bridge — port 9003."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from telephony_bridge.app.routers import twilio_voice, twilio_status

app = FastAPI(title="Telephony Bridge", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# HTTP + WS routes both on twilio_voice router
app.include_router(twilio_voice.router)
app.include_router(twilio_status.router)


@app.get("/health")
async def health():
    from telephony_bridge.app.routers.twilio_voice import _calls
    return {
        "status": "ok",
        "service": "telephony_bridge",
        "port": 9003,
        "version": "1.0.0",
        "active_calls": len([c for c in _calls.values() if c.get("status") == "streaming"]),
        "total_calls": len(_calls),
    }
