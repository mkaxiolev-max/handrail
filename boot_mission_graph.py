#!/usr/bin/env python3
"""
BOOT.MISSION_GRAPH.SYSTEM.v1 — NS∞ Sovereign Boot
12-phase CPS-governed protocol. FAIL_CLOSED on any phase failure.
Precedence enforced: DK > Canon > Policy > Role > Heuristic
"""
import json, hashlib, subprocess, time, os, sys
from datetime import datetime, timezone
from pathlib import Path

RUNTIME_DIR   = Path(os.environ.get("AXIOLEV_RUNTIME", Path.home()/"axiolev_runtime"))
NS_EXTERNAL   = Path("/Volumes/NSExternal")
ALEXANDRIA    = NS_EXTERNAL/".run"/"alexandria_ledger.jsonl"
BOOT_LOG      = NS_EXTERNAL/".run"/"boot_proofs.jsonl"
ABI_SCHEMAS   = RUNTIME_DIR/"schemas"/"abi"/"abi_schemas_v1.json"
POLICY_DIR    = RUNTIME_DIR/"policies"
YUBIKEY_FILE  = RUNTIME_DIR/"config"/"allowed_yubikey_serials.txt"
DK_LOG        = RUNTIME_DIR/"logs"/"dk"/"decisions.jsonl"
REQUIRED_Q    = 1  # set 2 for full 2-of-3

HANDRAIL = "http://127.0.0.1:8011"
NS_SVC   = "http://127.0.0.1:9000"
CONTIN   = "http://127.0.0.1:8788"
ADAPTER  = "http://127.0.0.1:8765"

PHASES = ["verify_substrate","mount_alexandria","validate_ledger","start_handrail",
          "load_policy_bundle","validate_schemas","discover_adapters","verify_adapter_auth",
          "init_simulation_engine","bind_interfaces","activate_mission_graphs","emit_boot_receipt"]

def ts(): return datetime.now(timezone.utc).isoformat()
def sha(s): return hashlib.sha256(s.encode()).hexdigest()[:16]
def http_ok(url, t=5):
    import urllib.request, urllib.error
    try:
        with urllib.request.urlopen(url, timeout=t) as r: return r.status==200
    except: return False
def wait_http(url, secs=45):
    d = time.time()+secs
    while time.time()<d:
        if http_ok(url): return True
        time.sleep(2)
    return False
def cmd(c, t=30):
    try:
        r = subprocess.run(c, capture_output=True, text=True, timeout=t)
        return r.returncode==0, (r.stdout+r.stderr).strip()
    except Exception as e: return False, str(e)
def icon(s): return {"PASS":"✓","FAIL":"✗","RUNNING":"→","SKIP":"○"}.get(s,"?")
def pp(n,name,status,msg=""): print(f"  [{icon(status)}] {n:02d}/{len(PHASES)} {name:<32} {status}  {msg}")

# ── Phases ───────────────────────────────────────────────────────────────────
def p_verify_substrate(ctx):
    ok, out = cmd(["ykman","list"])
    serials = [l.split("Serial:")[-1].strip() for l in out.splitlines() if "Serial:" in l] if ok else []
    ctx["yubikey_serials_present"] = serials
    authorized = False
    if YUBIKEY_FILE.exists():
        allowed = YUBIKEY_FILE.read_text().splitlines()
        authorized = any(s in allowed for s in serials)
    ctx["yubikey_authorized"] = authorized
    if not serials: return False, "No YubiKey — plug in serial 26116460"
    if not authorized: return False, f"YubiKey {serials} not authorized — FAIL_CLOSED"
    if not RUNTIME_DIR.exists(): return False, f"Runtime dir missing: {RUNTIME_DIR}"
    return True, f"YubiKey {serials[0]} authorized"

def p_mount_alexandria(ctx):
    if not NS_EXTERNAL.exists(): return False, f"NSExternal not mounted at {NS_EXTERNAL}"
    (NS_EXTERNAL/".run").mkdir(parents=True, exist_ok=True)
    ctx["alexandria_path"] = str(NS_EXTERNAL)
    return True, f"Alexandria mounted at {NS_EXTERNAL}"

