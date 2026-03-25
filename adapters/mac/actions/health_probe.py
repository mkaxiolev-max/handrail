import subprocess
def execute(service="handrail"):
    try:
        url = "http://127.0.0.1:8011/healthz" if service == "handrail" else "http://127.0.0.1:9000/healthz"
        r = subprocess.run(["curl", "-sf", "--max-time", "2", url], capture_output=True, text=True, timeout=3)
        return {"ok": True, "service": service, "health": "healthy" if r.returncode == 0 else "down"}
    except Exception as e:
        return {"ok": False, "error": str(e)}