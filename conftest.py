"""Root conftest — sys.path bootstrap for all tests."""
import sys, os
_ROOT = os.path.dirname(os.path.abspath(__file__))
for _p in [_ROOT, os.path.join(_ROOT, "services/ns_core")]:
    if _p not in sys.path:
        sys.path.insert(0, _p)
