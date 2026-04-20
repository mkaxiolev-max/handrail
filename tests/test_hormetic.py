import pytest
from services.gpx_omega import (
    HormeticBand, HormeticRun, HormeticResult, Signature, SignatureClassifier,
    fit_hormetic_curve, run_sweep, REFERENCE_FIXTURES,
)

def test_bands_ordered(): assert int(HormeticBand.B0) < int(HormeticBand.B5)

def test_classifier_brittle():
    assert SignatureClassifier().classify({0:90,1:70,2:50,3:30,4:10,5:20}) == Signature.BRITTLE

def test_classifier_super_gnoseogenic():
    assert SignatureClassifier().classify({0:60,1:65,2:72,3:82,4:90,5:75}) == Signature.SUPER_GNOSEOGENIC

def test_fit_hormetic():
    r = fit_hormetic_curve({0:70,1:75,2:85,3:80,4:60,5:72})
    assert r["peak_band"] == 2
    assert r["hormesis_index"] > 0.2

def test_run_sweep_stub():
    def fake(p):
        if "2" in p: return "4"
        return "paris"
    run = run_sweep(fake, REFERENCE_FIXTURES, "test", "fake")
    assert len(run.results) == len(REFERENCE_FIXTURES)

def test_band_score_aggregation():
    run = HormeticRun(run_id="t", model="m")
    run.results = [HormeticResult("1",HormeticBand.B0,1.0),
                   HormeticResult("2",HormeticBand.B0,1.0),
                   HormeticResult("3",HormeticBand.B4,0.5)]
    assert run.band_score(HormeticBand.B0) == 100.0
    assert run.band_score(HormeticBand.B4) == 50.0
