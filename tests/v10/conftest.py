"""v10 test conftest — ensures RUNTIME on path."""
import sys, pathlib
RUNTIME = pathlib.Path(__file__).parent.parent.parent
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))
