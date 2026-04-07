from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/boot", tags=["boot"])

class BootBinding(BaseModel):
    mac_folder: Optional[str] = None
    google_drive_folder: Optional[str] = None

boot_state = {
    "boot_ready": False,
    "bindings": {},
    "last_initialized": None
}

@router.get("/status")
async def boot_status():
    return {
        "status": "ok",
        "boot_ready": boot_state["boot_ready"],
        "required_bindings": ["mac_folder", "google_drive_folder"],
        "present_bindings": list(boot_state["bindings"].keys()),
        "last_initialized": boot_state["last_initialized"]
    }

@router.post("/bindings")
async def create_binding(binding: BootBinding):
    if binding.mac_folder:
        boot_state["bindings"]["mac_folder"] = binding.mac_folder
    if binding.google_drive_folder:
        boot_state["bindings"]["google_drive_folder"] = binding.google_drive_folder
    boot_state["boot_ready"] = len(boot_state["bindings"]) >= 1
    return {"status": "ok", "bindings": boot_state["bindings"], "boot_ready": boot_state["boot_ready"]}

@router.post("/initialize")
async def initialize():
    if not boot_state["boot_ready"]:
        raise HTTPException(status_code=400, detail="Bindings not complete")
    import datetime
    boot_state["last_initialized"] = datetime.datetime.utcnow().isoformat()
    return {"status": "initializing", "boot_mode": "alexandria_ingest"}

@router.get("/healthz")
async def health():
    return {"status": "ok"}
