"""PAP FastAPI router — /pap prefix."""
from .api.pap_routes import router as pap_router

__all__ = ["pap_router"]
