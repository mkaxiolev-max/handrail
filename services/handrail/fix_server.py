import re, os
path = "/app/handrail/server.py"
with open(path, "r") as f:
    content = f.read()

armored_gate = """@app.post("/ops/cps")
def ops_cps(req: CPSRequest):
    from handrail.cps_engine import CPSExecutor
    import hashlib, json, os
    from datetime import datetime
    run_id = now_id()
    run_dir = RUNS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    cps_dict = {"cps_id": req.cps_id, "ops": req.ops, "expect": req.expect or {}}
    result = CPSExecutor.execute(cps_dict, WORKSPACE)
    try:
        _h = hashlib.sha256(json.dumps(cps_dict, sort_keys=True).encode()).hexdigest()
        result["identity"] = {"input_hash": _h, "timestamp": datetime.utcnow().isoformat()}
        _lp = "/app/handrail/ledger_chain.json"
        _ph = "0" * 64
        if os.path.exists(_lp):
            try:
                with open(_lp, "r") as f: _ph = json.load(f).get("last_hash", _ph)
            except: pass
        _ch = hashlib.sha256((_ph + _h).encode()).hexdigest()
        result["ledger"] = {"prev_hash": _ph, "hash": _ch}
        with open(_lp, "w") as f: json.dump({"last_hash": _ch, "run_id": run_id}, f)
    except Exception as e:
        result["bk_error"] = str(e)
    result.update({"run_id": run_id, "run_dir": str(run_dir)})
    return JSONResponse(result)"""

pattern = r"@app\.post\(\"/ops/cps\"\).*?return JSONResponse\(result\)"
new_content = re.sub(pattern, armored_gate, content, flags=re.DOTALL)

with open(path, "w") as f:
    f.write(new_content)
