"""
Guardrails & Compliance for SpendSenseAI.

Provides:
- Consent Management System
- Decision Trace Logging System
"""

from .consent import (
    ConsentStatus,
    ConsentScope,
    ConsentRecord,
    ConsentAuditEntry,
    create_consent_tables,
    grant_consent,
    revoke_consent,
    get_consent,
    verify_consent,
    get_consent_audit_trail,
    get_all_consents_for_user
)

from .decision_trace import (
    ReviewStatus,
    SignalTrace,
    PersonaTrace,
    RecommendationTrace,
    DecisionTrace,
    create_decision_trace_tables,
    create_decision_trace,
    save_decision_trace,
    get_decision_trace,
    get_decision_traces_for_user,
    get_pending_reviews,
    update_review_status,
    export_trace_to_json
)

__all__ = [
    # Consent Management
    'ConsentStatus',
    'ConsentScope',
    'ConsentRecord',
    'ConsentAuditEntry',
    'create_consent_tables',
    'grant_consent',
    'revoke_consent',
    'get_consent',
    'verify_consent',
    'get_consent_audit_trail',
    'get_all_consents_for_user',
    
    # Decision Trace
    'ReviewStatus',
    'SignalTrace',
    'PersonaTrace',
    'RecommendationTrace',
    'DecisionTrace',
    'create_decision_trace_tables',
    'create_decision_trace',
    'save_decision_trace',
    'get_decision_trace',
    'get_decision_traces_for_user',
    'get_pending_reviews',
    'update_review_status',
    'export_trace_to_json'
]