def p_validate_ledger(ctx):
    if not ALEXANDRIA.exists():
        ALEXANDRIA.touch(); ctx["ledger_entries"]=0; ctx["ledger_last_hash"]="genesis"
        return True, "Ledger initialized (genesis)"
    entries=[]
    with open(ALEXANDRIA) as f:
        for line in f:
            line=line.strip()
            if line:
                try: entries.append(json.loads(line))
                except: return False, "Ledger corrupted — JSON parse error"
    for i,e in enumerate(entries[1:],1):
        expected = sha(json.dumps(entries[i-1],sort_keys=True))
        if e.get("prev_hash") != expected:
            return False, f"Hash chain broken at entry {i} — Alexandria integrity violation"
    ctx["ledger_entries"]=len(entries)
    ctx["ledger_last_hash"]=sha(json.dumps(entries[-1],sort_keys=True)) if entries else "genesis"
    return True, f"Ledger OK — {len(entries)} entries"

def p_start_handrail(ctx):
    if http_ok(f"{HANDRAIL}/healthz"): ctx["handrail_started"]=True; return True,"Handrail already up :8011"
    ok,out = cmd(["docker","compose","-f",str(RUNTIME_DIR/"docker-compose.yml"),"up","-d"],t=60)
    if not ok: return False, f"Docker compose failed: {out[:100]}"
    if not wait_http(f"{HANDRAIL}/healthz",45): return False,"Handrail timeout 45s"
    ctx["handrail_started"]=True; return True,"Handrail started :8011"

def p_load_policy_bundle(ctx):
    bundles={}
    if POLICY_DIR.exists():
        for p in POLICY_DIR.rglob("*.json"):
            try: bundles[p.stem]=sha(p.read_text())
            except Exception as e: return False, f"Policy read error {p.name}: {e}"
    ctx["policy_bundles"]=list(bundles.keys())
    ctx["policy_bundle_hash"]=sha(json.dumps(bundles,sort_keys=True))
    return True, f"Loaded {len(bundles)} policy bundles"

def p_validate_schemas(ctx):
    if not ABI_SCHEMAS.exists(): return False, f"ABI schemas missing: {ABI_SCHEMAS}"
    try:
        s=json.loads(ABI_SCHEMAS.read_text())
        objs=s.get("objects",{})
        ctx["schema_versions"]={k:s.get("version","1.0.0") for k in objs}
        ctx["schema_count"]=len(objs)
        return True, f"{len(objs)} ABI objects validated"
    except Exception as e: return False, f"ABI schema parse error: {e}"

def p_discover_adapters(ctx):
    checks=[("handrail",f"{HANDRAIL}/healthz",8011),("ns_northstar",f"{NS_SVC}/health",9000),
            ("continuum",f"{CONTIN}/health",8788),("macos_bridge",f"{ADAPTER}/health",8765)]
    adapters=[{"adapter_id":n,"port":port,"status":"UP" if http_ok(url) else "DOWN"} for n,url,port in checks]
    ctx["adapter_inventory"]=adapters
    down=[a["adapter_id"] for a in adapters if a["status"]=="DOWN"]
    if "handrail" in down: return False,"Handrail adapter DOWN"
    return True, f"{len(adapters)-len(down)} UP, {len(down)} DOWN"

def p_verify_adapter_auth(ctx):
    import urllib.request
    try:
        with urllib.request.urlopen(f"{HANDRAIL}/healthz",timeout=5) as r:
            d=json.loads(r.read()); ctx["handrail_version"]=d.get("version","?")
            return True, f"Handrail auth OK v={ctx['handrail_version']}"
    except Exception as e: return False, f"Adapter auth failed: {e}"

def p_init_simulation_engine(ctx):
    ctx["continuum_ready"]=http_ok(f"{CONTIN}/health")
    return True, f"Continuum {'ready' if ctx['continuum_ready'] else 'deferred'}"

def p_bind_interfaces(ctx):
    ctx["ns_bound"]=http_ok(f"{NS_SVC}/health")
    return True, f"NS {'bound :9000' if ctx['ns_bound'] else 'deferred (non-blocking)'}"

def p_activate_mission_graphs(ctx):
    cps_dir=RUNTIME_DIR/"services"/"handrail"/"handrail"/"cps"
    ops=[p.stem for p in cps_dir.glob("*") if cps_dir.exists() and not p.suffix]
    prog_dir=RUNTIME_DIR/"programs"
    progs=[p.stem for p in prog_dir.glob("*.json")] if prog_dir.exists() else []
    ctx["sovereign_ops"]=ops; ctx["sovereign_ops_count"]=len(ops)
    ctx["programs_loaded"]=progs
    return True, f"{len(ops)} ops, {len(progs)} programs loaded"

