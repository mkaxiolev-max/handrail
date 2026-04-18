#!/usr/bin/env bash
# =============================================================================
# NS∞ BROKERAGE v1 — SIGNAL-AWARE BUILD + AUTO-MERGE
# AXIOLEV HOLDINGS LLC — DIGNITY PRESERVED
# Owner: Mike Kenworthy
# LLM contribution: Claude (Anthropic), draft under founder review. No legal claim.
# =============================================================================

set -eo pipefail

REPO="${REPO:-$HOME/axiolev_runtime}"
WT="${WT:-$HOME/axiolev_runtime_brokerage_wt}"
BRANCH="feature/brokerage-v1"
TARGET="boot-operational-closure"
TAG_BUILT="brokerage-v1-built"
TAG_MERGED="brokerage-v1-merged"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"

ALEX_OUT="/Volumes/NSExternal/ALEXANDRIA/state_checks"
ALEX_SIGNALS="/Volumes/NSExternal/ALEXANDRIA/signals"
LOCAL_SIGNALS="$REPO/.terminal_manager/signals"
PACKET_INBOX="$REPO/.terminal_manager/packets/inbox"
BUILD_LOG_DIR="$WT/.brokerage_build_logs"
RETURN_JSON="$PACKET_INBOX/02_brokerage_full.return.json"

SIGNAL_FILES=(
    "$LOCAL_SIGNALS/ring6_complete.signal"
    "$ALEX_SIGNALS/ring6_complete.signal"
)

SIGNAL_TIMEOUT_MIN="${SIGNAL_TIMEOUT_MIN:-240}"
SIGNAL_POLL_SEC="${SIGNAL_POLL_SEC:-15}"
AUTO_PUSH="${AUTO_PUSH:-false}"
DRY_RUN="${DRY_RUN:-false}"

DIGNITY='AXIOLEV HOLDINGS LLC — DIGNITY PRESERVED'

