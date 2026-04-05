#!/usr/bin/env python3
"""
Gnoseogenic Lexicon Seeder — NS∞ v1
Seeds 30 P1 lexicon entries across 5 tiers into Alexandria.
POST to /alexandria/add or fallback to JSONL file.
"""
import json
import os
import sys
import hashlib
import requests
from datetime import datetime, timezone

NS_URL = os.environ.get("NS_URL", "http://localhost:9000")
FALLBACK_PATH = os.environ.get(
    "LEXICON_SEED_PATH",
    "/Volumes/NSExternal/.run/lexicon_seeds.jsonl"
)

# 30 P1 Gnoseogenic entries — 6 per tier
LEXICON: list[dict] = [
    # ── Tier 1 — gradient_source ──────────────────────────────────────────
    {
        "entry_id": "LEX-T1A00001",
        "word": "gnosis",
        "tier": 1,
        "pie_root": "*gno-",
        "semitic": "yd (ידע)",
        "cognitive_act": "direct knowing without inference",
        "engine_component": "gradient_source",
        "failure_mode": "epistemic collapse — system acts without verified knowledge",
        "priority": "P1",
        "ns_mapping": {"service": "ns", "module": "lexicon_substrate", "cps_op": None},
    },
    {
        "entry_id": "LEX-T1A00002",
        "word": "arche",
        "tier": 1,
        "pie_root": "*h2er-",
        "semitic": "r'sh (ראש)",
        "cognitive_act": "primordial origination point",
        "engine_component": "gradient_source",
        "failure_mode": "rootless execution — ops run with no originating intent",
        "priority": "P1",
        "ns_mapping": {"service": "ns", "module": "core.receipts", "cps_op": None},
    },
    {
        "entry_id": "LEX-T1A00003",
        "word": "logos",
        "tier": 1,
        "pie_root": "*leg-",
        "semitic": "dbr (דבר)",
        "cognitive_act": "structured reason / generative word",
        "engine_component": "gradient_source",
        "failure_mode": "semantic noise — outputs carry no causal chain",
        "priority": "P1",
        "ns_mapping": {"service": "ns", "module": "models.registry", "cps_op": None},
    },
    {
        "entry_id": "LEX-T1A00004",
        "word": "telos",
        "tier": 1,
        "pie_root": "*kwel-",
        "semitic": "qtz (קצ)",
        "cognitive_act": "end-directed purpose binding",
        "engine_component": "gradient_source",
        "failure_mode": "purpose drift — system optimizes for proximate not terminal goal",
        "priority": "P1",
        "ns_mapping": {"service": "ns", "module": "capability.graph", "cps_op": "ns.capability_graph"},
    },
    {
        "entry_id": "LEX-T1A00005",
        "word": "axiom",
        "tier": 1,
        "pie_root": "*ag-",
        "semitic": "qbl (קבל)",
        "cognitive_act": "unproven foundational assertion",
        "engine_component": "gradient_source",
        "failure_mode": "axiom drift — constitutional never-events eroded silently",
        "priority": "P1",
        "ns_mapping": {"service": "handrail", "module": "kernel.dignity_kernel", "cps_op": None},
    },
    {
        "entry_id": "LEX-T1A00006",
        "word": "nomos",
        "tier": 1,
        "pie_root": "*nem-",
        "semitic": "chq (חוק)",
        "cognitive_act": "law as distributed ordering principle",
        "engine_component": "gradient_source",
        "failure_mode": "policy void — execution proceeds unconstrained",
        "priority": "P1",
        "ns_mapping": {"service": "handrail", "module": "cps_engine", "cps_op": None},
    },

    # ── Tier 2 — intake ───────────────────────────────────────────────────
    {
        "entry_id": "LEX-T2A00001",
        "word": "aisthesis",
        "tier": 2,
        "pie_root": "*h2ew-",
        "semitic": "shm' (שמע)",
        "cognitive_act": "raw sensory perception before categorization",
        "engine_component": "intake",
        "failure_mode": "perceptual dropout — inputs arrive but are not registered",
        "priority": "P1",
        "ns_mapping": {"service": "ns", "module": "api.server", "cps_op": None},
    },
    {
        "entry_id": "LEX-T2A00002",
        "word": "krinein",
        "tier": 2,
        "pie_root": "*krei-",
        "semitic": "bch-n (בחן)",
        "cognitive_act": "discriminative separation / sorting",
        "engine_component": "intake",
        "failure_mode": "intake flooding — all inputs treated as equal weight",
        "priority": "P1",
        "ns_mapping": {"service": "handrail", "module": "cps_engine", "cps_op": None},
    },
    {
        "entry_id": "LEX-T2A00003",
        "word": "schema",
        "tier": 2,
        "pie_root": "*segh-",
        "semitic": "tzwr (צור)",
        "cognitive_act": "structural template that shapes perception",
        "engine_component": "intake",
        "failure_mode": "schema mismatch — payload rejected at ABI boundary",
        "priority": "P1",
        "ns_mapping": {"service": "handrail", "module": "abi.validators", "cps_op": None},
    },
    {
        "entry_id": "LEX-T2A00004",
        "word": "hyle",
        "tier": 2,
        "pie_root": "*h2ulH-",
        "semitic": "chm-r (חומר)",
        "cognitive_act": "undifferentiated raw material awaiting form",
        "engine_component": "intake",
        "failure_mode": "untyped payload — raw data enters execution without ABI wrapping",
        "priority": "P1",
        "ns_mapping": {"service": "handrail", "module": "server", "cps_op": None},
    },
    {
        "entry_id": "LEX-T2A00005",
        "word": "mneme",
        "tier": 2,
        "pie_root": "*men-",
        "semitic": "zkr (זכר)",
        "cognitive_act": "active recall from persistent store",
        "engine_component": "intake",
        "failure_mode": "memory blindness — context window starts cold every session",
        "priority": "P1",
        "ns_mapping": {"service": "ns", "module": "core.memory", "cps_op": "ns.memory_recent"},
    },
    {
        "entry_id": "LEX-T2A00006",
        "word": "kairos",
        "tier": 2,
        "pie_root": "*ker-",
        "semitic": "et (עת)",
        "cognitive_act": "opportune moment — qualitative time vs chronos",
        "engine_component": "intake",
        "failure_mode": "temporal blindness — proactive intel fires at wrong moment",
        "priority": "P1",
        "ns_mapping": {"service": "ns", "module": "intel", "cps_op": "ns.proactive_intel"},
    },

    # ── Tier 3 — conversion ───────────────────────────────────────────────
    {
        "entry_id": "LEX-T3A00001",
        "word": "poiesis",
        "tier": 3,
        "pie_root": "*kwei-",
        "semitic": "bra (ברא)",
        "cognitive_act": "bringing into being from nothing / creative causation",
        "engine_component": "conversion",
        "failure_mode": "sterile execution — ops complete but produce no new state",
        "priority": "P1",
        "ns_mapping": {"service": "handrail", "module": "cps_engine", "cps_op": None},
    },
    {
        "entry_id": "LEX-T3A00002",
        "word": "praxis",
        "tier": 3,
        "pie_root": "*per-",
        "semitic": "ma'ase (מעשה)",
        "cognitive_act": "deliberate action that transforms the actor",
        "engine_component": "conversion",
        "failure_mode": "phantom ops — actions recorded but produce no causal effect",
        "priority": "P1",
        "ns_mapping": {"service": "handrail", "module": "cps_engine", "cps_op": None},
    },
    {
        "entry_id": "LEX-T3A00003",
        "word": "synthesis",
        "tier": 3,
        "pie_root": "*dhe-",
        "semitic": "chibur (חיבור)",
        "cognitive_act": "combining disparate elements into unified whole",
        "engine_component": "conversion",
        "failure_mode": "fragmented execution — multi-step CPS plans lose coherence mid-chain",
        "priority": "P1",
        "ns_mapping": {"service": "handrail", "module": "cps_engine", "cps_op": None},
    },
    {
        "entry_id": "LEX-T3A00004",
        "word": "methodos",
        "tier": 3,
        "pie_root": "*med-",
        "semitic": "derech (דרך)",
        "cognitive_act": "path-following — systematic pursuit toward goal",
        "engine_component": "conversion",
        "failure_mode": "path collapse — execution jumps steps, violates op ordering",
        "priority": "P1",
        "ns_mapping": {"service": "ns", "module": "programs", "cps_op": "program.advance_state"},
    },
    {
        "entry_id": "LEX-T3A00005",
        "word": "aletheia",
        "tier": 3,
        "pie_root": "*leh2-",
        "semitic": "emet (אמת)",
        "cognitive_act": "unconcealment — truth as revealing hidden reality",
        "engine_component": "conversion",
        "failure_mode": "opacity — system state concealed from Founder console",
        "priority": "P1",
        "ns_mapping": {"service": "ns", "module": "ui.founder", "cps_op": None},
    },
    {
        "entry_id": "LEX-T3A00006",
        "word": "kinesis",
        "tier": 3,
        "pie_root": "*kei-",
        "semitic": "tn-ua (תנועה)",
        "cognitive_act": "motion / state change as metaphysical category",
        "engine_component": "conversion",
        "failure_mode": "state freeze — TierLatch stuck, no events flowing to Continuum",
        "priority": "P1",
        "ns_mapping": {"service": "continuum", "module": "server", "cps_op": None},
    },

    # ── Tier 4 — output ───────────────────────────────────────────────────
    {
        "entry_id": "LEX-T4A00001",
        "word": "apodeixis",
        "tier": 4,
        "pie_root": "*deik-",
        "semitic": "hara'ah (הראיה)",
        "cognitive_act": "formal demonstration — showing what cannot be doubted",
        "engine_component": "output",
        "failure_mode": "proof gap — boot receipts exist but chain validation fails",
        "priority": "P1",
        "ns_mapping": {"service": "ns", "module": "core.receipts", "cps_op": None},
    },
    {
        "entry_id": "LEX-T4A00002",
        "word": "entelecheia",
        "tier": 4,
        "pie_root": "*kwel-",
        "semitic": "sh-le-mut (שלמות)",
        "cognitive_act": "actuality — potential fully realized",
        "engine_component": "output",
        "failure_mode": "partial completion — ops return without fully realized ReturnBlock",
        "priority": "P1",
        "ns_mapping": {"service": "handrail", "module": "cps_engine", "cps_op": None},
    },
    {
        "entry_id": "LEX-T4A00003",
        "word": "eidos",
        "tier": 4,
        "pie_root": "*weid-",
        "semitic": "tzelem (צלם)",
        "cognitive_act": "form / essence visible to intellect",
        "engine_component": "output",
        "failure_mode": "formless output — ReturnBlock lacks typed structure",
        "priority": "P1",
        "ns_mapping": {"service": "handrail", "module": "abi.validators", "cps_op": None},
    },
    {
        "entry_id": "LEX-T4A00004",
        "word": "ergon",
        "tier": 4,
        "pie_root": "*werg-",
        "semitic": "ml-a-cha (מלאכה)",
        "cognitive_act": "function / characteristic work of a thing",
        "engine_component": "output",
        "failure_mode": "off-function — adapter op returns data outside its declared domain",
        "priority": "P1",
        "ns_mapping": {"service": "handrail-adapter-macos", "module": "adapter_core.capability_registry", "cps_op": None},
    },
    {
        "entry_id": "LEX-T4A00005",
        "word": "apophasis",
        "tier": 4,
        "pie_root": "*bha-",
        "semitic": "shlilah (שלילה)",
        "cognitive_act": "negative definition — knowing by exclusion",
        "engine_component": "output",
        "failure_mode": "boundary blindness — system cannot articulate what it will not do",
        "priority": "P1",
        "ns_mapping": {"service": "handrail", "module": "kernel.dignity_kernel", "cps_op": None},
    },
    {
        "entry_id": "LEX-T4A00006",
        "word": "mimesis",
        "tier": 4,
        "pie_root": "*mei-",
        "semitic": "chikui (חיקוי)",
        "cognitive_act": "representation / faithful reproduction of pattern",
        "engine_component": "output",
        "failure_mode": "drift from canon — semantic outputs diverge from Lexicon definitions",
        "priority": "P1",
        "ns_mapping": {"service": "ns", "module": "semantic.feedback_binder", "cps_op": None},
    },

    # ── Tier 5 — meta_constraint ──────────────────────────────────────────
    {
        "entry_id": "LEX-T5A00001",
        "word": "dikaiosyne",
        "tier": 5,
        "pie_root": "*deik-",
        "semitic": "tzedek (צדק)",
        "cognitive_act": "justice as structural ordering of parts to whole",
        "engine_component": "meta_constraint",
        "failure_mode": "constitutional violation — dignity kernel bypassed",
        "priority": "P1",
        "ns_mapping": {"service": "handrail", "module": "kernel.dignity_kernel", "cps_op": None},
    },
    {
        "entry_id": "LEX-T5A00002",
        "word": "sophrosyne",
        "tier": 5,
        "pie_root": "*swe-",
        "semitic": "anava (ענוה)",
        "cognitive_act": "temperance — self-limiting within proper measure",
        "engine_component": "meta_constraint",
        "failure_mode": "scope creep — ops execute beyond their declared risk tier",
        "priority": "P1",
        "ns_mapping": {"service": "handrail", "module": "cps_engine", "cps_op": None},
    },
    {
        "entry_id": "LEX-T5A00003",
        "word": "phronesis",
        "tier": 5,
        "pie_root": "*ghren-",
        "semitic": "da'at (דעת)",
        "cognitive_act": "practical wisdom — right action in contingent situation",
        "engine_component": "meta_constraint",
        "failure_mode": "rigid rule following — system applies policy without contextual judgment",
        "priority": "P1",
        "ns_mapping": {"service": "ns", "module": "models.router", "cps_op": None},
    },
    {
        "entry_id": "LEX-T5A00004",
        "word": "autonomia",
        "tier": 5,
        "pie_root": "*autos + *nem-",
        "semitic": "cheirut (חירות)",
        "cognitive_act": "self-governance under self-given law",
        "engine_component": "meta_constraint",
        "failure_mode": "hetero-determination — system accepts external command without YubiKey gate",
        "priority": "P1",
        "ns_mapping": {"service": "ns", "module": "kernel.dignity", "cps_op": "POST /kernel/yubikey/verify"},
    },
    {
        "entry_id": "LEX-T5A00005",
        "word": "harmonia",
        "tier": 5,
        "pie_root": "*ar-",
        "semitic": "shivuy (שיוי)",
        "cognitive_act": "fitting-together — consonance of heterogeneous parts",
        "engine_component": "meta_constraint",
        "failure_mode": "inter-service divergence — Handrail/NS/Continuum state desync",
        "priority": "P1",
        "ns_mapping": {"service": "ns", "module": "api.server", "cps_op": "GET /health/full"},
    },
    {
        "entry_id": "LEX-T5A00006",
        "word": "kathekon",
        "tier": 5,
        "pie_root": "*kat-",
        "semitic": "chov (חוב)",
        "cognitive_act": "appropriate action — what befits the nature of the agent",
        "engine_component": "meta_constraint",
        "failure_mode": "role confusion — model speaks with authority it does not hold",
        "priority": "P1",
        "ns_mapping": {"service": "ns", "module": "models.registry", "cps_op": None},
    },
]


