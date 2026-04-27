"""C01 — MISSING-031: Self-Modification Sandbox tests. I8."""
import pytest
from services.self_mod_sandbox.sandbox import SelfModSandbox, FORBIDDEN_PATHS


@pytest.fixture
def sandbox():
    return SelfModSandbox()


def test_sandbox_blocks_forbidden_paths(sandbox):
    for fp in FORBIDDEN_PATHS:
        with pytest.raises(ValueError, match="forbidden"):
            sandbox.propose_modification(fp + "some_file.py", "content")


def test_sandbox_allows_allowed_paths(sandbox):
    p = sandbox.propose_modification("services/new_service/module.py", "x = 1")
    assert p.approved


def test_sandbox_produces_audit_trail(sandbox):
    sandbox.propose_modification("some/path.py", "code")
    assert sandbox.audit_length() >= 1


def test_sandbox_forbidden_path_in_audit(sandbox):
    try:
        sandbox.propose_modification("tools/ns_test_ontology/hack.py", "bad")
    except ValueError:
        pass
    log = sandbox.get_audit_log()
    rejected = [e for e in log if not e["approved"]]
    assert len(rejected) >= 1


def test_sandbox_recursion_guard_covers_all_forbidden(sandbox):
    for fp in FORBIDDEN_PATHS:
        with pytest.raises(ValueError):
            sandbox.propose_modification(fp + "x.py", "")


def test_sandbox_approved_proposals_tracked(sandbox):
    sandbox.propose_modification("services/foo/bar.py", "x")
    sandbox.propose_modification("services/baz/qux.py", "y")
    assert len(sandbox.approved_proposals()) == 2


def test_sandbox_content_hash_in_proposal(sandbox):
    p = sandbox.propose_modification("a/b.py", "hello world")
    assert len(p.content_hash) == 16


def test_sandbox_proposal_has_timestamp(sandbox):
    p = sandbox.propose_modification("a/b.py", "t")
    assert "T" in p.proposed_at
