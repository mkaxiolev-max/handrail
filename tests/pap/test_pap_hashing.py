from services.pap.hashing import (
    canonical_json, compute_merkle_root, verify_merkle_root,
)


def test_canonical_json_deterministic():
    a = canonical_json({"b": 1, "a": 2})
    b = canonical_json({"a": 2, "b": 1})
    assert a == b


def test_merkle_root_recomputable(clean_resource):
    d = clean_resource.dict()
    assert verify_merkle_root(d) is True


def test_merkle_divergence_detected_on_field_mutation(clean_resource):
    d = clean_resource.dict()
    d["H"]["summary"] = "Mutated"
    assert verify_merkle_root(d) is False
