from services.aletheia_control.drift import drift_score, is_drifting
from services.aletheia_control.models import ControlClassification, ControlCircle

def _cls(c, n):
    return [ControlClassification(input_id=f"inp_x{i:06d}", circle=c,
        control_weight=1.0 if c==ControlCircle.CONTROL else 0.0,
        influence_weight=1.0 if c==ControlCircle.INFLUENCE else 0.0,
        concern_weight=1.0 if c==ControlCircle.CONCERN else 0.0,
        rationale="t", actuator_exists=True, feedback_observable=True,
        recommended_action="x") for i in range(n)]

def test_no_drift_when_identical():
    a = _cls(ControlCircle.CONTROL, 50); b = _cls(ControlCircle.CONTROL, 50)
    assert drift_score(a, b) == 0.0; assert is_drifting(a, b) is False

def test_drift_detected_when_distribution_shifts():
    a = _cls(ControlCircle.CONTROL, 50)
    b = _cls(ControlCircle.CONCERN, 50)
    assert drift_score(a, b) > 0.05; assert is_drifting(a, b) is True
