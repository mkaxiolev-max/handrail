"""Root conftest — adds ns_core to sys.path for all tests."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "services/ns_core"))
