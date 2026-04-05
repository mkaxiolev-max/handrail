"""
Memory Scope Enforcement — hard boundary at context assembly.
Not a suggestion. Not a role instruction.
The context object for each role is constructed with surgical exclusions BEFORE reaching any LLM.
"""
import json
from pathlib import Path
from typing import Optional

POLICY_DIR = Path(__file__).parent.parent / "policies"

# Hard-coded scope specs (also in policy bundles — this is the enforcement layer)
ROLE_MEMORY_SCOPES = {
    "elaine_access_operator": {
        "include": ["prospect_background","prior_call_summaries","program_state","company_overview","public_signals"],
        "exclude": ["pricing_history","deal_structure","competitor_terms","founder_personal_notes","stewart_notes","heidi_clinical_context","legal_draft","advisor_equity_terms"],
    },
    "stewart_negotiation_operator": {
        "include": ["pricing_history","objections","decision_map","prior_commitments","deal_structure","program_state","close_criteria"],
        "exclude": ["founder_personal_notes","heidi_clinical_context","advisor_equity_terms","hiring_context","fundraising_context"],
    },
    "heidi_validation_operator": {
        "include": ["validation_context_only","clinical_question","skepticism_signal"],
        "exclude": ["pricing","deal_structure","fundraising","hiring","partnership","ma","governance","founder_notes","commercial_strategy"],
    },
    "legal_operator": {
        "include": ["contract_draft","deal_structure","close_criteria","legal_flags"],
        "exclude": ["clinical_context","pricing_negotiation_history","founder_personal_notes"],
    },
    "founder": {
        "include": ["debrief_summaries","approval_requests","escalations","risk_flags","program_state"],
        "exclude": ["raw_conversation_transcripts","detailed_objection_logs"],
        "note": "Founder sees summaries and decisions, not live operational detail",
    },
}

class MemoryScope:
    def assemble_context(self, role: str, full_context: dict) -> dict:
        """
        Hard-bounded context assembly. Returns only what this role is allowed to see.
        Exclusions are enforced by key deletion, not by instruction.
        """
        scope = ROLE_MEMORY_SCOPES.get(role)
        if not scope:
            # Unknown role: return minimal safe context
            return {"program_state": full_context.get("program_state"), "_scope_warning": f"unknown role {role}"}

        scoped = {}
        include_keys = scope.get("include", [])
        exclude_keys = set(scope.get("exclude", []))

        for key, value in full_context.items():
            if key in include_keys:
                scoped[key] = value
            elif key not in exclude_keys and not any(ex in key for ex in exclude_keys):
                # Pass through neutral keys (program metadata, timestamps)
                if key.startswith("_") or key in ["program_id","program_run_id","state","active_role","timestamp"]:
                    scoped[key] = value

        scoped["_scope_enforced_for"] = role
        scoped["_excluded_keys_count"] = len([k for k in full_context if k not in scoped])
        return scoped

    def audit_scope_leak(self, role: str, context: dict) -> list:
        """Check for scope violations in an assembled context."""
        scope = ROLE_MEMORY_SCOPES.get(role, {})
        exclude_keys = set(scope.get("exclude", []))
        violations = []
        for key in context:
            if key in exclude_keys or any(ex in key for ex in exclude_keys):
                violations.append(f"SCOPE_LEAK: {role} has access to excluded key: {key}")
        return violations
