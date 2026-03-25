import subprocess
def execute(path=".", detailed=False):
    try:
        cmd = f"ls {\"-la\" if detailed else \"\"} {path}"
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=2)
        return {"ok": True, "output": r.stdout, "code": r.returncode}
    except Exception as e:
        return {"ok": False, "error": str(e)}