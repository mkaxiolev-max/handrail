"""Root conftest — adds axiolev_runtime to sys.path for all test runs."""
import sys, pathlib
RUNTIME = pathlib.Path(__file__).parent
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))
