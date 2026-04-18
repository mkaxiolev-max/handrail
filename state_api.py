#!/usr/bin/env python3
"""NS∞ System State API — GET /state"""
import json, os, socket, subprocess, hashlib, datetime, urllib.request
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

RUNTIME = str(Path(__file__).resolve().parent)
ALEXANDRIA = "/Volumes/NSExternal/ALEXANDRIA"
RECEIPT_LOG = f"{ALEXANDRIA}/receipts/boot_receipts.jsonl"
STATE_FILE = f"{RUNTIME}/.ns_state"
SERVICE_PORTS = {
    "ns_core": 9000, "alexandria": 9001, "model_router": 9002,
    "violet": 9003, "canon": 9004, "integrity": 9005,
    "omega": 9010, "handrail": 8011, "continuum": 8788
}

def get_git_info():
    try:
        commit = subprocess.check_output(["git","-C",RUNTIME,"rev-parse","HEAD"],
            stderr=subprocess.DEVNULL).decode().strip()[:12]
        branch = subprocess.check_output(["git","-C",RUNTIME,"branch","--show-current"],
            stderr=subprocess.DEVNULL).decode().strip()
        return {"commit": commit, "branch": branch}
    except: return {"commit": "unknown", "branch": "unknown"}

def check_service(port, timeout=2):
    try:
        sock = socket.create_connection(("127.0.0.1", port), timeout=timeout)
        sock.close()
        return "running"
    except: return "down"

def get_db_status():
    for port in (5433, 5432):
        if check_service(port) == "running":
            return {"status": "online", "host_port": port, "migration_version": None}
    return {"status": "offline", "host_port": None, "migration_version": None}


def get_ollama_status():
    installed = bool(shutil_which("ollama"))
    version = ""
    if installed:
        try:
            version = subprocess.check_output(
                ["ollama", "--version"], stderr=subprocess.STDOUT, timeout=5
            ).decode().strip().splitlines()[0]
        except Exception:
            version = "installed"
    try:
        with urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=3) as resp:
            payload = json.loads(resp.read().decode())
        models = [m.get("name") for m in payload.get("models", []) if m.get("name")]
        return {
            "installed": installed,
            "version": version,
            "reachable": True,
            "models": models,
            "model_count": len(models),
        }
    except Exception as e:
        return {
            "installed": installed,
            "version": version,
            "reachable": False,
            "models": [],
            "model_count": 0,
            "error": str(e),
        }


def shutil_which(binary):
    try:
        import shutil

        return shutil.which(binary)
    except Exception:
        return None

def get_alexandria_status():
    p = Path(ALEXANDRIA)
    if not p.exists(): return {"mounted": False, "writable": False}
    test_f = p / ".state_rw_test"
    try:
        test_f.write_text("test")
        test_f.unlink()
        return {"mounted": True, "writable": True}
    except: return {"mounted": True, "writable": False}

def get_receipt_chain_health():
    try:
        with open(RECEIPT_LOG, "rb") as f:
            lines = [l.strip() for l in f if l.strip()]
        if not lines: return "empty"
        for line in lines[-5:]:
            json.loads(line)
        return "healthy"
    except Exception as e: return f"error: {e}"

def build_state():
    svcs = {k: check_service(v) for k, v in SERVICE_PORTS.items()}
    degraded = [k for k, v in svcs.items() if v != "running"]
    ns_state = Path(STATE_FILE).read_text().strip() if Path(STATE_FILE).exists() else "UNKNOWN"
    exec_enabled = Path(f"{RUNTIME}/.execution_enabled").exists()
    return {
        "machine_id": socket.gethostname(),
        "state": ns_state,
        "boot_mode": "EXECUTION_ENABLED" if exec_enabled else "ADVISORY_ONLY",
        "git": get_git_info(),
        "alexandria": get_alexandria_status(),
        "database": get_db_status(),
        "services": svcs,
        "providers": {
            "anthropic": {"configured": bool(os.environ.get("ANTHROPIC_API_KEY"))},
            "ollama_local": get_ollama_status(),
        },
        "receipt_chain": get_receipt_chain_health(),
        "degraded": degraded,
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
    }

class StateHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args): pass
    def do_GET(self):
        if self.path in ("/state", "/state/"):
            data = build_state()
            body = json.dumps(data, indent=2).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", len(body))
            self.end_headers()
            self.wfile.write(body)
        elif self.path in ("/healthz", "/health"):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'{"status":"ok"}')
        else:
            self.send_response(404)
            self.end_headers()

if __name__ == "__main__":
    port = int(os.environ.get("STATE_API_PORT", 9090))
    print(f"NS∞ State API listening on :{port}")
    HTTPServer(("0.0.0.0", port), StateHandler).serve_forever()
