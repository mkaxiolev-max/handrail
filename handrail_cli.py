#!/usr/bin/env python3
"""
handrail — entry point
Add to PATH or alias:
  alias handrail='python3 /path/to/axiolev_runtime/services/handrail/handrail_cli.py'
"""
import sys
from pathlib import Path

# Ensure the handrail package is importable
HERE = Path(__file__).resolve().parent
HANDRAIL_PKG = HERE / "services" / "handrail"
if str(HANDRAIL_PKG) not in sys.path:
    sys.path.insert(0, str(HANDRAIL_PKG))

from handrail.cli.main import main
sys.exit(main())
