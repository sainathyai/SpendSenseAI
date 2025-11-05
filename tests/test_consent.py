"""
Unit tests for consent management system.

Tests:
- Consent table creation
- Grant consent
- Revoke consent
- Verify consent
- Consent audit trail
- Grace period handling
"""

import pytest
import tempfile
import os
from datetime import datetime, timedelta
from pathlib import Path

from guardrails.consent import (
    ConsentStatus, ConsentScope, ConsentRecord, ConsentAuditEntry,
    create_consent_tables, grant_consent, revoke_consent,
    get_consent, verify_consent, get_consent_audit_trail,
    get_all_consents_for_user
)


@pytest.fixture
def temp_db():
    """Create temporary database for testing."""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    # Create tables
    create_consent_tables(path)
    
    yield path
    
    # Cleanup
    os.unlink(path)


class TestConsentTables:
    """Test consent table creation."""
    
    def test_create_consent_tables(self, temp_db):
        """Test that consent tables are created."""
        # Tables should already be created by fixture
        # Just verify by trying to insert
        grant_consent("TEST_USER", temp_db, ConsentScope.ALL)
        
        consent = get_consent("TEST_USER", temp_db, ConsentScope.ALL)
        assert consent is not None
        assert consent.status == ConsentStatus.ACTIVE


class TestGrantConsent:
    """Test granting consent."""
    
    def test_grant_consent_basic(self, temp_db):
        """Test basic consent granting."""
        consent = grant_consent("TEST_USER", temp_db, ConsentScope.ALL)
        
        assert consent.user_id == "TEST_USER"
        assert consent.status == ConsentStatus.ACTIVE
        assert consent.scope == ConsentScope.ALL
        assert consent.granted_at is not None
    
    def test_grant_consent_with_expiration(self, temp_db):
        """Test granting consent with expiration."""
        expires_at = datetime.now() + timedelta(days=30)
        consent = grant_consent("TEST_USER", temp_db, ConsentScope.ALL, expires_at=expires_at)
        
        assert consent.expires_at == expires_at
    
    def test_grant_consent_creates_audit_trail(self, temp_db):
        """Test that granting consent creates audit trail."""
        grant_consent("TEST_USER", temp_db, ConsentScope.ALL)
        
        audit_trail = get_consent_audit_trail("TEST_USER", temp_db)
        assert len(audit_trail) > 0
        assert audit_trail[0].action == 'granted'
        assert audit_trail[0].new_status == ConsentStatus.ACTIVE


class TestRevokeConsent:
    """Test revoking consent."""
    
    def test_revoke_consent_all_scopes(self, temp_db):
        """Test revoking all consent scopes."""
        grant_consent("TEST_USER", temp_db, ConsentScope.ALL)
        
        revoked = revoke_consent("TEST_USER", temp_db)
        assert len(revoked) > 0
        
        consent = get_consent("TEST_USER", temp_db, ConsentScope.ALL)
        assert consent.status == ConsentStatus.REVOKED
    
    def test_revoke_consent_specific_scope(self, temp_db):
        """Test revoking specific consent scope."""
        grant_consent("TEST_USER", temp_db, ConsentScope.RECOMMENDATIONS)
        grant_consent("TEST_USER", temp_db, ConsentScope.PERSONALIZED_OFFERS)
        
        revoked = revoke_consent("TEST_USER", temp_db, scope=ConsentScope.RECOMMENDATIONS)
        assert len(revoked) == 1
        assert revoked[0].scope == ConsentScope.RECOMMENDATIONS
        
        # Check that other scope is still active
        consent_offers = get_consent("TEST_USER", temp_db, ConsentScope.PERSONALIZED_OFFERS)
        assert consent_offers.status == ConsentStatus.ACTIVE
    
    def test_revoke_consent_creates_audit_trail(self, temp_db):
        """Test that revoking consent creates audit trail."""
        grant_consent("TEST_USER", temp_db, ConsentScope.ALL)
        revoke_consent("TEST_USER", temp_db)
        
        audit_trail = get_consent_audit_trail("TEST_USER", temp_db)
        assert len(audit_trail) >= 2
        assert any(entry.action == 'revoked' for entry in audit_trail)