def _entry_with_ts(entry: dict) -> dict:
    e = dict(entry)
    e["timestamp"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return e


def _seed_via_api(entries: list[dict]) -> tuple[int, int]:
    ok = 0
    fail = 0
    for entry in entries:
        try:
            r = requests.post(
                f"{NS_URL}/alexandria/add",
                json={"type": "lexicon_entry", "data": entry},
                timeout=5,
            )
            if r.status_code in (200, 201):
                ok += 1
            else:
                print(f"  WARN {entry['entry_id']}: HTTP {r.status_code}", file=sys.stderr)
                fail += 1
        except Exception as exc:
            print(f"  WARN {entry['entry_id']}: {exc}", file=sys.stderr)
            fail += 1
    return ok, fail


def _seed_via_fallback(entries: list[dict]) -> None:
    os.makedirs(os.path.dirname(FALLBACK_PATH), exist_ok=True)
    with open(FALLBACK_PATH, "w") as fh:
        for entry in entries:
            fh.write(json.dumps(entry) + "\n")
    print(f"  Wrote {len(entries)} entries → {FALLBACK_PATH}")


def main() -> None:
    entries = [_entry_with_ts(e) for e in LEXICON]
    print(f"NS∞ Lexicon Seeder — {len(entries)} P1 entries across 5 tiers")
    print(f"  Target: {NS_URL}/alexandria/add")

    # Attempt API seed
    ok, fail = _seed_via_api(entries)
    print(f"  API seed: {ok} ok, {fail} failed")

    if fail > 0 or ok == 0:
        print("  Falling back to JSONL...")
        _seed_via_fallback(entries)

    # Print manifest
    fingerprint = hashlib.sha256(
        json.dumps([e["entry_id"] for e in entries], sort_keys=True).encode()
    ).hexdigest()[:16]
    print(f"\nLexicon manifest:")
    print(f"  entries:     {len(entries)}")
    print(f"  tiers:       1-5 (6 entries each)")
    print(f"  fingerprint: {fingerprint}")
    print(f"  schema:      abi/schemas/LexiconEntry.v1.json")

    by_component: dict[str, int] = {}
    for e in entries:
        c = e["engine_component"]
        by_component[c] = by_component.get(c, 0) + 1
    print("  by component:")
    for comp, count in sorted(by_component.items()):
        print(f"    {comp}: {count}")


if __name__ == "__main__":
    main()
