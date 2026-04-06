"""Token validation stubs."""
import os
from typing import Optional


def validate_api_key(token: Optional[str]) -> bool:
    expected = os.environ.get("NS_API_KEY")
    if not expected:
        return True  # open if not configured
    return token == expected
