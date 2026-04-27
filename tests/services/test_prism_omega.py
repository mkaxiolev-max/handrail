"""C17 — PRISM-Ω routing tests. I6."""
from services.prism_omega.router import PRISMRouter, Reality, INTENT_ROUTING


def test_known_intent_routed():
    r = PRISMRouter()
    d = r.route("semantic")
    assert d.primary == Reality.LEXICON


def test_knowledge_routes_to_alexandria():
    r = PRISMRouter()
    d = r.route("knowledge")
    assert d.primary == Reality.ALEXANDRIA


def test_territory_routes_to_san():
    r = PRISMRouter()
    d = r.route("territory")
    assert d.primary == Reality.SAN


def test_self_modify_routes_to_omega():
    r = PRISMRouter()
    d = r.route("self_modify")
    assert d.primary == Reality.OMEGA


def test_unknown_intent_default():
    r = PRISMRouter()
    d = r.route("foobar_xyz")
    assert d.confidence < 0.9


def test_decision_count():
    r = PRISMRouter()
    r.route("voice")
    r.route("memory")
    assert r.decision_count() == 2


def test_last_decision():
    r = PRISMRouter()
    r.route("claim")
    d = r.last_decision()
    assert d.intent == "claim"