class TestVerifyConsent:
    """Test consent verification."""
    
    def test_verify_consent_active(self, temp_db):
        """Test verifying active consent."""
        grant_consent("TEST_USER", temp_db, ConsentScope.ALL)
        
        is_consented, reason = verify_consent("TEST_USER", temp_db, ConsentScope.ALL)
        assert is_consented is True
        assert reason is None
    
    def test_verify_consent_revoked(self, temp_db):
        """Test verifying revoked consent."""
        grant_consent("TEST_USER", temp_db, ConsentScope.ALL)
        revoke_consent("TEST_USER", temp_db)
        
        is_consented, reason = verify_consent("TEST_USER", temp_db, ConsentScope.ALL)
        assert is_consented is False
        assert "revoked" in reason.lower()
    
    def test_verify_consent_grace_period(self, temp_db):
        """Test grace period after revocation."""
        grant_consent("TEST_USER", temp_db, ConsentScope.ALL)
        revoke_consent("TEST_USER", temp_db)
        
        # Should be within grace period (default 0 days = no grace period)
        is_consented, reason = verify_consent("TEST_USER", temp_db, ConsentScope.ALL, grace_period_days=0)
        assert is_consented is False
        
        # With grace period
        is_consented, reason = verify_consent("TEST_USER", temp_db, ConsentScope.ALL, grace_period_days=7)
        assert is_consented is True
        assert "grace period" in reason.lower()
    
    def test_verify_consent_expired(self, temp_db):
        """Test verifying expired consent."""
        expires_at = datetime.now() - timedelta(days=1)  # Expired yesterday
        grant_consent("TEST_USER", temp_db, ConsentScope.ALL, expires_at=expires_at)
        
        is_consented, reason = verify_consent("TEST_USER", temp_db, ConsentScope.ALL)
        assert is_consented is False
        assert "expired" in reason.lower()
    
    def test_verify_consent_no_record(self, temp_db):
        """Test verifying consent when no record exists."""
        is_consented, reason = verify_consent("NONEXISTENT_USER", temp_db, ConsentScope.ALL)
        assert is_consented is False
        assert "not found" in reason.lower()


class TestConsentAuditTrail:
    """Test consent audit trail."""
    
    def test_audit_trail_completeness(self, temp_db):
        """Test that audit trail captures all actions."""
        grant_consent("TEST_USER", temp_db, ConsentScope.ALL)
        revoke_consent("TEST_USER", temp_db)
        
        audit_trail = get_consent_audit_trail("TEST_USER", temp_db)
        assert len(audit_trail) >= 2
        
        actions = [entry.action for entry in audit_trail]
        assert 'granted' in actions
        assert 'revoked' in actions
    
    def test_audit_trail_ordering(self, temp_db):
        """Test that audit trail is ordered by timestamp."""
        grant_consent("TEST_USER", temp_db, ConsentScope.ALL)
        revoke_consent("TEST_USER", temp_db)
        
        audit_trail = get_consent_audit_trail("TEST_USER", temp_db)
        
        # Should be ordered by timestamp DESC (most recent first)
        timestamps = [entry.timestamp for entry in audit_trail]
        assert timestamps == sorted(timestamps, reverse=True)


class TestConsentIntegration:
    """Test consent integration with recommendation builder."""
    
    def test_recommendation_builder_respects_consent(self, temp_db):
        """Test that recommendation builder checks consent."""
        from personas.persona_prioritization import assign_personas_with_prioritization
        from recommend.recommendation_builder import build_recommendations
        
        # Try to build recommendations without consent
        persona_assignment = assign_personas_with_prioritization("CUST000001", temp_db)
        
        if persona_assignment.primary_persona:
            recommendations = build_recommendations(
                "CUST000001",
                temp_db,
                persona_assignment,
                check_consent=True
            )
            
            # Should return empty recommendations if no consent
            assert len(recommendations.education_items) == 0
            assert len(recommendations.partner_offers) == 0

