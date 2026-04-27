from services.pap.scoring import score_pap_resource


def test_complete_resource_scores_high(clean_resource):
    s = score_pap_resource(clean_resource)
    assert s.score_total >= 90, f"expected >=90; got {s.score_total} subs={s.subscores}"


def test_subscores_sum_equals_total(clean_resource):
    s = score_pap_resource(clean_resource)
    assert abs(s.score_total - sum(s.subscores.values())) < 1e-6


def test_grade_band_set(clean_resource):
    s = score_pap_resource(clean_resource)
    assert s.grade in {"WEB_PAGE","STRUCTURED","AGENT_USABLE",
                       "GOVERNED_PARITY","CANON_READY","THEORETICAL_MAX"}
