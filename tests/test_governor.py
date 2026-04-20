import pytest, time
from services.governor import (
    ZoneClassifier, Zone, ReplicationCoordinator, ReplicaVerdict,
    NygardCircuitBreaker, BreakerState, EWMADrift, PSI,
)

def test_zone_block():      assert ZoneClassifier().classify(20).zone==Zone.BLOCK
def test_zone_review():     assert ZoneClassifier().classify(50).zone==Zone.REVIEW
def test_zone_pass():       assert ZoneClassifier().classify(70).zone==Zone.PASS
def test_zone_ha():         assert ZoneClassifier().classify(85).zone==Zone.HIGH_ASSURANCE
def test_delta_alert():     assert ZoneClassifier().classify(87,prior=90).delta_action=="ALERT"
def test_delta_block():     assert ZoneClassifier().classify(80,prior=90).zone==Zone.BLOCK
def test_delta_hard_halt(): assert ZoneClassifier().classify(75,prior=90).delta_action=="HARD_HALT"

def test_replication_agreement():
    coord=ReplicationCoordinator()
    p=ReplicaVerdict("g1","d1",85,"HIGH_ASSURANCE","sa","ph",time.time())
    s=ReplicaVerdict("g2","d1",84,"HIGH_ASSURANCE","sb","ph",time.time())
    assert coord.quorum_verdict(p,s)["agreement"] is True

def test_replication_disagree_escalates():
    coord=ReplicationCoordinator()
    p=ReplicaVerdict("g1","d1",85,"PASS","sa","ph",time.time())
    s=ReplicaVerdict("g2","d1",45,"REVIEW","sb","ph",time.time())
    v=coord.quorum_verdict(p,s)
    assert v["agreement"] is False and v["escalate_to_hic"] is True

def test_krippendorff_perfect():
    coord=ReplicationCoordinator()
    for i in range(100):
        p=ReplicaVerdict("g1",f"d{i}",70,"PASS","s","p",time.time())
        s=ReplicaVerdict("g2",f"d{i}",71,"PASS","s","p",time.time())
        coord.record_pair(p,s)
    assert coord.krippendorff_alpha()>=0.9

def test_circuit_breaker_opens():
    cb=NygardCircuitBreaker(block_threshold=3,window_size=5)
    for _ in range(3): cb.record("BLOCK")
    assert cb.state==BreakerState.OPEN

def test_circuit_breaker_stays_closed():
    cb=NygardCircuitBreaker(block_threshold=5,window_size=20)
    for _ in range(10): cb.record("PASS")
    assert cb.state==BreakerState.CLOSED

def test_ewma_drift():
    d=EWMADrift(baseline=50.0,baseline_sigma=5.0)
    for _ in range(10): d.update(50.0)
    assert abs(d.update(50.0))<1.0
    for _ in range(20): d.update(70.0)
    assert d.update(70.0)>2.0

def test_psi_stable():
    assert PSI([50.0]*100,[50.0]*100)<0.1

def test_psi_shifted():
    import random; random.seed(42)
    base=[random.gauss(50,5) for _ in range(200)]
    cur=[random.gauss(70,5) for _ in range(200)]
    assert PSI(base,cur)>0.25
