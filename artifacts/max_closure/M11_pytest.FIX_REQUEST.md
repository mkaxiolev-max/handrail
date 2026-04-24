# FIX REQUEST — M11_pytest

- run_id: 20260424T001858Z
- timestamp: 2026-04-24T00:19:10Z
- args: -x --tb=short
- log: /Users/axiolevns/.ns_max_closure/logs/M11_pytest.pytest.log

## Last 200 lines of pytest output
```
..................                                                       [ 11%]
ns/tests/test_cqhml_projection_service.py .............................  [ 14%]
ns/tests/test_cqhml_quaternion.py ...................................... [ 16%]
...................................                                      [ 19%]
ns/tests/test_cqhml_spin7_phi.py ..........................              [ 21%]
ns/tests/test_cqhml_story_atom_loom.py ................................. [ 23%]
....................                                                     [ 24%]
ns/tests/test_ncom.py .................................................. [ 28%]
.                                                                        [ 28%]
ns/tests/test_omega_primitives.py ....                                   [ 28%]
ns/tests/test_omega_projection.py ................................       [ 31%]
ns/tests/test_oracle_v2.py ............................                  [ 33%]
ns/tests/test_piic.py ............................................       [ 36%]
ns/tests/test_ril_engines.py ......................................      [ 38%]
ns/tests/test_ring1_constitutional_layer.py ......................       [ 40%]
ns/tests/test_ring2_substrate_layers.py ................................ [ 42%]
...                                                                      [ 43%]
ns/tests/test_ring3_loom.py ......................................       [ 45%]
ns/tests/test_ring4_canon_promotion.py ................................. [ 48%]
...............                                                          [ 49%]
ns/tests/test_ring5_external_gates_noted.py ..........                   [ 49%]
ns/tests/test_ring6_g2_invariant.py .....................                [ 51%]
ns/tests/test_ring7_final_cert.py ..................................     [ 53%]
ns/tests/test_ug_entity.py ....                                          [ 54%]
ns/tests/test_ui_named_routes.py ........                                [ 54%]
services/handrail/tests/test_router.py ............................      [ 56%]
services/handrail/tests/test_smoke.py .                                  [ 56%]
services/ns_core/test_adversarial.py ...ss.....                          [ 57%]
services/ns_core/test_voice_e2e.py sss                                   [ 57%]
services/omega/app/tests/test_health.py ..                               [ 57%]
services/omega/app/tests/test_runs.py ...                                [ 58%]
services/omega/app/tests/test_simulate.py ....                           [ 58%]
services/witness/tests/test_witness.py ..............                    [ 59%]
tests/abi/test_bridge_normalization.py .....                             [ 59%]
tests/abi/test_endpoint_fixes.py F

=================================== FAILURES ===================================
_______________________ test_pdp_decide_returns_v2_deny ________________________
/opt/homebrew/Cellar/python@3.14/3.14.2/Frameworks/Python.framework/Versions/3.14/lib/python3.14/urllib/request.py:1321: in do_open
    h.request(req.get_method(), req.selector, req.data, headers,
/opt/homebrew/Cellar/python@3.14/3.14.2/Frameworks/Python.framework/Versions/3.14/lib/python3.14/http/client.py:1358: in request
    self._send_request(method, url, body, headers, encode_chunked)
/opt/homebrew/Cellar/python@3.14/3.14.2/Frameworks/Python.framework/Versions/3.14/lib/python3.14/http/client.py:1404: in _send_request
    self.endheaders(body, encode_chunked=encode_chunked)
/opt/homebrew/Cellar/python@3.14/3.14.2/Frameworks/Python.framework/Versions/3.14/lib/python3.14/http/client.py:1353: in endheaders
    self._send_output(message_body, encode_chunked=encode_chunked)
/opt/homebrew/Cellar/python@3.14/3.14.2/Frameworks/Python.framework/Versions/3.14/lib/python3.14/http/client.py:1113: in _send_output
    self.send(msg)
/opt/homebrew/Cellar/python@3.14/3.14.2/Frameworks/Python.framework/Versions/3.14/lib/python3.14/http/client.py:1057: in send
    self.connect()
/opt/homebrew/Cellar/python@3.14/3.14.2/Frameworks/Python.framework/Versions/3.14/lib/python3.14/http/client.py:1023: in connect
    self.sock = self._create_connection(
/opt/homebrew/Cellar/python@3.14/3.14.2/Frameworks/Python.framework/Versions/3.14/lib/python3.14/socket.py:870: in create_connection
    raise exceptions[0]
/opt/homebrew/Cellar/python@3.14/3.14.2/Frameworks/Python.framework/Versions/3.14/lib/python3.14/socket.py:855: in create_connection
    sock.connect(sa)
E   ConnectionRefusedError: [Errno 61] Connection refused

During handling of the above exception, another exception occurred:
tests/abi/test_endpoint_fixes.py:34: in test_pdp_decide_returns_v2_deny
    status, body = _post("/pdp/decide", {"principal": "anon", "action": "canon.promote"})
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/abi/test_endpoint_fixes.py:19: in _post
    with urllib.request.urlopen(req, timeout=5) as r:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
/opt/homebrew/Cellar/python@3.14/3.14.2/Frameworks/Python.framework/Versions/3.14/lib/python3.14/urllib/request.py:187: in urlopen
    return opener.open(url, data, timeout)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
/opt/homebrew/Cellar/python@3.14/3.14.2/Frameworks/Python.framework/Versions/3.14/lib/python3.14/urllib/request.py:487: in open
    response = self._open(req, data)
               ^^^^^^^^^^^^^^^^^^^^^
/opt/homebrew/Cellar/python@3.14/3.14.2/Frameworks/Python.framework/Versions/3.14/lib/python3.14/urllib/request.py:504: in _open
    result = self._call_chain(self.handle_open, protocol, protocol +
/opt/homebrew/Cellar/python@3.14/3.14.2/Frameworks/Python.framework/Versions/3.14/lib/python3.14/urllib/request.py:464: in _call_chain
    result = func(*args)
             ^^^^^^^^^^^
/opt/homebrew/Cellar/python@3.14/3.14.2/Frameworks/Python.framework/Versions/3.14/lib/python3.14/urllib/request.py:1350: in http_open
    return self.do_open(http.client.HTTPConnection, req)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
/opt/homebrew/Cellar/python@3.14/3.14.2/Frameworks/Python.framework/Versions/3.14/lib/python3.14/urllib/request.py:1324: in do_open
    raise URLError(err)
E   urllib.error.URLError: <urlopen error [Errno 61] Connection refused>
=============================== warnings summary ===============================
services/ns_core/test_adversarial.py::test_projection_storytime_user_no_sensitivity_leak
  /opt/homebrew/lib/python3.14/site-packages/pydantic/main.py:464: UserWarning: Pydantic serializer warnings:
    PydanticSerializationUnexpectedValue(Expected `enum` - serialized value may not be as expected [field_name='classification', input_value='CONFIDENTIAL', input_type=str])
    return self.__pydantic_serializer__.to_python(

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
FAILED tests/abi/test_endpoint_fixes.py::test_pdp_decide_returns_v2_deny - ur...
!!!!!!!!!!!!!!!!!!!!!!!!!! stopping after 1 failures !!!!!!!!!!!!!!!!!!!!!!!!!!!
============= 1 failed, 830 passed, 5 skipped, 1 warning in 3.57s ==============
============================= test session starts ==============================
platform darwin -- Python 3.14.2, pytest-9.0.2, pluggy-1.6.0
rootdir: /Users/axiolevns/axiolev_runtime
configfile: pytest.ini
plugins: anyio-4.12.1, json-report-1.5.0, timeout-2.4.0, metadata-3.1.1, asyncio-1.3.0
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 1399 items

ns/tests/test_cqhml_contradiction_engine.py ............................ [  2%]
...                                                                      [  2%]
ns/tests/test_cqhml_dimensions.py ...................................    [  4%]
ns/tests/test_cqhml_omega_router.py .................................... [  7%]
..............                                                           [  8%]
ns/tests/test_cqhml_oracle_dim_gate.py ................................. [ 10%]
..................                                                       [ 11%]
ns/tests/test_cqhml_projection_service.py .............................  [ 14%]
ns/tests/test_cqhml_quaternion.py ...................................... [ 16%]
...................................                                      [ 19%]
ns/tests/test_cqhml_spin7_phi.py ..........................              [ 21%]
ns/tests/test_cqhml_story_atom_loom.py ................................. [ 23%]
....................                                                     [ 24%]
ns/tests/test_ncom.py .................................................. [ 28%]
.                                                                        [ 28%]
ns/tests/test_omega_primitives.py ....                                   [ 28%]
ns/tests/test_omega_projection.py ................................       [ 31%]
ns/tests/test_oracle_v2.py ............................                  [ 33%]
ns/tests/test_piic.py ............................................       [ 36%]
ns/tests/test_ril_engines.py ......................................      [ 38%]
ns/tests/test_ring1_constitutional_layer.py ......................       [ 40%]
ns/tests/test_ring2_substrate_layers.py ................................ [ 42%]
...                                                                      [ 43%]
ns/tests/test_ring3_loom.py ......................................       [ 45%]
ns/tests/test_ring4_canon_promotion.py ................................. [ 48%]
...............                                                          [ 49%]
ns/tests/test_ring5_external_gates_noted.py ..........                   [ 49%]
ns/tests/test_ring6_g2_invariant.py .....................                [ 51%]
ns/tests/test_ring7_final_cert.py ..................................     [ 53%]
ns/tests/test_ug_entity.py ....                                          [ 54%]
ns/tests/test_ui_named_routes.py ........                                [ 54%]
services/handrail/tests/test_router.py ............................      [ 56%]
services/handrail/tests/test_smoke.py .                                  [ 56%]
services/ns_core/test_adversarial.py ...ss.....                          [ 57%]
services/ns_core/test_voice_e2e.py sss                                   [ 57%]
services/omega/app/tests/test_health.py ..                               [ 57%]
services/omega/app/tests/test_runs.py ...                                [ 58%]
services/omega/app/tests/test_simulate.py ....                           [ 58%]
services/witness/tests/test_witness.py ..............                    [ 59%]
tests/abi/test_bridge_normalization.py .....                             [ 59%]
tests/abi/test_endpoint_fixes.py F

=================================== FAILURES ===================================
_______________________ test_pdp_decide_returns_v2_deny ________________________
/opt/homebrew/Cellar/python@3.14/3.14.2/Frameworks/Python.framework/Versions/3.14/lib/python3.14/urllib/request.py:1321: in do_open
    h.request(req.get_method(), req.selector, req.data, headers,
/opt/homebrew/Cellar/python@3.14/3.14.2/Frameworks/Python.framework/Versions/3.14/lib/python3.14/http/client.py:1358: in request
    self._send_request(method, url, body, headers, encode_chunked)
/opt/homebrew/Cellar/python@3.14/3.14.2/Frameworks/Python.framework/Versions/3.14/lib/python3.14/http/client.py:1404: in _send_request
    self.endheaders(body, encode_chunked=encode_chunked)
/opt/homebrew/Cellar/python@3.14/3.14.2/Frameworks/Python.framework/Versions/3.14/lib/python3.14/http/client.py:1353: in endheaders
    self._send_output(message_body, encode_chunked=encode_chunked)
/opt/homebrew/Cellar/python@3.14/3.14.2/Frameworks/Python.framework/Versions/3.14/lib/python3.14/http/client.py:1113: in _send_output
    self.send(msg)
/opt/homebrew/Cellar/python@3.14/3.14.2/Frameworks/Python.framework/Versions/3.14/lib/python3.14/http/client.py:1057: in send
    self.connect()
/opt/homebrew/Cellar/python@3.14/3.14.2/Frameworks/Python.framework/Versions/3.14/lib/python3.14/http/client.py:1023: in connect
    self.sock = self._create_connection(
/opt/homebrew/Cellar/python@3.14/3.14.2/Frameworks/Python.framework/Versions/3.14/lib/python3.14/socket.py:870: in create_connection
    raise exceptions[0]
/opt/homebrew/Cellar/python@3.14/3.14.2/Frameworks/Python.framework/Versions/3.14/lib/python3.14/socket.py:855: in create_connection
    sock.connect(sa)
E   ConnectionRefusedError: [Errno 61] Connection refused

During handling of the above exception, another exception occurred:
tests/abi/test_endpoint_fixes.py:34: in test_pdp_decide_returns_v2_deny
    status, body = _post("/pdp/decide", {"principal": "anon", "action": "canon.promote"})
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/abi/test_endpoint_fixes.py:19: in _post
    with urllib.request.urlopen(req, timeout=5) as r:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
/opt/homebrew/Cellar/python@3.14/3.14.2/Frameworks/Python.framework/Versions/3.14/lib/python3.14/urllib/request.py:187: in urlopen
    return opener.open(url, data, timeout)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
/opt/homebrew/Cellar/python@3.14/3.14.2/Frameworks/Python.framework/Versions/3.14/lib/python3.14/urllib/request.py:487: in open
    response = self._open(req, data)
               ^^^^^^^^^^^^^^^^^^^^^
/opt/homebrew/Cellar/python@3.14/3.14.2/Frameworks/Python.framework/Versions/3.14/lib/python3.14/urllib/request.py:504: in _open
    result = self._call_chain(self.handle_open, protocol, protocol +
/opt/homebrew/Cellar/python@3.14/3.14.2/Frameworks/Python.framework/Versions/3.14/lib/python3.14/urllib/request.py:464: in _call_chain
    result = func(*args)
             ^^^^^^^^^^^
/opt/homebrew/Cellar/python@3.14/3.14.2/Frameworks/Python.framework/Versions/3.14/lib/python3.14/urllib/request.py:1350: in http_open
    return self.do_open(http.client.HTTPConnection, req)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
/opt/homebrew/Cellar/python@3.14/3.14.2/Frameworks/Python.framework/Versions/3.14/lib/python3.14/urllib/request.py:1324: in do_open
    raise URLError(err)
E   urllib.error.URLError: <urlopen error [Errno 61] Connection refused>
=============================== warnings summary ===============================
services/ns_core/test_adversarial.py::test_projection_storytime_user_no_sensitivity_leak
  /opt/homebrew/lib/python3.14/site-packages/pydantic/main.py:464: UserWarning: Pydantic serializer warnings:
    PydanticSerializationUnexpectedValue(Expected `enum` - serialized value may not be as expected [field_name='classification', input_value='CONFIDENTIAL', input_type=str])
    return self.__pydantic_serializer__.to_python(

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
FAILED tests/abi/test_endpoint_fixes.py::test_pdp_decide_returns_v2_deny - ur...
!!!!!!!!!!!!!!!!!!!!!!!!!! stopping after 1 failures !!!!!!!!!!!!!!!!!!!!!!!!!!!
============= 1 failed, 830 passed, 5 skipped, 1 warning in 3.48s ==============
```

## Suggested resolution
1. Open the failing tests; triage into (a) production-code bug, (b) test-spec bug, (c) flake.
2. For (a) fix the code; for (b) update spec with rationale in commit message; for (c) quarantine with xfail + ticket.
3. Re-run ns_max_closure.sh — the phase will resume from M11_pytest.
