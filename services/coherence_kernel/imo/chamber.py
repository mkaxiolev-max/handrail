"""Constitutional Chamber — quorum model for written override adjudication.

Override requires:
  - explicit reason (non-empty)
  - yubikey_receipt (non-empty, 64-char hex digest)
  - quorum_satisfied: at least 1 active slot (expands to 2-of-3 when second key provisioned)
"""
from __future__ import annotations
import re

_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_ACTIVE_SLOTS = 1  # grows to 2 when slot_2 enrolled


def quorum_satisfied(yubikey_receipt: str) -> bool:
    """A valid 64-char hex receipt satisfies the current 1-of-1 quorum."""
    return bool(_HEX64.match(yubikey_receipt))


def validate_override(reason: str, yubikey_receipt: str) -> None:
    """Raise ValueError if override cannot be accepted by the chamber."""
    if not reason or not reason.strip():
        raise ValueError("override requires non-empty written reason")
    if not quorum_satisfied(yubikey_receipt):
        raise ValueError(
            f"override requires valid 64-char hex yubikey_receipt; got {yubikey_receipt!r}"
        )
