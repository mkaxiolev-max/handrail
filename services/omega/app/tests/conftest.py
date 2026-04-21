"""conftest.py -- ensure services/omega/app is importable as app package. AXIOLEV 2026."""
import sys, pathlib
_APP_DIR = pathlib.Path(__file__).resolve().parents[1]
_SVC_DIR = _APP_DIR.parent
for p in (str(_SVC_DIR), str(_APP_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)
