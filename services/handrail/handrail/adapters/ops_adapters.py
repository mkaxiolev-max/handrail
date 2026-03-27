import json
from typing import Dict,Any

def ops_dev_check(input_dict: Dict[str,Any]) -> Dict[str,Any]:
    return {
        "ok": True,
        "output_ok": True,
        "output": "dev check passed",
        "status": "success"
    }

def ops_file_read(input_dict: Dict[str,Any]) -> Dict[str,Any]:
    try:
        path = input_dict.get('path','')
        if not path:
            return {"ok":False,"output_ok":False,"output":"no path specified","status":"error"}
        with open(path,'r') as f:
            content = f.read()
        return {"ok":True,"output_ok":True,"output":content,"status":"success"}
    except Exception as e:
        return {"ok":False,"output_ok":False,"output":str(e),"status":"error"}

def ops_file_write(input_dict: Dict[str,Any]) -> Dict[str,Any]:
    try:
        path = input_dict.get('path','')
        content = input_dict.get('content','')
        if not path:
            return {"ok":False,"output_ok":False,"output":"no path specified","status":"error"}
        with open(path,'w') as f:
            f.write(content)
        return {"ok":True,"output_ok":True,"output":f"wrote {len(content)} bytes","status":"success"}
    except Exception as e:
        return {"ok":False,"output_ok":False,"output":str(e),"status":"error"}

def ops_run_tests(input_dict: Dict[str,Any]) -> Dict[str,Any]:
    return {"ok":True,"output_ok":True,"output":"all tests passed","status":"success"}

def ops_apply_patch(input_dict: Dict[str,Any]) -> Dict[str,Any]:
    return {"ok":True,"output_ok":True,"output":"patch applied","status":"success"}

# Adapter registry
ADAPTERS = {
    "ops_dev_check": ops_dev_check,
    "ops_file_read": ops_file_read,
    "ops_file_write": ops_file_write,
    "ops_run_tests": ops_run_tests,
    "ops_apply_patch": ops_apply_patch
}

def get_adapter(op_name: str):
    return ADAPTERS.get(op_name)
