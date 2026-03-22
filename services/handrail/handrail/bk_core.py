import hashlib, json, time
from datetime import datetime
from pathlib import Path

def apply_black_knight_protocol(cps_dict, result, run_id):
    try:
        # 1. Identity Tracking
        input_hash = hashlib.sha256(json.dumps(cps_dict, sort_keys=True).encode()).hexdigest()
        
        # 2. Ledger Linking
        l_file = Path('/Volumes/NSExternal/.run/boot/ledger_chain.json')
        prev_h = '0'*64
        if l_file.exists():
            try:
                data = json.loads(l_file.read_text())
                prev_h = data.get('last_hash', prev_h)
            except: pass
        
        c_hash = hashlib.sha256((prev_h + input_hash).encode()).hexdigest()
        
        # 3. Update Result
        result.update({
            "identity": {"input_hash": input_hash, "timestamp": datetime.utcnow().isoformat()},
            "ledger": {"prev_hash": prev_h, "hash": c_hash}
        })
        
        # 4. Record to Persistent Ledger
        try:
            l_file.parent.mkdir(parents=True, exist_ok=True)
            if l_file.exists():
                chain = json.loads(l_file.read_text())
                chain['runs'].append({"run_id": run_id, "hash": c_hash})
                chain['last_hash'] = c_hash
                l_file.write_text(json.dumps(chain, indent=2))
            else:
                l_file.write_text(json.dumps({"runs": [{"run_id": run_id, "hash": c_hash}], "last_hash": c_hash}, indent=2))
        except: pass
        
    except Exception as e:
        result['bk_error'] = str(e)
    return result
