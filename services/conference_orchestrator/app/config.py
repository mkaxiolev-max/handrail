import os

PORT = int(os.environ.get("CONFERENCE_ORCHESTRATOR_PORT", 9004))
HOST = os.environ.get("CONFERENCE_ORCHESTRATOR_HOST", "0.0.0.0")
TELEPHONY_BRIDGE_URL = os.environ.get("TELEPHONY_BRIDGE_URL", "http://localhost:9003")
