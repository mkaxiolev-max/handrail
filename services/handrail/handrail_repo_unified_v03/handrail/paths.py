import os
from pathlib import Path

def default_db_path() -> str:
    home = Path.home()
    base = home / "Library" / "Application Support" / "Handrail"
    base.mkdir(parents=True, exist_ok=True)
    return str(base / "handrail.db")

def resolve_db_path() -> str:
    return os.environ.get("HANDRAIL_DB") or default_db_path()
