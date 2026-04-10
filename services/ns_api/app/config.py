import os
from pathlib import Path

PORT = int(os.environ.get("NS_API_PORT", 9001))
HOST = os.environ.get("NS_API_HOST", "0.0.0.0")
ALEXANDRIA_PATH = Path(os.environ.get("ALEXANDRIA_PATH", "/Volumes/NSExternal"))
RECEIPTS_PATH = ALEXANDRIA_PATH / "receipts"
LEDGER_PATH = ALEXANDRIA_PATH / "ledger"
SESSIONS_PATH = ALEXANDRIA_PATH / "sessions"

# Upstream services
HANDRAIL_URL = os.environ.get("HANDRAIL_URL", "http://localhost:8011")
NS_URL = os.environ.get("NS_URL", "http://localhost:9000")
CONTINUUM_URL = os.environ.get("CONTINUUM_URL", "http://localhost:8788")
ATOMLEX_URL = os.environ.get("ATOMLEX_URL", "http://localhost:8080")
OMEGA_URL = os.environ.get("OMEGA_URL", "http://localhost:9010")
