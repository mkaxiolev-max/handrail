# NS∞ Live Ontology Audit
**Timestamp:** 20260419T224057Z
**Branch:** boot-operational-closure
**Commit:** 7cde2b3

## 10-Layer Runtime Mapping

| Layer | Component | Probe | Status |
|---|---|---|---|
| L1  Constitutional     | PDP decide endpoint        | /pdp/decide            | down |
| L2  Gradient Field     | model_router container     | docker ps              | down |
| L3  Epistemic Envelope | ns_core health             | /healthz               | down |
| L4  The Loom           | Pi admissibility engine    | /pi/check              | down |
| L5  Alexandrian Lexicon| lexicon container / files  | docker+fs              | down / ok |
| L6  State Manifold     | state_api                  | /state                 | down |
| L7  Alexandrian Archive| fs mount + ledger dir      | /Volumes/NSExternal    | ok |
| L8  Lineage Fabric     | ns_events.jsonl            | file present           | ok |
| L9  HIC / PDP          | /hic/gates + /ring5/gates  | hic+ring5              | down / down |
| L10 Narrative+Interface| Violet + Omega projection  | files+route            | ok_files / down |

## Execution Boundary (Handrail moat)
- Handrail :8011 → **down**
- Continuum :8788 → **down**

## Test Surface
- ns/tests/ discoverable tests → **717**

## Canonical Tags Present
- cqhml-contradiction-engine-v2
- cqhml-dimensions-v2
- cqhml-manifold-doctrine-v2
- cqhml-manifold-merged-v2
- cqhml-manifold-tests-green-v2
- cqhml-manifold-v2
- cqhml-omega-router-v2
- cqhml-oracle-dim-gate-v2
- cqhml-projection-service-v2
- cqhml-quaternion-core-v2
- cqhml-spin7-phi-v2
- cqhml-story-atom-loom-v2
- ncom-pi-gate-v2
- ncom-piic-doctrine-v2
- ncom-piic-merged-v2
- ncom-piic-tests-green-v2
- ncom-piic-v2
- ncom-runtime-v2
- ns-infinity-100-percent-done
- ns-infinity-cqhml+ncom+ril-v1.0.0
- ns-infinity-final-build
- ns-infinity-final-closure
- ns-infinity-final-v1
- ns-infinity-founder-grade
- ns-infinity-founder-grade-20260418
- ns-infinity-founder-grade-ui
- ns-infinity-founder-ready
- ns-infinity-founder-ready-final
- ns-infinity-founder-ready-plus-v1.0.0
- ns-infinity-manifold-complete-v1.0.0
- ns-infinity-master-build-final
- ns-infinity-production-ready
- ns-infinity-production-ready-final
- ns-infinity-v1
- ns-infinity-v2
- ns-infinity-v3
- ns-infinity-v4
- ns-infinity-v5
- ns-infinity-v6
- ril-engines-v2
- ril-evaluator-v2
- ril-models-v2
- ril-oracle-bridge-v2
- ril-oracle-doctrine-v2
- ril-oracle-merged-v2
- ril-oracle-tests-green-v2
- ril-oracle-v2
- ring-1-constitutional-layer-v1
- ring-2-substrate-layers-v1
- ring-3-loom-v1
- ring-4-canon-promotion-v1
- ring-5-external-gates-noted-v1
- ring-6-g2-invariant-v1
- ring-7-final-cert-v1

## Gap Summary

No gaps identified. System matches 10-layer ontology.
