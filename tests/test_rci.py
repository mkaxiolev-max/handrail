"""Q10 — RCI harness tests."""
from services.rci import evaluate_edit

def test_clean_edit_high_rci():
    before = {"capital_of_france":"paris","sky_color":"blue",
              "france_language":"french","eiffel_city":"paris",
              "paris_country":"france"}
    after  = {"capital_of_france":"lyon","sky_color":"blue",
              "france_language":"french","eiffel_city":"lyon",
              "paris_country":"france"}
    r = evaluate_edit(before, after,
                      off_topic   = ["sky_color","france_language"],
                      paraphrases = ["capital_of_france","capital_of_france"],
                      downstream  = ["eiffel_city"])
    assert r.rci() > 0.85

def test_leaky_edit_low_locality():
    before = {"a":"1","b":"2","c":"3"}
    after  = {"a":"9","b":"9","c":"9"}   # edit leaked everywhere
    r = evaluate_edit(before, after,
                      off_topic=["b","c"],
                      paraphrases=["a","a"],
                      downstream=["a"])
    assert r.locality == 0.0
