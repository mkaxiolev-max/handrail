"""Self-loop MUST call /pi/check before any mutation."""
import asyncio
from autopoiesis.self_loop import self_adapt, AdaptationProposal
from autopoiesis.runtime import ProgramRuntime


def _run(coro):
    return asyncio.run(coro)


def test_canon_overwrite_blocked_by_pi():
    proposal = AdaptationProposal("canon.overwrite")
    result = _run(self_adapt(proposal))
    assert result["ok"] is False
    assert result["failure_reason"] == "pi_blocked"


def test_wire_send_blocked_by_pi():
    proposal = AdaptationProposal("wire.send", {"amount": 100})
    result = _run(self_adapt(proposal))
    assert result["ok"] is False
    assert "pi_blocked" in result.get("failure_reason", "")


def test_safe_op_adapts():
    rt = ProgramRuntime()
    proposal = AdaptationProposal("ledger.read", {"target": "recent"}, evidence="sha:abc")
    result = _run(self_adapt(proposal, runtime=rt))
    assert result["ok"] is True
    assert result["return_block_version"] == 2


def test_pi_check_is_in_checks_field():
    proposal = AdaptationProposal("canon.overwrite")
    result = _run(self_adapt(proposal))
    assert len(result.get("checks", [])) > 0
    # pi result should be in checks
    pi_check = result["checks"][0]
    assert "admissible" in pi_check


def test_null_evidence_blocks_consequential_op():
    proposal = AdaptationProposal("execute.thing", {}, evidence=None)
    result = _run(self_adapt(proposal))
    assert result["ok"] is False
