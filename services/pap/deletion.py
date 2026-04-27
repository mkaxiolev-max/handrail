"""Lineage-preserving deletion. Decree P-7."""
from typing import List
from .models import AletheiaPAPResource, PAPQECFailure


PROTECTED_PATHS = {
    "identity.ctf_lineage_id",
    "identity.session_hash",
    "merkle_root",
    "T.evidence",     # evidence hashes immutable
    "receipts",       # all receipt slots
}


def can_delete(field_path: str) -> bool:
    """Returns True if the field is active surface debris (deletable)."""
    return not any(field_path.startswith(p) for p in PROTECTED_PATHS)


def attempt_delete(resource: AletheiaPAPResource, field_path: str) -> List[PAPQECFailure]:
    """Returns [] on legal deletion, [S9] on lineage attempt."""
    if not can_delete(field_path):
        return [PAPQECFailure(syndrome="S9",
                              description=f"lineage deletion attempt on {field_path}",
                              field_path=field_path)]
    return []
