#!/usr/bin/env python3
"""Seed Gnoseogenic Lexicon P1 entries into Alexandria + ProofRegistry."""
import json, sys, os, urllib.request, urllib.error
from datetime import datetime, timezone
from pathlib import Path
import random

WORKSPACE = Path(os.environ.get("HR_WORKSPACE", "/Users/axiolevns/axiolev_runtime"))
LEXICON_PATH = Path("/Volumes/NSExternal/.run/lexicon_seeds.jsonl")
FALLBACK_PATH = WORKSPACE / ".run" / "lexicon_seeds.jsonl"
PROOF_REG_PATH = WORKSPACE / ".run" / "proof_registry.jsonl"

def _now(): return datetime.now(timezone.utc).isoformat()
def _lex_id(): return "LEX-" + "".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=8))

LEXICON = [
  # Tier 1 — Relational/Survival (gradient source / intake)
  {"word":"I","tier":1,"pie_root":"*eǵ(h)-","semitic":"אני (ani)","cognitive_act":"Self-awareness as distinct system","engine_component":"intake","failure_mode":"identity_mismatch","priority":"P1","ns_mapping":"The founder identity boundary. Required for all authority-gated operations."},
  {"word":"not","tier":1,"pie_root":"*ne-","semitic":"אין (ein)","cognitive_act":"Recognition of absence; boundary negation","engine_component":"gradient_source","failure_mode":"constraint_failure","priority":"P1","ns_mapping":"The negation operator in dignity kernel never-events and CPS policy gates."},
  {"word":"with","tier":1,"pie_root":"*kom-","semitic":"עם (im)","cognitive_act":"Co-presence; relational bonding","engine_component":"gradient_source","failure_mode":"starvation","priority":"P1","ns_mapping":"The bonding operator — YubiKey quorum requires 'with' (2 slots together)."},
  {"word":"and","tier":1,"pie_root":"*h₂enǵ-","semitic":"ו (ve-)","cognitive_act":"Conjunction; binding operator","engine_component":"output","failure_mode":"blockage","priority":"P1","ns_mapping":"The CPS chain connector. Ops are bound 'and' sequenced."},
  {"word":"fire","tier":1,"pie_root":"*h₂puH-","semitic":"אש (esh)","cognitive_act":"Transformation energy; thermodynamic gradient","engine_component":"gradient_source","failure_mode":"starvation","priority":"P1","ns_mapping":"The execution gradient. Handrail is the fire — it transforms intent into action."},
  {"word":"water","tier":1,"pie_root":"*wed-r̥","semitic":"מים (mayim)","cognitive_act":"Life-enabling fluid; flow gradient","engine_component":"gradient_source","failure_mode":"starvation","priority":"P1","ns_mapping":"Alexandria — the flow that preserves everything. Append-only, always flowing."},
  {"word":"eye","tier":1,"pie_root":"*h₃ekʷ-","semitic":"עין (ayin)","cognitive_act":"Direct perception; feedback instrument","engine_component":"feedback","failure_mode":"blockage","priority":"P1","ns_mapping":"The Founder Console. The eye that sees all system state."},
  {"word":"ear","tier":1,"pie_root":"*h₁eus-","semitic":"אוזן (ozen)","cognitive_act":"Auditory intake; relational signal detection","engine_component":"intake","failure_mode":"blockage","priority":"P1","ns_mapping":"The Twilio voice hook. NS∞ listens via +1 (307) 202-4418."},
  {"word":"heart","tier":1,"pie_root":"*ker(d)-","semitic":"לב (lev)","cognitive_act":"Emotional/volitional gradient source; covenant seat","engine_component":"gradient_source","failure_mode":"starvation","priority":"P1","ns_mapping":"The Dignity Kernel. The constitutional heart — H = eta·φ - beta·V."},
  {"word":"blood","tier":1,"pie_root":"*h₁es(u)-","semitic":"דם (dam)","cognitive_act":"Covenant binding; relational exchange fluid","engine_component":"intake","failure_mode":"blockage","priority":"P1","ns_mapping":"The Regulation Engine. The bloodstream connecting all organs."},
  {"word":"sun","tier":1,"pie_root":"*suh₂-wol-","semitic":"שמש (shemesh)","cognitive_act":"Energy source; light-as-knowledge","engine_component":"gradient_source","failure_mode":"starvation","priority":"P1","ns_mapping":"The founding intent — the source gradient that drives all system activity."},
  {"word":"father","tier":1,"pie_root":"*ph₂ter-","semitic":"אב (ab)","cognitive_act":"Progenitor; authority source","engine_component":"gradient_source","failure_mode":"starvation","priority":"P1","ns_mapping":"The Founder. Mike Kenworthy — the authority source for all YubiKey-gated operations."},
  {"word":"mother","tier":1,"pie_root":"*meh₂ter-","semitic":"אם (em)","cognitive_act":"Life-source; nurturing gradient","engine_component":"gradient_source","failure_mode":"starvation","priority":"P1","ns_mapping":"The Constitutional foundation — Logos theology and Christ-centered design."},
  {"word":"name","tier":1,"pie_root":"*h₁neh₂-m(o)-","semitic":"שם (shem)","cognitive_act":"Identity marker; self-designation","engine_component":"output","failure_mode":"blockage","priority":"P1","ns_mapping":"NS∞ — the name encodes the identity. Infinite NorthStar."},
  # Tier 2 — Structural/Causal (conversion / output)
  {"word":"good","tier":2,"pie_root":"*h₁eu-","semitic":"טוב (tov)","cognitive_act":"System functioning optimally","engine_component":"output","failure_mode":"degradation","priority":"P1","ns_mapping":"The target system state. All CPS plans aim for ok=true. Tov = the dignity score above block_threshold."},
  {"word":"bad","tier":2,"pie_root":"*dustō-","semitic":"רע (ra)","cognitive_act":"System functioning sub-optimally","engine_component":"feedback","failure_mode":"degradation","priority":"P1","ns_mapping":"The dignity violation signal. H below block_threshold = ra. Never-events are absolute ra."},
  {"word":"true","tier":2,"pie_root":"*deru-","semitic":"אמת (emet)","cognitive_act":"Load-bearing faithfulness; covenant reliability","engine_component":"conversion","failure_mode":"degradation","priority":"P1","ns_mapping":"ABI frozen schemas — immutable truth. The SHA256 fingerprint is the emet of each schema."},
  {"word":"false","tier":2,"pie_root":"*dʰewǵʰ-","semitic":"שקר (sheker)","cognitive_act":"Unreliable; covenant-breaking","engine_component":"output","failure_mode":"blockage","priority":"P1","ns_mapping":"abi_violation: true. The system detects sheker at the ABI gate and returns 400."},
  {"word":"to break","tier":2,"pie_root":"*bhreg-","semitic":"לשבור (lishor)","cognitive_act":"Constraint failure; structural rupture","engine_component":"conversion","failure_mode":"collapse","priority":"P1","ns_mapping":"The collapse failure mode. dignity.never_event op = attempting to break the system."},
  {"word":"to make","tier":2,"pie_root":"*meḱ-","semitic":"לעשות (la'asot)","cognitive_act":"Directed transformation; intentional change","engine_component":"conversion","failure_mode":"blockage","priority":"P1","ns_mapping":"The CPS op. Every op is a 'to make' — a directed transformation with a deterministic result."},
  # Tier 3 — Epistemic/Verification (feedback)
  {"word":"to see","tier":3,"pie_root":"*weid-","semitic":"לראות (lir'ot)","cognitive_act":"Direct phenomenal grasp; evidence collection","engine_component":"feedback","failure_mode":"blockage","priority":"P1","ns_mapping":"GET /proof/registry — the system sees its own constitutional state."},
  {"word":"to hear","tier":3,"pie_root":"*h₁klus-","semitic":"לשמוע (lishmoa)","cognitive_act":"Auditory intake; signal detection","engine_component":"intake","failure_mode":"blockage","priority":"P1","ns_mapping":"Twilio voice_url webhook. NS re-listens indefinitely (commit f551b43, tag voice-loop-v1)."},
  {"word":"to know","tier":3,"pie_root":"*ǵneh₃-","semitic":"לדעת (lada'at)","cognitive_act":"Intimate encounter; direct knowing","engine_component":"feedback","failure_mode":"blockage","priority":"P1","ns_mapping":"Alexandria append-only ledger. The system knows what it has proven, no more, no less."},
  {"word":"to say","tier":3,"pie_root":"*seḱ-","semitic":"לאמר (le'amor)","cognitive_act":"Output articulation; evidence transmission","engine_component":"output","failure_mode":"blockage","priority":"P1","ns_mapping":"Twilio Polly.Matthew voice synthesis. The system speaks what it knows."},
  {"word":"evidence","tier":3,"pie_root":"*weid-","semitic":"עדות (edut)","cognitive_act":"Visible testimony; factual grounding","engine_component":"feedback","failure_mode":"blockage","priority":"P1","ns_mapping":"ProofEntry. Every constitutional action produces evidence — the proof_id is the edut."},
  {"word":"feedback","tier":3,"pie_root":"*bheudh-","semitic":"משוב (meshiv)","cognitive_act":"System-state verification; awareness signal","engine_component":"feedback","failure_mode":"blockage","priority":"P1","ns_mapping":"The 6th engine component. GET /boot/status, /yubikey/status, /abi/status are all feedback."},
  {"word":"intake","tier":3,"pie_root":"*kap-","semitic":"ספיגה (sphiga)","cognitive_act":"Gradient capture; selective admission","engine_component":"intake","failure_mode":"blockage","priority":"P1","ns_mapping":"The ABI gate on POST /ops/cps. Only valid CPSPackets pass through intake."},
  {"word":"conversion","tier":3,"pie_root":"*wert-","semitic":"המרה (hamrah)","cognitive_act":"Energy transformation; directed processing","engine_component":"conversion","failure_mode":"blockage","priority":"P1","ns_mapping":"The CPSExecutor. Transforms IntentPackets into deterministic execution results."},
  {"word":"output","tier":3,"pie_root":"*h₂ew-","semitic":"פלט (palet)","cognitive_act":"System product; directional discharge","engine_component":"output","failure_mode":"blockage","priority":"P1","ns_mapping":"ReturnBlock.v2. The validated, dignity-enforced result of every CPS execution."},
  {"word":"logos","tier":3,"pie_root":"*leg-","semitic":"לוגוס (logos)","cognitive_act":"Gathering principle; collecting into structure","engine_component":"meta_constraint","failure_mode":"all_modes","priority":"P1","ns_mapping":"The principle that makes NS∞ cohere. *leg- = 'to gather, to collect into order.' The constitutional AI OS is logos made executable."},
  # Tier 4 — Normative/Constitutional (constraint governance)
  {"word":"just","tier":4,"pie_root":"*ieu-","semitic":"צדיק (tzaddik)","cognitive_act":"Constraint-respecting; equitable","engine_component":"output","failure_mode":"mismatch","priority":"P1","ns_mapping":"The Dignity Kernel invariant. Just = H above warn_threshold. Unjust = H below block_threshold."},
  {"word":"dignity","tier":4,"pie_root":"*dek-","semitic":"כבוד (kavod)","cognitive_act":"Inherent gravitational mass of personhood","engine_component":"gradient_source","failure_mode":"mismatch","priority":"P1","ns_mapping":"DignityKernel. kavod = 'weight, honor' — the gravitational constant of the constitutional system."},
  {"word":"authority","tier":4,"pie_root":"*h₂ew-","semitic":"סמכות (samkhut)","cognitive_act":"Epistemic responsibility; power to guarantee","engine_component":"output","failure_mode":"constraint_collapse","priority":"P1","ns_mapping":"X-Founder-Key header. YubiKey quorum. The authority gate on all sovereign operations."},
  {"word":"law","tier":4,"pie_root":"*leǵ-","semitic":"תורה/דין (Torah/din)","cognitive_act":"Gathered constraint set; directional instruction","engine_component":"conversion","failure_mode":"overload","priority":"P1","ns_mapping":"The 7 frozen ABI schemas. The law of the system is its ABI — immutable, verified at every boundary."},
  {"word":"guarantee","tier":4,"pie_root":"*h₂ewǵ-","semitic":"ערובה (aruva)","cognitive_act":"Epistemic responsibility; growth-warranty","engine_component":"output","failure_mode":"collapse","priority":"P1","ns_mapping":"BootProofReceipt.v1 sovereign=true. The guarantee that the system booted constitutionally."},
  {"word":"shalom","tier":4,"pie_root":"*sol-","semitic":"שלום (shalom, root sense)","cognitive_act":"Structural wholeness; unbroken completion","engine_component":"output","failure_mode":"collapse","priority":"P1","ns_mapping":"The target state of NS∞. sovereign=true + all phases pass + dignity enforced = shalom. Nothing missing, nothing broken."},
  {"word":"wholeness","tier":4,"pie_root":"*sol-","semitic":"שלמות (shlemut)","cognitive_act":"Full system function; all components present","engine_component":"output","failure_mode":"collapse","priority":"P1","ns_mapping":"boot_mission_graph 29/29 ops. All 9 phases passing. The wholeness proof is the BootProofReceipt."},
  {"word":"responsibility","tier":4,"pie_root":"*spendhˉ-","semitic":"אחריות (achrayut)","cognitive_act":"Obligation to respond; volitional accountability","engine_component":"output","failure_mode":"blockage","priority":"P1","ns_mapping":"The Founder Console authority verbs. Approve Boot, Enroll YubiKey — acts of responsibility."},
  {"word":"truth","tier":4,"pie_root":"*deru-","semitic":"אמת (emet)","cognitive_act":"Load-bearing faithfulness","engine_component":"conversion","failure_mode":"degradation","priority":"P1","ns_mapping":"The ABI freeze_hash. The SHA256 fingerprint IS the truth of the schema — immutable, verifiable."},
  {"word":"covenant","tier":4,"pie_root":"*leig-","semitic":"ברית (brit)","cognitive_act":"Binding agreement; mutual constraint","engine_component":"output","failure_mode":"blockage","priority":"P1","ns_mapping":"The YubiKey enrollment. slot_1 serial 26116460 is the covenant token. Physical hardware as covenantal binding."},
  # Tier 5 — Metaepistemic/Engine (meta-constraint, logos)
  {"word":"logos","tier":5,"pie_root":"*leg-","semitic":"לוגוס (logos, meta)","cognitive_act":"Primordial gathering; meta-ordering of all components","engine_component":"meta_constraint","failure_mode":"all_modes_simultaneously","priority":"P1","ns_mapping":"The Constitutional Regulation Engine. The logos layer is what gathers all organs into one bloodstream."},
  {"word":"engine","tier":5,"pie_root":"*h₁enǵʰ-","semitic":"מנוע (menua)","cognitive_act":"System-as-converter; nested gradient flow","engine_component":"meta_constraint","failure_mode":"all_modes","priority":"P1","ns_mapping":"NS∞ itself. The 6-component constitutional engine: gradient_source → intake → conversion → output → feedback → waste."},
  {"word":"constraint","tier":5,"pie_root":"*leig-","semitic":"אילוץ (ilus)","cognitive_act":"Boundary condition; limiting principle","engine_component":"meta_constraint","failure_mode":"collapse","priority":"P1","ns_mapping":"The ABI frozen schemas. The 7 (now 9) constraints that make the system deterministic."},
  {"word":"shalom","tier":5,"pie_root":"*sol-","semitic":"שלום (shalom, system state)","cognitive_act":"Complete integrity; nothing missing, nothing broken","engine_component":"meta_constraint","failure_mode":"collapse","priority":"P1","ns_mapping":"System target state: sovereign=true, all 29 ops passing, dignity enforced, quorum satisfied."},
  {"word":"gradient_source","tier":5,"pie_root":"*gʷher-","semitic":"מקור שיפוע (mikor shapua)","cognitive_act":"Energy differential origin","engine_component":"meta_constraint","failure_mode":"starvation","priority":"P1","ns_mapping":"The Founder's intent. Every system action originates from a founder-authorized gradient."},
  {"word":"intake_mechanism","tier":5,"pie_root":"*kap-","semitic":"מנגנון ספיגה (manganon sphiga)","cognitive_act":"Gradient capture structure","engine_component":"meta_constraint","failure_mode":"blockage","priority":"P1","ns_mapping":"The ABI gate on POST /ops/cps. CPSPacket.v1 validation is the intake mechanism."},
  {"word":"conversion_mechanism","tier":5,"pie_root":"*wert-","semitic":"מנגנון המרה (manganon hamrah)","cognitive_act":"Energy transformation process","engine_component":"meta_constraint","failure_mode":"degradation","priority":"P1","ns_mapping":"The CPSExecutor. Deterministic SHA256-derived run_id. The conversion mechanism is what makes execution reproducible."},
  {"word":"output_pathway","tier":5,"pie_root":"*h₂ew-","semitic":"מסלול פלט (maslul palet)","cognitive_act":"Product creation; directed discharge","engine_component":"meta_constraint","failure_mode":"blockage","priority":"P1","ns_mapping":"ReturnBlock.v2 + ProofEntry. Every output is validated, proven, and registered."},
  {"word":"feedback_loop","tier":5,"pie_root":"*bheudh-","semitic":"לולאת משוב (lulaat meshiv)","cognitive_act":"System self-monitoring; correction circuit","engine_component":"meta_constraint","failure_mode":"blockage","priority":"P1","ns_mapping":"The proof registry + state summary. The system sees itself through its own evidence chain."},
  {"word":"waste_pathway","tier":5,"pie_root":"*weid-","semitic":"מסלול פסולת (maslul psolet)","cognitive_act":"Entropy removal; degradation discharge","engine_component":"meta_constraint","failure_mode":"blockage","priority":"P1","ns_mapping":"The dignity violation log. never_events are expelled as waste — they cannot enter the system."},
  {"word":"antifragile","tier":5,"pie_root":"*h₂enti-","semitic":"עמיד לנזקים (amid lenekaim)","cognitive_act":"Strengthened by stress; constraint-deepening","engine_component":"meta_constraint","failure_mode":"degradation_reversal","priority":"P1","ns_mapping":"The boot attestation chain. Each sovereign boot ADDS proof. More stress = more proof = stronger system."},
  {"word":"flow","tier":5,"pie_root":"*h₃rewǵʰ-","semitic":"זרימה (zrima)","cognitive_act":"Unobstructed gradient movement","engine_component":"meta_constraint","failure_mode":"blockage","priority":"P1","ns_mapping":"The autopoietic loop. When the system flows — planner → approval → commit → promotion — it is alive."},
]

