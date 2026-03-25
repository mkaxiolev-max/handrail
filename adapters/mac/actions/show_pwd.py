import os
def execute():
    try:
        return {"ok": True, "pwd": os.getcwd()}
    except Exception as e:
        return {"ok": False, "error": str(e)}