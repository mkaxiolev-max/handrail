"""v10 smoke tests — team runtime."""
import pytest
from services.ns.nss.lenses.teams import REGISTRY

def test_five_teams_registered():
    ids = {t.team_id for t in REGISTRY.list()}
    assert ids == {"architecture","math_phi","data_engineering","validation_audit","web_crawl"}

def test_solo_quorum_default():
    for t in REGISTRY.list():
        assert t.charter.quorum_n_of_m == (1, 1)
        assert "mike" in t.on_call_rotation

def test_each_team_has_cps_lanes():
    for t in REGISTRY.list():
        assert len(t.charter.cps_lanes) >= 2, f"{t.team_id} has < 2 CPS lanes"

def test_each_team_has_owned_lenses():
    for t in REGISTRY.list():
        assert len(t.charter.owned_lenses) >= 1, f"{t.team_id} owns no lenses"

def test_each_team_has_ci_gates():
    for t in REGISTRY.list():
        assert len(t.charter.ci_gates) >= 1, f"{t.team_id} has no CI gates"
