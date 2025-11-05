"""
Test consent management system end-to-end.

Tests the complete consent flow:
Grant → Verify → Revoke → Verify → Grace Period
"""

from guardrails.consent import (
    create_consent_tables, grant_consent, revoke_consent,
    verify_consent, get_consent, get_consent_audit_trail,
    ConsentScope, ConsentStatus
)
from datetime import datetime, timedelta

db_path = 'data/spendsense.db'
sample_user = 'CUST000001'

print("="*60)
print("Testing Consent Management System")
print("="*60)
print()

# Step 1: Create consent tables
print("[STEP 1] Creating consent tables...")
create_consent_tables(db_path)
print("   [SUCCESS] Consent tables created")

print()

# Step 2: Grant consent
print("[STEP 2] Granting consent...")
consent = grant_consent(
    sample_user,
    db_path,
    scope=ConsentScope.ALL,
    ip_address="192.168.1.1",
    user_agent="Mozilla/5.0",
    notes="Initial consent granted"
)
print(f"   User ID: {consent.user_id}")
print(f"   Status: {consent.status.value}")
print(f"   Scope: {consent.scope.value}")
print(f"   Granted At: {consent.granted_at}")

print()

# Step 3: Verify consent
print("[STEP 3] Verifying consent...")
is_consented, reason = verify_consent(sample_user, db_path, ConsentScope.ALL)
print(f"   Is Consented: {is_consented}")
if reason:
    print(f"   Reason: {reason}")

print()

# Step 4: Get consent record
print("[STEP 4] Retrieving consent record...")
consent_record = get_consent(sample_user, db_path, ConsentScope.ALL)
if consent_record:
    print(f"   Status: {consent_record.status.value}")
    print(f"   Scope: {consent_record.scope.value}")
    print(f"   Granted At: {consent_record.granted_at}")
    print(f"   IP Address: {consent_record.ip_address}")

print()

# Step 5: Revoke consent
print("[STEP 5] Revoking consent...")
revoked = revoke_consent(
    sample_user,
    db_path,
    scope=ConsentScope.ALL,
    ip_address="192.168.1.1",
    notes="User requested revocation"
)
print(f"   Revoked {len(revoked)} consent record(s)")

print()

# Step 6: Verify after revocation
print("[STEP 6] Verifying consent after revocation...")
is_consented, reason = verify_consent(sample_user, db_path, ConsentScope.ALL)
print(f"   Is Consented: {is_consented}")
if reason:
    print(f"   Reason: {reason}")

print()

# Step 7: Check grace period
print("[STEP 7] Testing grace period...")
is_consented, reason = verify_consent(
    sample_user,
    db_path,
    ConsentScope.ALL,
    grace_period_days=7
)
print(f"   Is Consented (with 7-day grace period): {is_consented}")
if reason:
    print(f"   Reason: {reason}")

print()

# Step 8: Audit trail
print("[STEP 8] Retrieving audit trail...")
audit_trail = get_consent_audit_trail(sample_user, db_path)
print(f"   Total audit entries: {len(audit_trail)}")
for i, entry in enumerate(audit_trail[:5], 1):  # Show first 5 entries
    print(f"   {i}. {entry.action} at {entry.timestamp}")
    if entry.previous_status:
        print(f"      Previous: {entry.previous_status.value}")
    if entry.new_status:
        print(f"      New: {entry.new_status.value}")

print("\n" + "="*60)
print("[SUCCESS] Consent management system tested successfully!")
print("="*60)