log()  { printf '[%s] %s\n' "$(date -u +%H:%M:%SZ)" "$*"; }
hdr()  { printf '\n─── %s ' "$*"; printf '%0.s─' $(seq 1 $((70 - ${#*}))); printf '\n'; }
die()  { log "FAIL: $*"; exit 1; }

echo "═════════════════════════════════════════════════════════════════════════"
echo " NS∞ BROKERAGE v1 — BUILD + SIGNAL-TRIGGERED AUTO-MERGE"
echo "═════════════════════════════════════════════════════════════════════════"
log "Repo:               $REPO"
log "Worktree:           $WT"
log "Source → Target:    $BRANCH → $TARGET"
log "Signal files:       ${SIGNAL_FILES[*]}"
log "Signal timeout:     ${SIGNAL_TIMEOUT_MIN} min (0=forever)"
log "Auto-push on merge: $AUTO_PUSH"
log "Dry run:            $DRY_RUN"
echo "═════════════════════════════════════════════════════════════════════════"

hdr "§0 · Pre-flight"

[ -d "$REPO/.git" ] || die "$REPO not a git repo"
cd "$REPO"

CURRENT_BRANCH="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo '?')"
BASE_SHA="$(git rev-parse HEAD)"
log "Main repo branch: $CURRENT_BRANCH @ $BASE_SHA"
if [ "$CURRENT_BRANCH" != "$TARGET" ]; then
    log "WARN: main not on $TARGET — worktree isolation keeps us safe, continuing"
fi

for lock in .git/index.lock .git/HEAD.lock .git/MERGE_HEAD .git/rebase-merge .git/rebase-apply; do
    [ -e "$REPO/$lock" ] && die "repo lock present ($lock) — terminal-1 mid-op, retry in a moment"
done

for p in runtime/program_engine.py programs/program_library_v1.json policies dignity_kernel; do
    [ -e "$p" ] || die "required core artifact missing: $p"
done
log "✓ core artifacts present"

mkdir -p "$LOCAL_SIGNALS"
mkdir -p "$PACKET_INBOX"
[ -d "$ALEX_OUT" ] && mkdir -p "$ALEX_SIGNALS" 2>/dev/null || true
log "✓ signal + inbox directories ready"

if [ -e "$WT" ]; then
    [ -e "$WT/.git" ] || die "$WT exists but not a worktree"
    WT_FRESH=0
    log "Worktree exists — reusing"
else
    WT_FRESH=1
    log "Worktree will be created"
fi

if git rev-parse --verify "$BRANCH" >/dev/null 2>&1; then
    BRANCH_EXISTS=1
else
    BRANCH_EXISTS=0
fi

hdr "§1 · Worktree creation"

if [ "$WT_FRESH" = "1" ]; then
    if [ "$BRANCH_EXISTS" = "0" ]; then
        git worktree add -b "$BRANCH" "$WT" "$BASE_SHA"
    else
        git worktree add "$WT" "$BRANCH"
    fi
    log "✓ worktree added"
else
    ( cd "$WT" && (git checkout "$BRANCH" 2>/dev/null || git checkout -b "$BRANCH" "$BASE_SHA") )
    log "✓ worktree on branch $BRANCH"
fi

cd "$WT"
log "pwd:    $(pwd)"
log "branch: $(git rev-parse --abbrev-ref HEAD)"
log "HEAD:   $(git rev-parse HEAD)"

mkdir -p "$BUILD_LOG_DIR"

hdr "§2 · Scaffold"
mkdir -p programs/brokerage/missions programs/brokerage/roles
mkdir -p policies/jurisdictions/ca policies/jurisdictions/wa
mkdir -p adapters/brokerage runtime/jurisdiction ops/compliance tests/brokerage
log "✓ directories scaffolded"

hdr "§3 · JurisdictionBundle loader"

cat > runtime/jurisdiction/__init__.py << 'PYEOF'
# AXIOLEV HOLDINGS LLC — DIGNITY PRESERVED
# Owner: Mike Kenworthy | LLM contribution: Claude, no legal claim
from .loader import JurisdictionBundle, load_jurisdiction, list_available
__all__ = ["JurisdictionBundle", "load_jurisdiction", "list_available"]
PYEOF

cat > runtime/jurisdiction/loader.py << 'PYEOF'
"""
AXIOLEV NS∞ — JurisdictionBundle

Adds a jurisdiction-layered policy to the existing PolicyBundle pattern.
Additive only: can tighten, never loosen, the gates established above it.

Precedence:  DK > Canon > PolicyBundle > JurisdictionBundle > RoleBinding
Owner:       AXIOLEV Holdings LLC. No LLM legal claim.
"""
import json
from pathlib import Path

JURISDICTION_ROOT = Path("policies/jurisdictions")


class JurisdictionBundle:
    def __init__(self, jurisdiction, vertical, spec):
        self.jurisdiction = jurisdiction
        self.vertical = vertical
        self.spec = spec

    @property
    def gates(self):
        return self.spec.get("rules", {}) or self.spec.get("gates", {})

    @property
    def forbidden_actions(self):
        return self.spec.get("forbidden_actions", [])

    @property
    def required_receipts(self):
        return self.spec.get("required_receipts", [])

    @property
    def citations(self):
        return self.spec.get("citations", [])

    def enforces(self, gate_name):
        return bool(self.gates.get(gate_name, False))

    def to_dict(self):
        return {
            "jurisdiction": self.jurisdiction,
            "vertical": self.vertical,
            "gates": self.gates,
            "forbidden_actions": self.forbidden_actions,
            "required_receipts": self.required_receipts,
            "citations": self.citations,
        }


def load_jurisdiction(jurisdiction, vertical="brokerage"):
    code = jurisdiction.lower()
    path = JURISDICTION_ROOT / code / f"{vertical}.json"
    if not path.exists():
        raise FileNotFoundError(f"No jurisdiction pack for ({jurisdiction},{vertical}) at {path}")
    spec = json.loads(path.read_text())
    return JurisdictionBundle(jurisdiction=code.upper(), vertical=vertical, spec=spec)


def list_available():
    out = []
    if not JURISDICTION_ROOT.exists():
        return out
    for jdir in JURISDICTION_ROOT.iterdir():
        if jdir.is_dir():
            for f in jdir.glob("*.json"):
                out.append((jdir.name.upper(), f.stem))
    return sorted(out)
PYEOF

log "✓ jurisdiction loader"

hdr "§4 · CA + WA policy packs"

cat > policies/jurisdictions/ca/brokerage.json << 'JSONEOF'
{
  "jurisdiction": "CA",
  "vertical": "brokerage",
  "version": "v1",
  "citations": [
    "CA Penal Code 632 (all-party consent, confidential communications)",
    "CA Penal Code 632.7 (cellular/cordless communications)",
    "42 USC 3601 et seq. (Fair Housing Act)",
    "47 USC 227 (TCPA)"
  ],
  "rules": {
    "call_recording_requires_all_party_consent": true,
    "pre_capture_disclosure_required": true,
    "tcpa_dnc_check_required_for_outbound": true,
    "fair_housing_lint_required_for_listing_marketing": true,
    "fair_housing_lint_required_for_buyer_match": true,
    "wire_execution_blocked": true,
    "wire_playbook_required": true,
    "agency_check_required_before_offer_actions": true,
    "required_disclosure_bundle_check": true
  },
  "forbidden_actions": [
    "wire.send",
    "offer.request_signatures_without_agency_check",
    "listing.publish_without_disclosure_completion",
    "comms.call_outbound_without_dnc_check"
  ],
  "required_receipts": ["ComputeReceipt","IDS_trace","transcript_chunk_if_voice_used"]
}
JSONEOF

cat > policies/jurisdictions/wa/brokerage.json << 'JSONEOF'
{
  "jurisdiction": "WA",
  "vertical": "brokerage",
  "version": "v1",
  "citations": [
    "RCW 9.73.030 (all-party consent; announcement-based consent permitted)",
    "RCW 18.86 (brokerage relationships, pamphlet requirement)",
    "RCW 19.158 (commercial telephone solicitation; real-estate carveout)"
  ],
  "rules": {
    "call_recording_requires_all_party_consent": true,
    "announcement_recorded_required": true,
    "pamphlet_surface_required": true,
    "agency_relationship_step_required": true,
    "outbound_high_compliance_mode": true,
    "consent_status_required_before_outbound_recommendation": true,
    "fair_housing_lint_required_for_listing_marketing": true,
    "wire_execution_blocked": true,
    "wire_playbook_required": true,
    "agency_check_required_before_offer_actions": true
  },
  "forbidden_actions": [
    "wire.send",
    "offer.request_signatures_without_agency_check",
    "listing.publish_without_disclosure_completion",
    "buyer.advance_consult_without_pamphlet_surface"
  ],
  "required_receipts": [
    "ComputeReceipt","IDS_trace","transcript_chunk_if_voice_used","pamphlet_ack_if_buyer_or_seller_consult"
  ]
}
JSONEOF

log "✓ CA + WA packs"

hdr "§5 · Compliance CPS ops"

cat > ops/compliance/__init__.py << 'PYEOF'
# AXIOLEV HOLDINGS LLC — DIGNITY PRESERVED
from .brokerage_gates import REGISTRY, register
__all__ = ["REGISTRY", "register"]
PYEOF

cat > ops/compliance/brokerage_gates.py << 'PYEOF'
"""
AXIOLEV NS∞ — Brokerage compliance ops
Six deterministic gate ops. Each returns:
  {ok: bool, gate: str, evidence: dict, timestamp: str, reason?: str}
Not a substitute for counsel — a pre-action gate so any forbidden action
emits a clean FAIL_CLOSED receipt before an adapter is touched.
Owner: AXIOLEV Holdings LLC. No LLM legal claim.
"""
from datetime import datetime, timezone


def _ts(): return datetime.now(timezone.utc).isoformat()


def _receipt(ok, gate, evidence, reason=""):
    r = {"ok": ok, "gate": gate, "evidence": evidence, "timestamp": _ts()}
    if reason: r["reason"] = reason
    return r


def check_fair_housing(payload):
    text = (payload.get("text") or "").lower()
    stoplist = ["no kids","adults only","no children","christian home",
                "perfect for singles","no section 8","prefer male","prefer female",
                "ideal for families","no families","mature tenants"]
    hits = [w for w in stoplist if w in text]
    if hits:
        return _receipt(False, "fair_housing",
                        {"text_sample": text[:200], "hits": hits},
                        reason=f"stoplist hit: {hits}")
    return _receipt(True, "fair_housing", {"text_length": len(text), "hits": []})


def check_tcpa_dnc(payload):
    phone = payload.get("phone")
    consent = payload.get("consent_status")
    dnc = payload.get("dnc_status")
    if not phone:
        return _receipt(False, "tcpa_dnc", {}, reason="missing phone")
    if consent not in ("express_written","express","prior_business_relationship"):
        return _receipt(False, "tcpa_dnc", {"phone": phone, "consent": consent}, reason="consent not verified")
    if dnc not in ("clear","not_listed"):
        return _receipt(False, "tcpa_dnc", {"phone": phone, "dnc": dnc}, reason="DNC status unresolved")
    return _receipt(True, "tcpa_dnc", {"phone": phone, "consent": consent, "dnc": dnc})


def check_ca_recording_consent(payload):
    participants = payload.get("participants", [])
    disclosures = payload.get("disclosures", [])
    missing = [p for p in participants if p not in disclosures]
    if missing:
        return _receipt(False, "ca_recording_consent",
                        {"participants": participants, "missing": missing},
                        reason=f"consent not recorded for: {missing}")
    return _receipt(True, "ca_recording_consent",
                    {"participants": participants, "disclosures_count": len(disclosures)})


def check_wa_recording_announcement(payload):
    ar = payload.get("announcement_recorded", False)
    ats = payload.get("announcement_timestamp")
    if not ar:
        return _receipt(False, "wa_recording_announcement",
                        {"announcement_recorded": False}, reason="announcement not recorded")
    if not ats:
        return _receipt(False, "wa_recording_announcement",
                        {"announcement_recorded": True, "timestamp": None},
                        reason="announcement timestamp missing")
    return _receipt(True, "wa_recording_announcement",
                    {"announcement_recorded": True, "timestamp": ats})


def check_agency(payload):
    status = payload.get("agency_status")
    ack = payload.get("agency_acknowledged", False)
    if status not in ("buyer","seller","dual_disclosed"):
        return _receipt(False, "agency_check", {"agency_status": status}, reason="agency not established")
    if not ack:
        return _receipt(False, "agency_check",
                        {"agency_status": status, "acknowledged": False},
                        reason="agency not acknowledged by party")
    return _receipt(True, "agency_check", {"agency_status": status, "acknowledged": True})


def block_wire_execution(payload):
    """UNCONDITIONAL block. Never returns ok=True."""
    return _receipt(False, "wire_execution_block",
                    {"intent": payload.get("intent"),
                     "amount": payload.get("amount"),
                     "destination": payload.get("destination")},
                    reason="wire execution structurally forbidden; route to wire-safe playbook")


REGISTRY = {
    "compliance.check_fair_housing": check_fair_housing,
    "compliance.check_tcpa_dnc": check_tcpa_dnc,
    "compliance.check_ca_recording_consent": check_ca_recording_consent,
    "compliance.check_wa_recording_announcement": check_wa_recording_announcement,
    "compliance.check_agency": check_agency,
    "compliance.block_wire_execution": block_wire_execution,
}


def register(cps_registry):
    n = 0
    for name, fn in REGISTRY.items():
        if hasattr(cps_registry, "register"):
            cps_registry.register(name, fn)
        else:
            cps_registry[name] = fn
        n += 1
    return n
PYEOF

log "✓ 6 compliance ops"

hdr "§6 · Adapters"

cat > adapters/brokerage/__init__.py << 'PYEOF'
# AXIOLEV HOLDINGS LLC — DIGNITY PRESERVED
from .mls import MLSAdapter
from .docs import DocsAdapter
from .offer import OfferAdapter
from .escrow import EscrowAdapter
from .wire import WireAdapter
from .comms import CommsAdapter
__all__ = ["MLSAdapter","DocsAdapter","OfferAdapter","EscrowAdapter","WireAdapter","CommsAdapter"]
PYEOF

cat > adapters/brokerage/mls.py << 'PYEOF'
"""AXIOLEV NS∞ — MLS adapter (RESO Web API shape, mocked)."""
from datetime import datetime, timezone

class MLSAdapter:
    def __init__(self, config=None):
        self.config = config or {}
        self.mock = self.config.get("mock", True)

    def fetch_property(self, address):
        return {"ok": True, "adapter": "mls.fetch_property", "mock": self.mock,
                "address": address, "data": {"beds": 3, "baths": 2, "sqft": 1820}}

    def fetch_comps(self, address, radius_mi=0.5):
        return {"ok": True, "adapter": "mls.fetch_comps", "mock": self.mock,
                "address": address, "comps": []}

    def stage_listing(self, listing):
        return {"ok": True, "adapter": "mls.stage_listing", "mock": self.mock,
                "listing_id": f"staged_{int(datetime.now(timezone.utc).timestamp())}"}

    def publish_listing(self, staging_id):
        return {"ok": True, "adapter": "mls.publish_listing", "mock": self.mock,
                "mls_number": f"MOCK{staging_id[-8:]}"}
PYEOF

cat > adapters/brokerage/docs.py << 'PYEOF'
"""AXIOLEV NS∞ — Docs adapter (DocuSign-shape, mocked)."""
from datetime import datetime, timezone

class DocsAdapter:
    def __init__(self, config=None):
        self.config = config or {}
        self.mock = self.config.get("mock", True)

    def request_esign(self, doc, signers):
        return {"ok": True, "adapter": "docs.request_esign", "mock": self.mock,
                "envelope_id": f"env_{int(datetime.now(timezone.utc).timestamp())}",
                "signers": [s.get("email") for s in signers]}

    def send_pamphlet(self, to, pamphlet_kind):
        return {"ok": True, "adapter": "docs.send_pamphlet", "mock": self.mock,
                "to": to, "kind": pamphlet_kind}

    def surface_wa_brokerage_pamphlet(self, buyer_or_seller):
        return {"ok": True, "adapter": "docs.surface_wa_brokerage_pamphlet",
                "mock": self.mock, "party": buyer_or_seller}
PYEOF

cat > adapters/brokerage/offer.py << 'PYEOF'
"""AXIOLEV NS∞ — Offer adapter (mocked)."""
from datetime import datetime, timezone

class OfferAdapter:
    def __init__(self, config=None):
        self.config = config or {}
        self.mock = self.config.get("mock", True)

    def generate(self, terms):
        return {"ok": True, "adapter": "offer.generate", "mock": self.mock,
                "offer_id": f"off_{int(datetime.now(timezone.utc).timestamp())}",
                "terms": terms}

    def compare(self, offers):
        return {"ok": True, "adapter": "offer.compare", "mock": self.mock,
                "ranking": list(range(len(offers)))}

    def counter_generate(self, offer_id, changes):
        return {"ok": True, "adapter": "offer.counter_generate", "mock": self.mock,
                "offer_id": offer_id, "counter": changes}
PYEOF

cat > adapters/brokerage/escrow.py << 'PYEOF'
"""AXIOLEV NS∞ — Escrow adapter (mocked)."""
from datetime import datetime, timezone

class EscrowAdapter:
    def __init__(self, config=None):
        self.config = config or {}
        self.mock = self.config.get("mock", True)

    def open(self, contract_id):
        return {"ok": True, "adapter": "escrow.open", "mock": self.mock,
                "escrow_id": f"esc_{int(datetime.now(timezone.utc).timestamp())}"}

    def track_deadline(self, escrow_id, deadline):
        return {"ok": True, "adapter": "escrow.track_deadline", "mock": self.mock,
                "escrow_id": escrow_id, "deadline": deadline}

    def attach_title_update(self, escrow_id, update):
        return {"ok": True, "adapter": "escrow.attach_title_update", "mock": self.mock,
                "escrow_id": escrow_id}

    def attach_lender_update(self, escrow_id, update):
        return {"ok": True, "adapter": "escrow.attach_lender_update", "mock": self.mock,
                "escrow_id": escrow_id}
PYEOF

cat > adapters/brokerage/wire.py << 'PYEOF'
"""
AXIOLEV NS∞ — Wire adapter.
By design this adapter NEVER exposes a .send() method. All wire intents
route through compliance.block_wire_execution (FAIL_CLOSED by design).
"""

class WireAdapter:
    def __init__(self, config=None):
        self.config = config or {}
        self.mock = self.config.get("mock", True)

    def verify_playbook(self, wire_details):
        checklist = ["out_of_band_phone_verification","known_contact_confirmation",
                     "recent_change_review","amount_sanity_check","destination_beneficiary_verified"]
        return {"ok": True, "adapter": "wire.verify_playbook", "mock": self.mock,
                "wire_id": wire_details.get("wire_id"),
                "checklist": checklist, "executable": False}
PYEOF

cat > adapters/brokerage/comms.py << 'PYEOF'
"""AXIOLEV NS∞ — Comms adapter (Twilio-shape, mocked)."""
from datetime import datetime, timezone

class CommsAdapter:
    def __init__(self, config=None):
        self.config = config or {}
        self.mock = self.config.get("mock", True)

    def call_outbound(self, to, from_, twiml_url):
        return {"ok": True, "adapter": "comms.call_outbound", "mock": self.mock,
                "call_sid": f"CA{int(datetime.now(timezone.utc).timestamp()):x}"}

    def send_sms(self, to, from_, body):
        return {"ok": True, "adapter": "comms.send_sms", "mock": self.mock,
                "message_sid": f"SM{int(datetime.now(timezone.utc).timestamp()):x}"}

    def send_email(self, to, subject, body):
        return {"ok": True, "adapter": "comms.send_email", "mock": self.mock,
                "message_id": f"em_{int(datetime.now(timezone.utc).timestamp())}"}

    def schedule_showing(self, property_id, when, parties):
        return {"ok": True, "adapter": "comms.schedule_showing", "mock": self.mock,
                "showing_id": f"sh_{int(datetime.now(timezone.utc).timestamp())}"}
PYEOF

log "✓ 6 adapters (wire has no .send by design)"

hdr "§7 · Mission graphs"

cat > programs/brokerage/missions/mg_resi_hunter_prospect.json << 'JSONEOF'
{
  "mission_id": "MG.RESI.HUNTER.PROSPECT",
  "version": "v1",
  "default_role": "hunter_operator",
  "states": ["H0_candidate_identified","H1_consent_dnc_check","H2_opening_prepared",
             "H3_first_contact","H4_disposition_logged","H5_followup_scheduled","H6_archive"],
  "transitions": [
    {"from":"H0_candidate_identified","trigger":"begin_outreach_prep","to":"H1_consent_dnc_check"},
    {"from":"H1_consent_dnc_check","trigger":"consent_dnc_ok","to":"H2_opening_prepared"},
    {"from":"H2_opening_prepared","trigger":"call_initiated","to":"H3_first_contact"},
    {"from":"H3_first_contact","trigger":"call_ended","to":"H4_disposition_logged"},
    {"from":"H4_disposition_logged","trigger":"followup_required","to":"H5_followup_scheduled"},
    {"from":"H5_followup_scheduled","trigger":"cycle_complete","to":"H6_archive"}
  ],
  "gate_hooks": {
    "H2_opening_prepared": ["compliance.check_tcpa_dnc","compliance.check_fair_housing"],
    "H3_first_contact": ["compliance.check_ca_recording_consent:if_ca","compliance.check_wa_recording_announcement:if_wa"]
  },
  "adapters": ["comms"]
}
JSONEOF

cat > programs/brokerage/missions/mg_resi_listing_intake.json << 'JSONEOF'
{
  "mission_id": "MG.RESI.LISTING.INTAKE",
  "version": "v1",
  "default_role": "listing_operator",
  "states": ["L0_seller_lead_created","L1_consult_live","L2_facts_capture","L3_pricing_prep",
             "L4_disclosures_check","L5_media_marketing_stage","L6_mls_stage",
             "L7_publish_approval","L8_listing_live","L9_seller_feedback_loop"],
  "transitions": [
    {"from":"L0_seller_lead_created","trigger":"consult_scheduled","to":"L1_consult_live"},
    {"from":"L1_consult_live","trigger":"facts_captured","to":"L2_facts_capture"},
    {"from":"L2_facts_capture","trigger":"comps_ready","to":"L3_pricing_prep"},
    {"from":"L3_pricing_prep","trigger":"disclosures_started","to":"L4_disclosures_check"},
    {"from":"L4_disclosures_check","trigger":"disclosures_complete","to":"L5_media_marketing_stage"},
    {"from":"L5_media_marketing_stage","trigger":"marketing_approved","to":"L6_mls_stage"},
    {"from":"L6_mls_stage","trigger":"publish_requested","to":"L7_publish_approval"},
    {"from":"L7_publish_approval","trigger":"published","to":"L8_listing_live"},
    {"from":"L8_listing_live","trigger":"feedback_received","to":"L9_seller_feedback_loop"}
  ],
  "gate_hooks": {
    "L5_media_marketing_stage": ["compliance.check_fair_housing"],
    "L7_publish_approval": ["compliance.check_fair_housing"]
  },
  "adapters": ["mls","docs"]
}
JSONEOF

cat > programs/brokerage/missions/mg_resi_buyer_consult.json << 'JSONEOF'
{
  "mission_id": "MG.RESI.BUYER.CONSULT",
  "version": "v1",
  "default_role": "buyer_operator",
  "states": ["B0_buyer_lead_created","B1_consult_live","B2_agency_pamphlet_surface",
             "B3_criteria_capture","B4_financing_status_check","B5_search_plan",
             "B6_tour_sequence","B7_followup_commit","B8_archive_learn"],
  "transitions": [
    {"from":"B0_buyer_lead_created","trigger":"consult_scheduled","to":"B1_consult_live"},
    {"from":"B1_consult_live","trigger":"pamphlet_surfaced","to":"B2_agency_pamphlet_surface"},
    {"from":"B2_agency_pamphlet_surface","trigger":"criteria_started","to":"B3_criteria_capture"},
    {"from":"B3_criteria_capture","trigger":"financing_discussed","to":"B4_financing_status_check"},
    {"from":"B4_financing_status_check","trigger":"plan_built","to":"B5_search_plan"},
    {"from":"B5_search_plan","trigger":"tours_scheduled","to":"B6_tour_sequence"},
    {"from":"B6_tour_sequence","trigger":"followup_committed","to":"B7_followup_commit"},
    {"from":"B7_followup_commit","trigger":"cycle_complete","to":"B8_archive_learn"}
  ],
  "gate_hooks": {"B2_agency_pamphlet_surface": ["compliance.check_agency:if_wa_relaxed"]},
  "adapters": ["docs","comms"]
}
JSONEOF

cat > programs/brokerage/missions/mg_resi_offer_esign.json << 'JSONEOF'
{
  "mission_id": "MG.RESI.OFFER.ESIGN",
  "version": "v1",
  "default_role": "offer_operator",
  "states": ["F0_context_created","F1_agency_verification","F2_terms_capture",
             "F3_draft_offer_generated","F4_strategy_review","F5_compare_or_counter",
             "F6_signatures_requested","F7_fully_executed","F8_distribution","F9_archive"],
  "transitions": [
    {"from":"F0_context_created","trigger":"agency_checked","to":"F1_agency_verification"},
    {"from":"F1_agency_verification","trigger":"terms_received","to":"F2_terms_capture"},
    {"from":"F2_terms_capture","trigger":"draft_ready","to":"F3_draft_offer_generated"},
    {"from":"F3_draft_offer_generated","trigger":"review_done","to":"F4_strategy_review"},
    {"from":"F4_strategy_review","trigger":"decision_made","to":"F5_compare_or_counter"},
    {"from":"F5_compare_or_counter","trigger":"signatures_sent","to":"F6_signatures_requested"},
    {"from":"F6_signatures_requested","trigger":"all_signed","to":"F7_fully_executed"},
    {"from":"F7_fully_executed","trigger":"distributed","to":"F8_distribution"},
    {"from":"F8_distribution","trigger":"archived","to":"F9_archive"}
  ],
  "gate_hooks": {
    "F1_agency_verification": ["compliance.check_agency"],
    "F6_signatures_requested": ["compliance.check_agency"]
  },
  "adapters": ["offer","docs"]
}
JSONEOF

cat > programs/brokerage/missions/mg_resi_escrow_wire_safe.json << 'JSONEOF'
{
  "mission_id": "MG.RESI.ESCROW.WIRE_SAFE",
  "version": "v1",
  "default_role": "escrow_operator",
  "states": ["E0_accepted_contract_received","E1_escrow_opened","E2_timeline_generated",
             "E3_inspections_title_lender_tracking","E4_contingency_monitoring",
             "E5_funding_and_settlement_prep","E6_wire_verification_playbook",
             "E7_signing","E8_recording_and_close","E9_post_close_actions","E10_archive_and_review"],
  "transitions": [
    {"from":"E0_accepted_contract_received","trigger":"escrow_opened","to":"E1_escrow_opened"},
    {"from":"E1_escrow_opened","trigger":"timeline_built","to":"E2_timeline_generated"},
    {"from":"E2_timeline_generated","trigger":"vendors_engaged","to":"E3_inspections_title_lender_tracking"},
    {"from":"E3_inspections_title_lender_tracking","trigger":"contingency_watch","to":"E4_contingency_monitoring"},
    {"from":"E4_contingency_monitoring","trigger":"funding_phase","to":"E5_funding_and_settlement_prep"},
    {"from":"E5_funding_and_settlement_prep","trigger":"wire_verification_started","to":"E6_wire_verification_playbook"},
    {"from":"E6_wire_verification_playbook","trigger":"verified","to":"E7_signing"},
    {"from":"E7_signing","trigger":"signed","to":"E8_recording_and_close"},
    {"from":"E8_recording_and_close","trigger":"recorded","to":"E9_post_close_actions"},
    {"from":"E9_post_close_actions","trigger":"complete","to":"E10_archive_and_review"}
  ],
  "gate_hooks": {
    "E6_wire_verification_playbook": ["compliance.block_wire_execution"],
    "E7_signing": ["compliance.check_agency"]
  },
  "adapters": ["escrow","wire","docs"]
}
JSONEOF

cat > programs/brokerage/missions/mg_resi_close_postcare.json << 'JSONEOF'
{
  "mission_id": "MG.RESI.CLOSE.POSTCARE",
  "version": "v1",
  "default_role": "violet_interface_operator",
  "states": ["P0_recording_confirmed","P1_key_handoff","P2_settlement_review",
             "P3_review_request_queued","P4_referral_nurture_scheduled","P5_archive"],
  "transitions": [
    {"from":"P0_recording_confirmed","trigger":"keys_delivered","to":"P1_key_handoff"},
    {"from":"P1_key_handoff","trigger":"settlement_reviewed","to":"P2_settlement_review"},
    {"from":"P2_settlement_review","trigger":"review_queued","to":"P3_review_request_queued"},
    {"from":"P3_review_request_queued","trigger":"nurture_scheduled","to":"P4_referral_nurture_scheduled"},
    {"from":"P4_referral_nurture_scheduled","trigger":"archived","to":"P5_archive"}
  ],
  "adapters": ["comms"]
}
JSONEOF

log "✓ 6 residential missions"

hdr "§8 · Role bindings"

cat > programs/brokerage/roles/violet_interface_operator.json << 'JSONEOF'
{
  "role_id":"violet_interface_operator","voice_profile":"violet_voice_v1",
  "allowed_states":["B1","B2","P0","P1","P2","P3","P4","P5"],
  "functions":["frame_context","capture_intent","ask_missing_questions","offer_next_step","generate_whisper"],
  "forbidden":["unverified_regulatory_claims","wire_execution","pricing_commitment_without_role_transfer"],
  "memory_scope_spec":{"allowed_keys":["deal.stage","deal.parties","deal.next_step","deal.notes_public"],
                       "excluded_keys":["deal.pricing_floor","deal.negotiation_strategy","deal.financial_disclosure"]}
}
JSONEOF

cat > programs/brokerage/roles/hunter_operator.json << 'JSONEOF'
{
  "role_id":"hunter_operator","voice_profile":"hunter_voice_v1",
  "missions":["MG.RESI.HUNTER.PROSPECT"],
  "allowed_states":["H0","H1","H2","H3","H4","H5"],
  "functions":["surface_propensity","suggest_opening_line","check_consent","guide_call","log_outcome"],
  "memory_scope_spec":{"allowed_keys":["candidate.public_record","candidate.propensity_score","candidate.consent_status"],
                       "excluded_keys":["candidate.private_financial","candidate.health_info"]}
}
JSONEOF

cat > programs/brokerage/roles/listing_operator.json << 'JSONEOF'
{
  "role_id":"listing_operator","voice_profile":"listing_voice_v1",
  "missions":["MG.RESI.LISTING.INTAKE"],
  "allowed_states":["L1","L2","L3","L4","L5","L6","L7","L8","L9"],
  "functions":["capture_property_facts","surface_missing_disclosures","guide_pricing_frame","stage_marketing_assets","request_publish_approval"],
  "memory_scope_spec":{"allowed_keys":["property.facts","property.disclosures","listing.marketing","seller.priorities"],
                       "excluded_keys":["seller.financial_pressure_private","seller.divorce_context"]}
}
JSONEOF

cat > programs/brokerage/roles/buyer_operator.json << 'JSONEOF'
{
  "role_id":"buyer_operator","voice_profile":"buyer_voice_v1",
  "missions":["MG.RESI.BUYER.CONSULT"],
  "allowed_states":["B1","B2","B3","B4","B5","B6","B7"],
  "functions":["capture_criteria","surface_agency_pamphlet","check_financing_readiness","build_search_plan","sequence_tours"],
  "memory_scope_spec":{"allowed_keys":["buyer.criteria","buyer.agency_ack","buyer.financing_status_public"],
                       "excluded_keys":["buyer.credit_score_raw","buyer.private_income_detail"]}
}
JSONEOF

cat > programs/brokerage/roles/offer_operator.json << 'JSONEOF'
{
  "role_id":"offer_operator","voice_profile":"offer_voice_v1",
  "missions":["MG.RESI.OFFER.ESIGN"],
  "allowed_states":["F1","F2","F3","F4","F5","F6"],
  "functions":["verify_agency","capture_terms","draft_offer","compare_offers","guide_counter"],
  "memory_scope_spec":{"allowed_keys":["offer.terms","offer.comparison","offer.agency_status"],
                       "excluded_keys":["offer.seller_motivation_private","offer.buyer_ceiling_private"]}
}
JSONEOF

cat > programs/brokerage/roles/escrow_operator.json << 'JSONEOF'
{
  "role_id":"escrow_operator","voice_profile":"escrow_voice_v1",
  "missions":["MG.RESI.ESCROW.WIRE_SAFE"],
  "allowed_states":["E1","E2","E3","E4","E5","E6","E7","E8","E9"],
  "functions":["build_timeline","flag_deadlines","track_vendors","verify_wire_playbook","coordinate_close"],
  "memory_scope_spec":{"allowed_keys":["escrow.timeline","escrow.vendors","escrow.contingencies","escrow.wire_verification_status"],
                       "excluded_keys":["escrow.bank_account_numbers","escrow.wire_routing_raw"]}
}
JSONEOF

cat > programs/brokerage/roles/compliance_operator.json << 'JSONEOF'
{
  "role_id":"compliance_operator","voice_profile":"compliance_voice_v1",
  "allowed_states":["*"],
  "functions":["fair_housing_lint","tcpa_dnc_check","ca_recording_consent_check","wa_recording_announcement_check","agency_check","wire_fraud_block"],
  "memory_scope_spec":{"allowed_keys":["*"],"excluded_keys":[]},
  "note":"Full read scope to enforce gates; cannot execute adapters directly."
}
JSONEOF

log "✓ 7 role bindings"

hdr "§9 · Program definition + library entry"

cat > programs/brokerage/whisper_brokerage_residential_starter_v1.json << 'JSONEOF'
{
  "program_id": "whisper_brokerage_residential_starter_v1",
  "program_name": "Whisper Brokerage — Residential Starter",
  "version": "v1",
  "vertical": "brokerage_residential",
  "interface_layer": "Violet",
  "binding_layer": "Eloh_Handrail",
  "default_output_mode": "whisper",
  "allowed_output_modes": ["whisper","assisted_voice","direct_voice"],
  "receipt_mode": "required",
  "jurisdictions_supported": ["CA","WA"],
  "missions": ["MG.RESI.HUNTER.PROSPECT","MG.RESI.LISTING.INTAKE","MG.RESI.BUYER.CONSULT",
               "MG.RESI.OFFER.ESIGN","MG.RESI.ESCROW.WIRE_SAFE","MG.RESI.CLOSE.POSTCARE"],
  "roles": ["violet_interface_operator","hunter_operator","listing_operator",
            "buyer_operator","offer_operator","escrow_operator","compliance_operator"],
  "adapters": ["mls","docs","offer","escrow","wire","comms"],
  "compliance_ops": ["compliance.check_fair_housing","compliance.check_tcpa_dnc",
                     "compliance.check_ca_recording_consent","compliance.check_wa_recording_announcement",
                     "compliance.check_agency","compliance.block_wire_execution"],
  "meta_states": ["R0_INIT","R1_INTAKE","R2_FRAME","R3_QUALIFY","R4_PLAN","R5_EXECUTE",
                  "R6_VERIFY","R7_COMMIT","R8_MONITOR","R9_CLOSE","R10_ARCHIVE","R11_LEARN"]
}
JSONEOF

python3 - << 'PYEOF'
import json
from pathlib import Path
lib_path = Path("programs/program_library_v1.json")
lib = json.loads(lib_path.read_text())
progs = lib.get("programs", [])
entry = {
    "program_id": "whisper_brokerage_residential_starter_v1",
    "name": "Whisper Brokerage Residential Starter",
    "vertical": "brokerage_residential",
    "states": ["R0_INIT","R1_INTAKE","R2_FRAME","R3_QUALIFY","R4_PLAN","R5_EXECUTE",
               "R6_VERIFY","R7_COMMIT","R8_MONITOR","R9_CLOSE","R10_ARCHIVE","R11_LEARN"],
    "definition_path": "programs/brokerage/whisper_brokerage_residential_starter_v1.json"
}
if not any(p.get("program_id") == entry["program_id"] for p in progs):
    progs.append(entry)
    lib["programs"] = progs
    lib_path.write_text(json.dumps(lib, indent=2))
    print(f"[library] appended: {entry['program_id']}")
else:
    print(f"[library] already present: {entry['program_id']} (no-op)")
PYEOF

log "✓ program + library"

hdr "§10 · Smoke tests"

cat > tests/brokerage/test_brokerage_v1_smoke.py << 'PYEOF'
"""AXIOLEV NS∞ — Brokerage v1 smoke tests. Zero LLM calls, zero network."""
import json, sys
from pathlib import Path
sys.path.insert(0, ".")

FAILED = []


def check(name, cond, detail=""):
    if cond:
        print(f"  [OK]   {name}")
    else:
        print(f"  [FAIL] {name} — {detail}")
        FAILED.append(name)


def test_jurisdiction_loader():
    print("\n· Jurisdiction loader")
    from runtime.jurisdiction import load_jurisdiction, list_available
    avail = list_available()
    check("CA+WA packs available",
          ("CA","brokerage") in avail and ("WA","brokerage") in avail, f"got {avail}")
    ca = load_jurisdiction("CA","brokerage")
    check("CA loads", ca.jurisdiction=="CA")
    check("CA all-party consent", ca.enforces("call_recording_requires_all_party_consent"))
    check("CA forbids wire.send", "wire.send" in ca.forbidden_actions)
    check("CA has statute citations", len(ca.citations) >= 2)
    wa = load_jurisdiction("WA","brokerage")
    check("WA loads", wa.jurisdiction=="WA")
    check("WA pamphlet required", wa.enforces("pamphlet_surface_required"))


def test_compliance_ops():
    print("\n· Compliance ops")
    from ops.compliance.brokerage_gates import REGISTRY
    expected = {"compliance.check_fair_housing","compliance.check_tcpa_dnc",
                "compliance.check_ca_recording_consent","compliance.check_wa_recording_announcement",
                "compliance.check_agency","compliance.block_wire_execution"}
    check("all 6 ops registered", set(REGISTRY.keys())==expected)
    r = REGISTRY["compliance.check_fair_housing"]({"text":"Adults only, no kids."})
    check("fair_housing fails on stoplist", r["ok"] is False)
    r = REGISTRY["compliance.check_fair_housing"]({"text":"Bright 3 bed, updated kitchen."})
    check("fair_housing passes on clean", r["ok"] is True)
    r = REGISTRY["compliance.block_wire_execution"]({"intent":"send","amount":500000,"destination":"x"})
    check("wire_block always ok=False", r["ok"] is False)
    r = REGISTRY["compliance.check_agency"]({"agency_status":None})
    check("agency_check fails no status", r["ok"] is False)
    r = REGISTRY["compliance.check_tcpa_dnc"]({"phone":"+15551234567","consent_status":"express_written","dnc_status":"clear"})
    check("tcpa_dnc passes with good inputs", r["ok"] is True)


def test_adapters():
    print("\n· Adapters")
    from adapters.brokerage import (MLSAdapter, DocsAdapter, OfferAdapter,
                                    EscrowAdapter, WireAdapter, CommsAdapter)
    for cls in (MLSAdapter, DocsAdapter, OfferAdapter, EscrowAdapter, WireAdapter, CommsAdapter):
        check(f"{cls.__name__} instantiates", cls() is not None)
    w = WireAdapter()
    check("WireAdapter has verify_playbook", hasattr(w,"verify_playbook"))
    check("WireAdapter has NO .send", not hasattr(w,"send"))
    r = w.verify_playbook({"wire_id":"w1"})
    check("verify_playbook executable=False", r["executable"] is False)


def test_mission_graphs():
    print("\n· Mission graphs")
    d = Path("programs/brokerage/missions")
    expected = {"mg_resi_hunter_prospect.json","mg_resi_listing_intake.json",
                "mg_resi_buyer_consult.json","mg_resi_offer_esign.json",
                "mg_resi_escrow_wire_safe.json","mg_resi_close_postcare.json"}
    present = {p.name for p in d.glob("*.json")}
    check("all 6 missions present", expected.issubset(present), f"missing: {expected-present}")
    for f in expected:
        data = json.loads((d/f).read_text())
        check(f"{f} mission_id", "mission_id" in data)
        check(f"{f} states≥1", len(data.get("states",[]))>0)
        check(f"{f} transitions≥1", len(data.get("transitions",[]))>0)


def test_program_library():
    print("\n· Program library")
    lib = json.loads(Path("programs/program_library_v1.json").read_text())
    ids = {p["program_id"] for p in lib.get("programs",[])}
    check("brokerage registered", "whisper_brokerage_residential_starter_v1" in ids)


def test_roles():
    print("\n· Role bindings")
    d = Path("programs/brokerage/roles")
    expected = {"violet_interface_operator.json","hunter_operator.json","listing_operator.json",
                "buyer_operator.json","offer_operator.json","escrow_operator.json","compliance_operator.json"}
    present = {p.name for p in d.glob("*.json")}
    check("all 7 roles present", expected.issubset(present), f"missing: {expected-present}")
    for f in expected:
        data = json.loads((d/f).read_text())
        check(f"{f} has memory_scope_spec", "memory_scope_spec" in data)


if __name__ == "__main__":
    print("═══════════════════════════════════════════════════════════════════")
    print(" BROKERAGE v1 SMOKE TESTS")
    print("═══════════════════════════════════════════════════════════════════")
    test_jurisdiction_loader()
    test_compliance_ops()
    test_adapters()
    test_mission_graphs()
    test_program_library()
    test_roles()
    print("")
    if FAILED:
        print(f"✗ {len(FAILED)} failure(s): {FAILED}")
        sys.exit(1)
    print("✓ ALL SMOKE TESTS PASSED")
PYEOF

log "✓ smoke test suite"

hdr "§11 · Running smoke tests"

TEST_LOG="$BUILD_LOG_DIR/smoke_build_${STAMP}.log"
if python3 tests/brokerage/test_brokerage_v1_smoke.py 2>&1 | tee "$TEST_LOG"; then
    BUILD_TESTS_PASS=true
    log "✓ smoke PASS"
else
    BUILD_TESTS_PASS=false
    log "✗ smoke FAIL — aborting before commit"
fi

hdr "§12 · Stage + commit (worktree only)"

BUILD_COMMITTED_SHA=""
BUILD_TAG_CREATED=false

if [ "$BUILD_TESTS_PASS" = "true" ]; then
    git add \
        programs/brokerage \
        policies/jurisdictions \
        adapters/brokerage \
        runtime/jurisdiction \
        ops/compliance \
        tests/brokerage \
        programs/program_library_v1.json

    git diff --cached --stat > "$BUILD_LOG_DIR/stage_${STAMP}.txt" || true

    if ! git diff --cached --quiet; then
        git -c user.name="AXIOLEV Build Bot" -c user.email="build@axiolev.internal" \
            commit -F - << 'COMMITEOF'
feat(brokerage): whisper_brokerage_residential_starter_v1 parallel build

Isolated worktree build — zero collision with terminal-1 Ring 6 / Doctrine
/ Clearing Layer / UI / Autopoiesis work in main checkout.

Scope:
- JurisdictionBundle loader (CA + WA packs with statute citations)
- 6 compliance CPS ops: fair_housing, tcpa_dnc, ca_recording_consent,
  wa_recording_announcement, agency, block_wire_execution
- 6 mission graphs: MG.RESI.{HUNTER,LISTING,BUYER,OFFER,ESCROW,CLOSE}
- 7 role bindings with memory_scope_spec
- 6 adapters (mls, docs, offer, escrow, wire, comms) —
  WireAdapter deliberately has no .send() method
- Program registered in program_library_v1
- Full smoke test suite (passed before commit)

Additive only — no modification of ProgramEngine, Handrail, DignityKernel.
IP: AXIOLEV Holdings LLC. LLM tools hold no legal claim.
Dignity: AXIOLEV HOLDINGS LLC — DIGNITY PRESERVED
COMMITEOF
        BUILD_COMMITTED_SHA="$(git rev-parse HEAD)"
        log "✓ commit $BUILD_COMMITTED_SHA"

        if ! git rev-parse "$TAG_BUILT" >/dev/null 2>&1; then
            git tag -a "$TAG_BUILT" -m "Brokerage v1 built $STAMP. AXIOLEV."
            BUILD_TAG_CREATED=true
            log "✓ tag $TAG_BUILT (local only)"
        fi
    else
        log "nothing to commit (identical content)"
    fi
else
    log "commit SKIPPED (tests failed)"
fi

hdr "§13 · Waiting for terminal-1 completion signal"

SIGNAL_FOUND=""
SIGNAL_CONTENT=""
SIGNAL_WAIT_START="$(date -u +%s)"

if [ "$BUILD_TESTS_PASS" != "true" ]; then
    log "build failed → skipping signal watcher (nothing safe to merge)"
elif [ "$DRY_RUN" = "true" ]; then
    log "DRY_RUN=true → skipping signal watcher"
else
    log "Watching every ${SIGNAL_POLL_SEC}s for:"
    for sf in "${SIGNAL_FILES[@]}"; do log "  - $sf"; done
    log "(Terminal-1 writes any one of these to trigger auto-merge.)"

    WAIT_DEADLINE=0
    if [ "$SIGNAL_TIMEOUT_MIN" -gt 0 ]; then
        WAIT_DEADLINE=$(( SIGNAL_WAIT_START + SIGNAL_TIMEOUT_MIN * 60 ))
    fi

    while true; do
        for sf in "${SIGNAL_FILES[@]}"; do
            if [ -f "$sf" ]; then
                SIGNAL_FOUND="$sf"
                SIGNAL_CONTENT="$(cat "$sf" 2>/dev/null || echo '')"
                break
            fi
        done
        [ -n "$SIGNAL_FOUND" ] && break

        if [ "$WAIT_DEADLINE" -ne 0 ] && [ "$(date -u +%s)" -ge "$WAIT_DEADLINE" ]; then
            log "⏰ signal timeout reached (${SIGNAL_TIMEOUT_MIN} min) — exiting"
            break
        fi

        NOW=$(date -u +%s)
        ELAPSED=$(( (NOW - SIGNAL_WAIT_START) / 60 ))
        if [ $(( (NOW - SIGNAL_WAIT_START) % 300 )) -lt "$SIGNAL_POLL_SEC" ]; then
            log "… still waiting (${ELAPSED} min elapsed)"
        fi

        sleep "$SIGNAL_POLL_SEC"
    done
fi

hdr "§14 · Auto-merge to $TARGET"

MERGE_ATTEMPTED=false
MERGE_OK=false
MERGE_SHA=""
MERGE_TAG_CREATED=false
POST_TESTS_PASS=false
ROLLBACK_PERFORMED=false

if [ -n "$SIGNAL_FOUND" ] && [ "$BUILD_TESTS_PASS" = "true" ] && [ "$DRY_RUN" != "true" ]; then
    MERGE_ATTEMPTED=true
    log "signal: $SIGNAL_FOUND"
    [ -n "$SIGNAL_CONTENT" ] && log "content: $SIGNAL_CONTENT"

    cd "$REPO"

    for lock in .git/index.lock .git/HEAD.lock .git/MERGE_HEAD .git/rebase-merge .git/rebase-apply; do
        if [ -e "$REPO/$lock" ]; then
            log "FAIL: repo still locked ($lock) despite signal — skipping merge"
            MERGE_ATTEMPTED=false
            break
        fi
    done

    if [ "$MERGE_ATTEMPTED" = "true" ]; then
        if ! git diff --quiet HEAD -- 2>/dev/null; then
            log "FAIL: $TARGET has uncommitted changes — cannot merge cleanly"
            git status --short | sed 's/^/       /'
            MERGE_ATTEMPTED=false
        fi
    fi

    if [ "$MERGE_ATTEMPTED" = "true" ]; then
        CUR="$(git rev-parse --abbrev-ref HEAD)"
        if [ "$CUR" != "$TARGET" ]; then
            log "switching $CUR → $TARGET"
            git checkout "$TARGET" || { log "FAIL: checkout $TARGET"; MERGE_ATTEMPTED=false; }
        fi
    fi

    if [ "$MERGE_ATTEMPTED" = "true" ]; then
        PRE_MERGE_SHA="$(git rev-parse HEAD)"
        log "pre-merge $TARGET HEAD: $PRE_MERGE_SHA"

        (
            cd "$WT"
            log "re-testing worktree against current $TARGET..."
            python3 tests/brokerage/test_brokerage_v1_smoke.py
        ) 2>&1 | tee "$BUILD_LOG_DIR/smoke_preMerge_${STAMP}.log"

        PREMERGE_RC=${PIPESTATUS[0]}
        if [ "$PREMERGE_RC" -ne 0 ]; then
            log "✗ pre-merge retest failed — aborting merge"
            MERGE_ATTEMPTED=false
        fi
    fi

    if [ "$MERGE_ATTEMPTED" = "true" ]; then
        MERGE_MSG="merge: whisper_brokerage_residential_starter_v1 (feature/brokerage-v1)

Auto-merge triggered by terminal-1 completion signal:
  signal_file: $SIGNAL_FOUND

Pre-merge target HEAD: $PRE_MERGE_SHA
Pre-merge brokerage HEAD: $(git rev-parse $BRANCH)

Artifacts integrated:
- 6 mission graphs (MG.RESI.*)
- 7 role bindings
- 6 adapters (WireAdapter has no .send by design)
- 2 jurisdiction packs (CA + WA) with statute citations
- 6 compliance CPS ops
- 1 program definition + library entry

Post-merge manual step required:
- Register compliance ops in CPS op-registry init:
    from ops.compliance import register as _rg
    _rg(CPS_OPS)

$DIGNITY"

        if git merge --no-ff "$BRANCH" -m "$MERGE_MSG"; then
            MERGE_SHA="$(git rev-parse HEAD)"
            MERGE_OK=true
            log "✓ merged → $MERGE_SHA"
        else
            log "✗ merge conflict — aborting"
            git merge --abort 2>/dev/null || true
            MERGE_OK=false
        fi
    fi

    if [ "$MERGE_OK" = "true" ]; then
        log "running post-merge smoke tests"
        if python3 tests/brokerage/test_brokerage_v1_smoke.py 2>&1 | tee "$BUILD_LOG_DIR/smoke_postMerge_${STAMP}.log"; then
            POST_TESTS_PASS=true
            log "✓ post-merge tests green"

            if ! git rev-parse "$TAG_MERGED" >/dev/null 2>&1; then
                git tag -a "$TAG_MERGED" -m "Brokerage v1 merged $STAMP. AXIOLEV."
                MERGE_TAG_CREATED=true
                log "✓ tag $TAG_MERGED"
            fi

            if [ "$AUTO_PUSH" = "true" ]; then
                log "AUTO_PUSH=true → pushing $TARGET + tags"
                git push origin "$TARGET" || log "WARN: push $TARGET failed"
                git push origin "$TAG_BUILT" 2>/dev/null || true
                git push origin "$TAG_MERGED" 2>/dev/null || true
            else
                log "AUTO_PUSH=false → merge local only; push manually when ready"
            fi
        else
            POST_TESTS_PASS=false
            log "✗ post-merge tests FAILED → rolling back to $PRE_MERGE_SHA"
            git reset --hard "$PRE_MERGE_SHA"
            ROLLBACK_PERFORMED=true
            log "✓ rollback complete; $TARGET restored to $PRE_MERGE_SHA"
        fi
    fi
else
    if [ "$BUILD_TESTS_PASS" != "true" ]; then
        log "skip merge (build tests failed)"
    elif [ "$DRY_RUN" = "true" ]; then
        log "skip merge (DRY_RUN)"
    elif [ -z "$SIGNAL_FOUND" ]; then
        log "skip merge (no signal received within timeout — build artifacts preserved on $BRANCH)"
    fi
fi

hdr "§15 · Return block"

mkdir -p "$PACKET_INBOX"

NUM_MISSIONS=$(ls "$WT"/programs/brokerage/missions/*.json 2>/dev/null | wc -l | tr -d ' ')
NUM_ROLES=$(ls "$WT"/programs/brokerage/roles/*.json 2>/dev/null | wc -l | tr -d ' ')
NUM_ADAPTERS=$(ls "$WT"/adapters/brokerage/*.py 2>/dev/null | grep -v __init__ | wc -l | tr -d ' ')
NUM_JUR=$(ls "$WT"/policies/jurisdictions/*/brokerage.json 2>/dev/null | wc -l | tr -d ' ')

SIGNAL_CONTENT_ESCAPED=$(printf '%s' "$SIGNAL_CONTENT" | python3 -c 'import sys,json; print(json.dumps(sys.stdin.read()))' 2>/dev/null || echo '""')

cat > "$RETURN_JSON" << JSONEOF
{
  "return_block_version": 2,
  "worker_kind": "brokerage_v1_build_and_merge",
  "stamp": "$STAMP",
  "dignity_banner": "$DIGNITY",
  "build": {
    "tests_passed": $BUILD_TESTS_PASS,
    "committed_sha": "$BUILD_COMMITTED_SHA",
    "local_tag": "$([ "$BUILD_TAG_CREATED" = "true" ] && echo "$TAG_BUILT" || echo "")",
    "worktree_path": "$WT",
    "branch": "$BRANCH",
    "base_sha": "$BASE_SHA"
  },
  "artifacts": {
    "missions": $NUM_MISSIONS,
    "roles": $NUM_ROLES,
    "adapters": $NUM_ADAPTERS,
    "jurisdiction_packs": $NUM_JUR,
    "compliance_ops": 6
  },
  "signal_watch": {
    "signal_found": $([ -n "$SIGNAL_FOUND" ] && echo true || echo false),
    "signal_path": "$SIGNAL_FOUND",
    "signal_content": $SIGNAL_CONTENT_ESCAPED,
    "timeout_min": $SIGNAL_TIMEOUT_MIN,
    "watched_paths": [
      "${SIGNAL_FILES[0]}",
      "${SIGNAL_FILES[1]}"
    ]
  },
  "merge": {
    "attempted": $MERGE_ATTEMPTED,
    "ok": $MERGE_OK,
    "merge_sha": "$MERGE_SHA",
    "target_branch": "$TARGET",
    "source_branch": "$BRANCH",
    "tag_created": "$([ "$MERGE_TAG_CREATED" = "true" ] && echo "$TAG_MERGED" || echo "")",
    "rollback_performed": $ROLLBACK_PERFORMED
  },
  "post_merge": {
    "tests_passed": $POST_TESTS_PASS
  },
  "push": {
    "auto_push_enabled": $([ "$AUTO_PUSH" = "true" ] && echo true || echo false),
    "pushed": false,
    "note": "Local only by default. Set AUTO_PUSH=true to push. Or manually: git push origin $TARGET $TAG_BUILT $TAG_MERGED"
  },
  "next_steps": [
    "If merge OK + tests green: register compliance ops in CPS init (from ops.compliance import register; register(CPS_OPS))",
    "First live brokerage run: POST /program/start {\"program_id\":\"whisper_brokerage_residential_starter_v1\",\"jurisdiction\":\"CA\",\"mission_id\":\"MG.RESI.LISTING.INTAKE\"}",
    "Optional cleanup: git worktree remove $WT"
  ]
}
JSONEOF

[ -d "$ALEX_OUT" ] && cp "$RETURN_JSON" "$ALEX_OUT/brokerage_full_${STAMP}.json" 2>/dev/null || true
log "✓ return block → $RETURN_JSON"

echo ""
echo "═════════════════════════════════════════════════════════════════════════"
if [ "$MERGE_OK" = "true" ] && [ "$POST_TESTS_PASS" = "true" ]; then
    echo " ✓ BROKERAGE v1 COMPLETE — merged + green on $TARGET"
elif [ "$BUILD_TESTS_PASS" = "true" ] && [ -z "$SIGNAL_FOUND" ]; then
    echo " ⏸ BROKERAGE v1 BUILT — waiting (no signal received yet)"
elif [ "$ROLLBACK_PERFORMED" = "true" ]; then
    echo " ↩ BROKERAGE v1 ROLLED BACK — post-merge tests failed"
else
    echo " ⚠ BROKERAGE v1 — see return block for status"
fi
echo "═════════════════════════════════════════════════════════════════════════"
echo "REPORT_PATH=$RETURN_JSON"
echo "BUILD_TESTS_PASSED=$BUILD_TESTS_PASS"
echo "SIGNAL_FOUND=$([ -n "$SIGNAL_FOUND" ] && echo true || echo false)"
echo "MERGE_ATTEMPTED=$MERGE_ATTEMPTED"
echo "MERGE_OK=$MERGE_OK"
echo "POST_TESTS_PASSED=$POST_TESTS_PASS"
echo "ROLLBACK=$ROLLBACK_PERFORMED"
echo "WORKTREE=$WT"
echo "BRANCH=$BRANCH → $TARGET"
echo ""
echo " $DIGNITY"
echo "═════════════════════════════════════════════════════════════════════════"