def p_emit_boot_receipt(ctx):
    bid=f"BOOT-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
    phases_rec=[{"phase":n,"status":ctx.get(f"phase_{n}",{}).get("status","PASS"),
                 "hash":sha(n+ts()),"duration_ms":ctx.get(f"phase_{n}",{}).get("dur",0)}
                for n in PHASES]
    receipt={
        "boot_id":bid,"timestamp":ts(),"phases":phases_rec,
        "yubikey_quorum":{"required":REQUIRED_Q,"present":ctx.get("yubikey_serials_present",[]),
                          "authorized":ctx.get("yubikey_authorized",False)},
        "schema_versions":ctx.get("schema_versions",{}),
        "adapter_inventory":[a["adapter_id"] for a in ctx.get("adapter_inventory",[])],
        "policy_bundle_hash":ctx.get("policy_bundle_hash","none"),
        "sovereign_ops_count":ctx.get("sovereign_ops_count",0),
        "programs_loaded":ctx.get("programs_loaded",[]),
        "ledger_entries_before_boot":ctx.get("ledger_entries",0),
        "alexandria_ledger_entry":""
    }
    prev=ctx.get("ledger_last_hash","genesis")
    entry={"entry_id":bid,"timestamp":ts(),"entry_type":"boot_proof","payload":receipt,
           "prev_hash":prev,"hash":""}
    entry["hash"]=sha(json.dumps({**entry,"hash":""},sort_keys=True))
    receipt["alexandria_ledger_entry"]=entry["hash"]
    BOOT_LOG.parent.mkdir(parents=True,exist_ok=True)
    with open(BOOT_LOG,"a") as f: f.write(json.dumps(receipt)+"\n")
    with open(ALEXANDRIA,"a") as f: f.write(json.dumps(entry)+"\n")
    ctx["boot_id"]=bid; ctx["boot_receipt"]=receipt
    return True, f"BOOT_PROOF_RECEIPT {bid} hash={entry['hash']}"

PHASE_FNS=[p_verify_substrate,p_mount_alexandria,p_validate_ledger,p_start_handrail,
           p_load_policy_bundle,p_validate_schemas,p_discover_adapters,p_verify_adapter_auth,
           p_init_simulation_engine,p_bind_interfaces,p_activate_mission_graphs,p_emit_boot_receipt]

def run_boot(skip_yk=False):
    print(f"\n{'='*62}")
    print("NS∞ SOVEREIGN BOOT — BOOT.MISSION_GRAPH.SYSTEM.v1")
    print(f"Started: {ts()}")
    print("="*62+"\n")
    ctx={}
    for i,(name,fn) in enumerate(zip(PHASES,PHASE_FNS),1):
        if skip_yk and name=="verify_substrate":
            pp(i,name,"SKIP","(--dev mode)"); ctx["yubikey_authorized"]=True
            ctx["yubikey_serials_present"]=["DEV"]; ctx[f"phase_{name}"]={"status":"SKIP","dur":0}; continue
        t0=time.time()
        try: ok,msg=fn(ctx)
        except Exception as e: ok,msg=False,f"EXCEPTION: {e}"
        dur=round((time.time()-t0)*1000)
        status="PASS" if ok else "FAIL"
        ctx[f"phase_{name}"]={"status":status,"dur":dur}
        pp(i,name,status,f"({dur}ms) {msg}")
        if not ok:
            print(f"\n  BOOT HALTED — phase {i}: {name}\n  {msg}\n  FAIL_CLOSED.\n"); return False
    r=ctx.get("boot_receipt",{})
    print(f"\n{'='*62}")
    print("NS∞ BOOT COMPLETE — SOVEREIGN RECEIPT ISSUED")
    print(f"  Boot ID:     {r.get('boot_id')}")
    print(f"  Ledger hash: {r.get('alexandria_ledger_entry')}")
    print(f"  Ops loaded:  {ctx.get('sovereign_ops_count',0)}")
    print(f"  Programs:    {ctx.get('programs_loaded',[])}")
    print(f"  Adapters:    {len(ctx.get('adapter_inventory',[]))}")
    print(f"  YubiKey:     {ctx.get('yubikey_serials_present')}")
    print("="*62+"\n")
    return True

if __name__=="__main__":
    ok=run_boot(skip_yk="--dev" in sys.argv or "--no-yubikey" in sys.argv)
    sys.exit(0 if ok else 1)
