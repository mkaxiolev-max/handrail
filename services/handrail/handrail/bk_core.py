import hashlib, json, os
from datetime import datetime
from pathlib import Path

def apply_black_knight_protocol(cps_dict, result, run_id):
    # HEARTBEAT: Prove the function was entered
    Path('/app/handrail/bk_heartbeat.txt').write_text(f"Entered at {datetime.utcnow().isoformat()}")
    
    try:
        # Identity
        input_state = json.dumps(cps_dict, sort_keys=True)
        input_hash = hashlib.sha256(input_state.encode()).hexdigest()
        
        # Ledger (strictly local for this proof)
        l_file = Path('/app/handrail/ledger_chain.json')
        prev_h = '0' * 64
        if l_file.exists():
            try:
                prev_h = json.loads(l_file.read_text()).get('last_hash', prev_h)
            except: pass
        
        c_hash = hashlib.sha256((prev_h + input_hash).encode()).hexdigest()
        
        # Manifest
        result['identity'] = {'input_hash': input_hash, 'timestamp': datetime.utcnow().isoformat()}
        result['ledger'] = {'prev_hash': prev_h, 'hash': c_hash}
        
        # Persist
        if not l_file.exists():
            l_file.write_text(json.dumps({'runs': [], 'last_hash': c_hash}, indent=2))
        
        data = json.loads(l_file.read_text())
        data['runs'].append({'run_id': run_id, 'hash': c_hash})
        data['last_hash'] = c_hash
        l_file.write_text(json.dumps(data, indent=2))
        
    except Exception as e:
        Path('/app/handrail/bk_error.txt').write_text(str(e))
        result['bk_error'] = str(e)
        
    return result