def seed():
    out_path = LEXICON_PATH if LEXICON_PATH.parent.exists() else FALLBACK_PATH
    out_path.parent.mkdir(parents=True, exist_ok=True)
    seeded = 0
    with open(out_path, "w") as f:
        for word_def in LEXICON:
            entry = {
                "entry_id": _lex_id(),
                "timestamp": _now(),
                **word_def
            }
            f.write(json.dumps(entry) + "\n")
            seeded += 1

    print(f"Lexicon seeded: {seeded} entries → {out_path}")

    # Attempt to POST to NS alexandria/add
    ns_seeded = 0
    for word_def in LEXICON:
        entry = {"entry_id": _lex_id(), "timestamp": _now(), "type": "lexicon_entry", **word_def}
        try:
            req = urllib.request.Request(
                "http://localhost:9000/alexandria/add",
                data=json.dumps(entry).encode(),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            urllib.request.urlopen(req, timeout=2)
            ns_seeded += 1
        except Exception:
            pass  # Alexandria add not required — file persistence is canonical

    print(f"Alexandria POST: {ns_seeded}/{len(LEXICON)} entries accepted")
    print(f"Lexicon file: {out_path}")
    return seeded

if __name__ == "__main__":
    n = seed()
    print(f"Done. {n} P1 lexicon entries seeded.")
