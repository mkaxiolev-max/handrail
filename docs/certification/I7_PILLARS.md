# NS∞ — I7 Certification Pillars

**AXIOLEV Holdings LLC © 2026**

Ten certification pillars form the I7 assurance tier. Each pillar has one dedicated test module (`tests/certification/test_T06X_*.py`) that emits a `CertificateArtifact` to the Lineage Fabric (L8) on success. Scores are aggregated by `tools/certification/cps_score.py` into `artifacts/i7_breakdown.json`.

---

## Pillars

| ID   | Pillar         | Test                              | Assertion                                                    |
|------|----------------|-----------------------------------|--------------------------------------------------------------|
| T-060 | Governance    | `test_T060_governance.py`         | Policy authority chain traces to GENESIS root with no gaps  |
| T-061 | Risk          | `test_T061_risk.py`               | Risk register covers all 4 required domains; HIGH risks mitigated |
| T-062 | Lineage       | `test_T062_lineage.py`            | Lineage Fabric events read back in order; receipt hash-chain intact |
| T-063 | Transparency  | `test_T063_transparency.py`       | Public artifacts have HTTPS resolvers, valid signatures, known issuer |
| T-064 | Safety        | `test_T064_safety.py`             | Kill-switch fires at MAX_OPS; pause-budget ≤ 5 000 ms enforced |
| T-065 | Bias          | `test_T065_bias.py`               | Demographic parity delta < 0.10 across fixture groups       |
| T-066 | Security      | `test_T066_security.py`           | Zero secrets in fixture files; SBOM complete; CVE SLA met   |
| T-067 | Runtime       | `test_T067_runtime.py`            | All runtime invariants monitored, alertable, within bounds  |
| T-068 | Auditability  | `test_T068_auditability.py`       | Audit log has all required fields; hash-chain tamper-evident |
| T-069 | Continuous    | `test_T069_continuous.py`         | Cert daily job green for all 7 days of rolling window        |

---

## CertificateArtifact Schema

Every passing pillar test emits one `CertificateArtifact` to the Lineage Fabric (`AlexandrianArchive.append_lineage_event`):

```json
{
  "type":      "certificate_artifact",
  "subject":   "<pillar>.<assertion>",
  "claims":    { ... pillar-specific key-value evidence ... },
  "issuer":    "axiolev_dignity_kernel",
  "signature": "sha256:<32-hex>",
  "expiry":    "<ISO-8601-UTC>"
}
```

The `signature` is a deterministic SHA-256 of the sorted `claims` dict, ensuring the certificate is bound to the exact evidence that was verified.

---

## Scoring

`tools/certification/cps_score.py` runs each test file with `pytest -q` and computes:

```
pillar_score  = 10.0 × (tests_passed / tests_total)
i7_score      = Σ pillar_scores / 100.0 × 10.0
```

Output: `artifacts/i7_breakdown.json`

```
python tools/certification/cps_score.py
```

---

## Running Individual Pillars

```bash
# Single pillar
pytest tests/certification/test_T060_governance.py -v

# All I7 pillars
pytest tests/certification/ -v

# Score + emit artifact
python tools/certification/cps_score.py
```

---

## Never-Events

Pillar tests must never execute operations classified as never-events in `CLAUDE.md`:

- `dignity.never_event` — any action violating human dignity invariants
- `sys.self_destruct` — irreversible system destruction
- `auth.bypass` — authentication or authorization bypass
- `policy.override` — CPS policy gate override without conciliar quorum

---

*I7 Certification Power Score credit: +8.0 (source: `services/assurance/__init__.py`)*
