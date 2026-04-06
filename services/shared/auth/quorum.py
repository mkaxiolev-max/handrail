"""YubiKey quorum stubs."""
from typing import Optional


ACTIVE_YUBIKEY_SERIALS = ["26116460"]
QUORUM_THRESHOLD = 1  # expands to 2-of-3 when slot_2 provisioned


def quorum_satisfied(verified_serials: list[str]) -> bool:
    active = set(ACTIVE_YUBIKEY_SERIALS)
    verified = set(verified_serials)
    return len(active & verified) >= QUORUM_THRESHOLD


def is_yubikey_verified(yubikey_verified: Optional[bool]) -> bool:
    return yubikey_verified is True
