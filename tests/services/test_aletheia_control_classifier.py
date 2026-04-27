"""Classifier accuracy >=0.97 on 300-input golden corpus."""
import json, pathlib, pytest
from services.aletheia_control.models import ControlInput, ControlCircle
from services.aletheia_control.classifier import classify

CORPUS = json.loads((pathlib.Path("tests/golden_corpus/aletheia_control_300_inputs.json")).read_text())

def _to_inp(ex, i):
    return ControlInput(input_id=f"inp_gc{i:04d}", text=ex["input"],
                        source="golden", urgency=0.5, reversibility=0.5, actor="self")

@pytest.mark.timeout(60)
def test_corpus_size():
    assert len(CORPUS) == 300

@pytest.mark.timeout(60)
def test_classifier_accuracy_ge_097():
    correct = 0
    for i, ex in enumerate(CORPUS):
        cls = classify(_to_inp(ex, i))
        if cls.circle.value == ex["label"]:
            correct += 1
    acc = correct / len(CORPUS)
    assert acc >= 0.97, f"accuracy {acc:.4f} < 0.97"

@pytest.mark.timeout(30)
def test_weights_sum_to_one():
    cls = classify(_to_inp({"input":"I will commit the spec"}, 1))
    assert abs(cls.control_weight + cls.influence_weight + cls.concern_weight - 1.0) < 1e-3
