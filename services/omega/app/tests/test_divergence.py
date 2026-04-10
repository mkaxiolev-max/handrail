from app.engine.divergence import score_divergence


def test_default_divergence_score():
    assert score_divergence([])["divergence_score"] == 0.0


def test_divergence_detects_branch_spread():
    branch_results = [
        {
            "outputs": {"final_state": {"x": 1.0, "y": 2.0}},
            "divergence_components": {"constraint_pressure": 0.2, "model_mismatch": 0.1},
        },
        {
            "outputs": {"final_state": {"x": 4.0, "y": 5.0}},
            "divergence_components": {"constraint_pressure": 0.4, "model_mismatch": 0.2},
        },
    ]
    scored = score_divergence(branch_results)
    assert scored["divergence_score"] > 0.0
    assert scored["branch_spread"]["x"] == 3.0
