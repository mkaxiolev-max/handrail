import os, pytest
from services.aletheia_control.service import AletheiaControlService
from services.aletheia_control.middleware import AletheiaControlMiddleware
from services.aletheia_control.models import ControlInput

def test_observation_mode_does_not_block(monkeypatch):
    monkeypatch.delenv("ALETHEIA_CONTROL_ENFORCE", raising=False)
    svc = AletheiaControlService(); mw = AletheiaControlMiddleware(svc)
    called = {"n": 0}
    mw.gate("handrail.execute", {"input_id":"inp_unknown"}, lambda: called.update(n=1))
    assert called["n"] == 1

def test_enforce_mode_blocks_without_classification(monkeypatch):
    monkeypatch.setenv("ALETHEIA_CONTROL_ENFORCE", "1")
    svc = AletheiaControlService(); mw = AletheiaControlMiddleware(svc)
    with pytest.raises(PermissionError):
        mw.gate("handrail.execute", {"input_id":"inp_missing"}, lambda: None)

def test_enforce_mode_allows_with_classification(monkeypatch):
    monkeypatch.setenv("ALETHEIA_CONTROL_ENFORCE", "1")
    svc = AletheiaControlService(); mw = AletheiaControlMiddleware(svc)
    inp = ControlInput(input_id="inp_present", text="I will run tests",
                       source="t", urgency=0.5, reversibility=0.5, actor="self")
    from services.aletheia_control.classifier import classify
    svc.record_classification(inp, classify(inp))
    out = mw.gate("handrail.execute", {"input_id":"inp_present"}, lambda: "ok")
    assert out == "ok"
