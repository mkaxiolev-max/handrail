import os

PORT = int(os.environ.get("VOICE_GATEWAY_PORT", 9002))
HOST = os.environ.get("VOICE_GATEWAY_HOST", "0.0.0.0")
NGROK_DOMAIN = os.environ.get("NGROK_DOMAIN", "monica-problockade-caylee.ngrok-free.dev")
NS_URL = os.environ.get("NS_URL", "http://localhost:9000")
