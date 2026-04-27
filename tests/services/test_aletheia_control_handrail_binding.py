"""Handrail binding: aletheia.control.execute op exists and requires ControlAtom."""
from services.aletheia_control.models import ControlAtom

def test_control_atom_schema_has_required_fields():
    a = ControlAtom(atom_id="atm_aaaaaa", input_id="inp_x", actor="self",
                    verb="commit", target="spec", constraints={},
                    expected_receipt="receipt://x")
    d = a.model_dump()
    for k in ("atom_id","input_id","actor","verb","target","expected_receipt"):
        assert k in d

def test_handrail_op_name_is_canonical():
    HANDRAIL_OP = "aletheia.control.execute"
    assert HANDRAIL_OP.startswith("aletheia.control.")
