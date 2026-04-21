"""AXIOLEV Holdings LLC © 2026 — omega_logos entrypoint."""
import uvicorn
from .runtime.service import app
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9010)
