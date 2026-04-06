import os

PORT = int(os.environ.get("TELEPHONY_BRIDGE_PORT", 9003))
HOST = os.environ.get("TELEPHONY_BRIDGE_HOST", "0.0.0.0")
NGROK_DOMAIN = os.environ.get("NGROK_DOMAIN", "monica-problockade-caylee.ngrok-free.dev")
VOICE_GATEWAY_URL = os.environ.get("VOICE_GATEWAY_URL", "http://localhost:9002")
