"""Q12 — hormetic profile classifier tests."""
from services.gpx_omega.profiler import ProfileClassifier, Signature

def test_super_gnoseogenic_profile():
    c = ProfileClassifier()
    assert c.classify({0:60,1:65,2:72,3:82,4:90,5:80}) == Signature.SUPER_GNOSEOGENIC

def test_brittle_profile():
    c = ProfileClassifier()
    assert c.classify({0:90,1:80,2:70,3:60,4:50,5:40}) == Signature.BRITTLE

def test_plastic_profile():
    c = ProfileClassifier()
    sig = c.classify({0:80,1:82,2:78,3:75,4:72,5:79})
    assert sig in (Signature.PLASTIC, Signature.GENERATIVE)
