from fastapi import FastAPI
from handrail.archivist import Archivist

app = FastAPI()
arch = Archivist()

@app.get("/healthz")
def healthz():
    return {"ok": True}

@app.get("/doctor")
def doctor():
    return arch.doctor(integrity_check=False)

@app.get("/sessions")
def sessions():
    d = arch.doctor(integrity_check=False)
    return {"sessions": d.get("sessions", []), "quarantined": d.get("quarantined", [])}

@app.get("/session/{session_id}/receipts")
def receipts(session_id: str, limit: int = 200):
    return {"session_id": session_id, "receipts": list(reversed(arch.read(session_id, limit=limit)))}
