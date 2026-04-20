"""Q17 — judge ensemble tests."""
from services.judge_ensemble import JudgeVerdict, consensus

def test_unanimous_pass():
    vs = [JudgeVerdict("anthropic","pass",0.9),
          JudgeVerdict("openai",   "pass",0.8),
          JudgeVerdict("google",   "pass",0.85)]
    r = consensus(vs)
    assert r["verdict"] == "pass"
    assert r["families"] == 3

def test_diversity_bonus_applied():
    vs_single = [JudgeVerdict("anthropic","pass",0.9),
                 JudgeVerdict("anthropic","pass",0.9)]
    vs_multi  = [JudgeVerdict("anthropic","pass",0.9),
                 JudgeVerdict("openai",   "pass",0.9),
                 JudgeVerdict("google",   "pass",0.9)]
    assert consensus(vs_multi)["score"] >= consensus(vs_single)["score"]

def test_empty_defaults_review():
    assert consensus([])["verdict"] == "review"
