from services.pap.deletion import attempt_delete, can_delete


def test_active_surface_deletable():
    assert can_delete("H.persuasion_flags") is True


def test_lineage_deletion_blocked():
    assert can_delete("identity.ctf_lineage_id") is False
    assert can_delete("identity.session_hash") is False


def test_evidence_hash_deletion_blocked():
    assert can_delete("T.evidence") is False


def test_attempt_delete_lineage_returns_S9(clean_resource):
    failures = attempt_delete(clean_resource, "identity.ctf_lineage_id")
    assert len(failures) == 1
    assert failures[0].syndrome == "S9"
