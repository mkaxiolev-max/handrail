"""C08 — MISSING-029: Autonomous Goal Formation tests. I8."""
from services.goal_formation.formation import GoalRegistry, Goal, GoalStatus, GoalPriority


def test_form_goal_from_context():
    r = GoalRegistry()
    g = r.form_goal({"score": 92.0, "target": 97.0})
    assert isinstance(g, Goal)


def test_form_goal_with_missing_fields_is_high_priority():
    r = GoalRegistry()
    g = r.form_goal({"score": None, "band": ""})
    assert g.priority == GoalPriority.HIGH


def test_form_goal_complete_context_is_low_priority():
    r = GoalRegistry()
    g = r.form_goal({"score": 92.0, "band": "provisional"})
    assert g.priority == GoalPriority.LOW


def test_rank_goals_by_priority():
    r = GoalRegistry()
    r.form_goal({"a": "ok"})
    r.form_goal({"b": None})
    ranked = r.rank_goals()
    assert ranked[0].priority.value <= ranked[-1].priority.value


def test_update_goal_status():
    r = GoalRegistry()
    g = r.form_goal({"x": 1})
    r.update_status(g.goal_id, GoalStatus.ACTIVE)
    assert r.active_goals()[0].goal_id == g.goal_id


def test_pending_goals_initially():
    r = GoalRegistry()
    r.form_goal({"x": 1})
    assert len(r.pending_goals()) == 1


def test_goal_has_context_keys():
    r = GoalRegistry()
    g = r.form_goal({"foo": 1, "bar": 2})
    assert "foo" in g.context_keys and "bar" in g.context_keys
