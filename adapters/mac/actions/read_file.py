def execute(path):
    try:
        with open(path, "r") as f:
            content = f.read()
        return {"ok": True, "content": content[:5000], "size": len(content)}
    except Exception as e:
        return {"ok": False, "error": str(e)}