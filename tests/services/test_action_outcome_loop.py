"""C09 — MISSING-030: Action-Outcome Loop tests. I8."""
from services.action_outcome_loop.loop import ActionOutcomeLoop, ActionRecord


def test_loop_records_action():
    l = ActionOutcomeLoop()
    r = l.record_action("compute", 5, lambda x: x * 2)
    assert isinstance(r, ActionRecord)


def test_loop_output_captured():
    l = ActionOutcomeLoop()
    r = l.record_action("double", 3, lambda x: x * 2)
    assert "6" in r.output_summary


def test_loop_analyze_success_rate():
    l = ActionOutcomeLoop()
    l.record_action("a", 1, lambda x: x, lambda i, o: 1.0)
    l.record_action("b", 2, lambda x: x, lambda i, o: 0.0)
    analysis = l.analyze()
    assert analysis["success_rate"] == 0.5


def test_loop_empty_analyze():
    l = ActionOutcomeLoop()
    assert l.analyze()["total"] == 0


def test_loop_records_multiple():
    l = ActionOutcomeLoop()
    for i in range(5):
        l.record_action(f"op{i}", i, lambda x: x)
    assert len(l.records()) == 5


def test_loop_outcome_score_bounded():
    l = ActionOutcomeLoop()
    r = l.record_action("x", 1, lambda x: x, lambda i, o: 0.75)
    assert 0.0 <= r.outcome_score <= 1.0
