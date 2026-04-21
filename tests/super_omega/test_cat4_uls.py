"""Category 4 — ULS (User Local System). AXIOLEV © 2026."""
from services.omega_logos.layers.uls import read_local, write_local

def test_4_1_read_write_local_file(tmp_path):
    p = str(tmp_path / "demo.txt")
    ok, op1 = write_local(p, "hello")
    assert ok and op1.after_sha
    ok2, data, op2 = read_local(p)
    assert ok2 and data == "hello" and op2.before_sha == op1.after_sha

def test_4_2_unsafe_path_blocked():
    ok, _ = write_local("/etc/hosts_oops", "blocked")
    assert ok is False, "must refuse writes outside SAFE_ROOTS"
