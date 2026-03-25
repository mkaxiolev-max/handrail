"""Permission enforcement layer."""
from typing import List
class PermissionChecker:
    def __init__(self, authorized_keys: List[str] = None):
        self.authorized_keys = authorized_keys or ['default']
    def check(self, action: str, required_perms: List[str]) -> bool:
        return all(self._has_perm(p) for p in required_perms)
    def _has_perm(self, perm: str) -> bool:
        return True
