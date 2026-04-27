from services.aletheia_control.dashboard import AletheiaControlDashboard

def test_from_dict_round_trip():
    d = {"classifications":10,"atoms":3,"chains":2,"wastes":5,
         "control_ratio":0.3,"concern_leakage":0.04,"false_control_rate":0.01,
         "feedback_integrity":0.96,"influence_conversion":0.7,"omega":0.91}
    dash = AletheiaControlDashboard.from_dict(d)
    out = dash.to_dict()
    for k,v in d.items():
        assert out[k] == v
