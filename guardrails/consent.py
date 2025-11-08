"""
Consent Management System for SpendSenseAI.

Tracks and enforces user consent for recommendations:
- Consent data model (user_id, status, timestamp, scope)
- Consent states: pending, active, revoked
- Opt-in/opt-out functions with timestamp logging
- Consent verification before recommendations
- Consent audit trail
- Grace period handling
"""

from typing import Optional, List, Dict
from datetime import datetime, date, timedelta
from dataclasses import dataclass
from enum import Enum
import sqlite3
from contextlib import contextmanager


@contextmanager
def get_connection(db_path: str):
    """Get database connection context manager."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


class ConsentStatus(str, Enum):
    """Consent status states."""
    PENDING = "pending"
    ACTIVE = "active"
    REVOKED = "revoked"
    EXPIRED = "expired"


class ConsentScope(str, Enum):
    """Consent scope types."""
    RECOMMENDATIONS = "recommendations"
    PERSONALIZED_OFFERS = "personalized_offers"
    EDUCATIONAL_CONTENT = "educational_content"
    ALL = "all"  # Full consent for all features


@dataclass
class ConsentRecord:
    """Consent record for a user."""
    user_id: str
    status: ConsentStatus
    scope: ConsentScope
    granted_at: datetime
    revoked_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    notes: Optional[str] = None


@dataclass
class ConsentAuditEntry:
    """Audit trail entry for consent changes."""
    user_id: str
    action: str  # 'granted', 'revoked', 'expired', 'verified'
    timestamp: datetime
    previous_status: Optional[ConsentStatus] = None
    new_status: Optional[ConsentStatus] = None
    scope: Optional[ConsentScope] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    notes: Optional[str] = None


def create_consent_tables(db_path: str) -> None:
    """
    Create consent management tables in the database.
    
    Args:
        db_path: Path to SQLite database
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        
        # Consent table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS consent (
                user_id TEXT NOT NULL,
                status TEXT NOT NULL,
                scope TEXT NOT NULL,
                granted_at TIMESTAMP NOT NULL,
                revoked_at TIMESTAMP,
                expires_at TIMESTAMP,
                ip_address TEXT,
                user_agent TEXT,
                notes TEXT,
                PRIMARY KEY (user_id, scope)
            )
        """)
        
        # Consent audit trail table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS consent_audit (
                audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                action TEXT NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                previous_status TEXT,
                new_status TEXT,
                scope TEXT,
                ip_address TEXT,
                user_agent TEXT,
                notes TEXT
            )
        """)
        
        # Create indexes
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_consent_user_status 
            ON consent(user_id, status)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_consent_audit_user 
            ON consent_audit(user_id, timestamp)
        """)
        
        conn.commit()


def grant_consent(
    user_id: str,
    db_path: str,
    scope: ConsentScope = ConsentScope.ALL,
    expires_at: Optional[datetime] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    notes: Optional[str] = None
) -> ConsentRecord:
    """
    Grant consent to a user.
    
    Args:
        user_id: User ID
        db_path: Path to SQLite database
        scope: Consent scope (default: ALL)
        expires_at: Optional expiration datetime
        ip_address: Optional IP address
        user_agent: Optional user agent string
        notes: Optional notes
        
    Returns:
        ConsentRecord object
    """
    granted_at = datetime.now()
    
    # Get previous consent status for audit trail
    previous_record = get_consent(user_id, db_path, scope)
    previous_status = previous_record.status if previous_record else None
    
    # Create new consent record
    consent_record = ConsentRecord(
        user_id=user_id,
        status=ConsentStatus.ACTIVE,
        scope=scope,
        granted_at=granted_at,
        expires_at=expires_at,
        ip_address=ip_address,
        user_agent=user_agent,
        notes=notes
    )
    
    # Save to database
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO consent 
            (user_id, status, scope, granted_at, revoked_at, expires_at, ip_address, user_agent, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            ConsentStatus.ACTIVE.value,
            scope.value,
            granted_at.isoformat(),
            None,
            expires_at.isoformat() if expires_at else None,
            ip_address,
            user_agent,
            notes
        ))
        
        # Log audit trail
        cursor.execute("""
            INSERT INTO consent_audit 
            (user_id, action, timestamp, previous_status, new_status, scope, ip_address, user_agent, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            'granted',
            granted_at.isoformat(),
            previous_status.value if previous_status else None,
            ConsentStatus.ACTIVE.value,
            scope.value,
            ip_address,
            user_agent,
            notes
        ))
        
        conn.commit()
    
    return consent_record


def revoke_consent(
    user_id: str,
    db_path: str,
    scope: Optional[ConsentScope] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    notes: Optional[str] = None
) -> List[ConsentRecord]:
    """
    Revoke consent for a user (all scopes or specific scope).
    
    Args:
        user_id: User ID
        db_path: Path to SQLite database
        scope: Optional specific scope to revoke (if None, revokes all)
        ip_address: Optional IP address
        user_agent: Optional user agent string
        notes: Optional notes
        
    Returns:
        List of revoked ConsentRecord objects
    """
    revoked_at = datetime.now()
    revoked_records = []
    
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        
        # Get existing consent records
        if scope:
            cursor.execute("""
                SELECT user_id, status, scope, granted_at, revoked_at, expires_at, 
                       ip_address, user_agent, notes
                FROM consent
                WHERE user_id = ? AND scope = ? AND status = ?
            """, (user_id, scope.value, ConsentStatus.ACTIVE.value))
        else:
            cursor.execute("""
                SELECT user_id, status, scope, granted_at, revoked_at, expires_at, 
                       ip_address, user_agent, notes
            FROM consent
            WHERE user_id = ? AND status = ?
        """, (user_id, ConsentStatus.ACTIVE.value))
        
        rows = cursor.fetchall()
        
        for row in rows:
            previous_status = ConsentStatus(row['status'])
            scope_value = ConsentScope(row['scope'])
            granted_at = datetime.fromisoformat(row['granted_at'])
            
            # Update consent record
            cursor.execute("""
                UPDATE consent
                SET status = ?, revoked_at = ?
                WHERE user_id = ? AND scope = ?
            """, (
                ConsentStatus.REVOKED.value,
                revoked_at.isoformat(),
                user_id,
                scope_value.value
            ))
            
            # Create revoked record
            revoked_record = ConsentRecord(
                user_id=user_id,
                status=ConsentStatus.REVOKED,
                scope=scope_value,
                granted_at=granted_at,
                revoked_at=revoked_at,
                ip_address=row['ip_address'],
                user_agent=row['user_agent'],
                notes=row['notes']
            )
            revoked_records.append(revoked_record)
            
            # Log audit trail
            cursor.execute("""
                INSERT INTO consent_audit 
                (user_id, action, timestamp, previous_status, new_status, scope, ip_address, user_agent, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                'revoked',
                revoked_at.isoformat(),
                previous_status.value,
                ConsentStatus.REVOKED.value,
                scope_value.value,
                ip_address,
                user_agent,
                notes
            ))
        
        conn.commit()
    
    return revoked_records


def get_consent(
    user_id: str,
    db_path: str,
    scope: ConsentScope = ConsentScope.ALL
) -> Optional[ConsentRecord]:
    """
    Get consent record for a user.
    
    Args:
        user_id: User ID
        db_path: Path to SQLite database
        scope: Consent scope to check
        
    Returns:
        ConsentRecord or None if not found
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT user_id, status, scope, granted_at, revoked_at, expires_at, 
                   ip_address, user_agent, notes
            FROM consent
            WHERE user_id = ? AND scope = ?
        """, (user_id, scope.value))
        
        row = cursor.fetchone()
        
        if not row:
            return None
        
        # Check if expired
        status = ConsentStatus(row['status'])
        expires_at = None
        if row['expires_at']:
            expires_at = datetime.fromisoformat(row['expires_at'])
            if expires_at < datetime.now() and status == ConsentStatus.ACTIVE:
                # Update status to expired
                cursor.execute("""
                    UPDATE consent
                    SET status = ?
                    WHERE user_id = ? AND scope = ?
                """, (ConsentStatus.EXPIRED.value, user_id, scope.value))
                
                # Log audit trail
                cursor.execute("""
                    INSERT INTO consent_audit 
                    (user_id, action, timestamp, previous_status, new_status, scope)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    user_id,
                    'expired',
                    datetime.now().isoformat(),
                    ConsentStatus.ACTIVE.value,
                    ConsentStatus.EXPIRED.value,
                    scope.value
                ))
                
                conn.commit()
                status = ConsentStatus.EXPIRED
        
        return ConsentRecord(
            user_id=row['user_id'],
            status=status,
            scope=ConsentScope(row['scope']),
            granted_at=datetime.fromisoformat(row['granted_at']),
            revoked_at=datetime.fromisoformat(row['revoked_at']) if row['revoked_at'] else None,
            expires_at=expires_at,
            ip_address=row['ip_address'],
            user_agent=row['user_agent'],
            notes=row['notes']
        )


def verify_consent(
    user_id: str,
    db_path: str,
    required_scope: ConsentScope = ConsentScope.ALL,
    grace_period_days: int = 0
) -> tuple[bool, Optional[str]]:
    """
    Verify if user has active consent.
    
    Args:
        user_id: User ID
        db_path: Path to SQLite database
        required_scope: Required consent scope
        grace_period_days: Grace period in days (allows recommendations for N days after revocation)
        
    Returns:
        Tuple of (is_consented, reason)
        - is_consented: True if consent is active or within grace period
        - reason: Optional reason string if consent is not valid
    """
    # Check for specific scope
    consent_record = get_consent(user_id, db_path, required_scope)
    
    # If specific scope not found, check ALL scope
    if not consent_record and required_scope != ConsentScope.ALL:
        consent_record = get_consent(user_id, db_path, ConsentScope.ALL)
    
    if not consent_record:
        return False, "No consent record found"
    
    # Check status
    if consent_record.status == ConsentStatus.ACTIVE:
        # Check expiration
        if consent_record.expires_at and consent_record.expires_at < datetime.now():
            return False, "Consent has expired"
        return True, None
    
    elif consent_record.status == ConsentStatus.REVOKED:
        # Check grace period
        if consent_record.revoked_at and grace_period_days > 0:
            grace_period_end = consent_record.revoked_at + timedelta(days=grace_period_days)
            if datetime.now() <= grace_period_end:
                return True, f"Within grace period (expires {grace_period_end})"
        
        return False, "Consent has been revoked"
    
    elif consent_record.status == ConsentStatus.EXPIRED:
        return False, "Consent has expired"
    
    elif consent_record.status == ConsentStatus.PENDING:
        return False, "Consent is pending"
    
    return False, "Unknown consent status"


def get_consent_audit_trail(
    user_id: str,
    db_path: str,
    limit: Optional[int] = None
) -> List[ConsentAuditEntry]:
    """
    Get consent audit trail for a user.
    
    Args:
        user_id: User ID
        db_path: Path to SQLite database
        limit: Optional limit on number of entries
        
    Returns:
        List of ConsentAuditEntry objects
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        
        query = """
            SELECT user_id, action, timestamp, previous_status, new_status, 
                   scope, ip_address, user_agent, notes
            FROM consent_audit
            WHERE user_id = ?
            ORDER BY timestamp DESC
        """
        
        if limit:
            query += f" LIMIT {limit}"
        
        cursor.execute(query, (user_id,))
        
        rows = cursor.fetchall()
        
        audit_entries = []
        for row in rows:
            entry = ConsentAuditEntry(
                user_id=row['user_id'],
                action=row['action'],
                timestamp=datetime.fromisoformat(row['timestamp']),
                previous_status=ConsentStatus(row['previous_status']) if row['previous_status'] else None,
                new_status=ConsentStatus(row['new_status']) if row['new_status'] else None,
                scope=ConsentScope(row['scope']) if row['scope'] else None,
                ip_address=row['ip_address'],
                user_agent=row['user_agent'],
                notes=row['notes']
            )
            audit_entries.append(entry)
        
        return audit_entries


def get_all_consents_for_user(
    user_id: str,
    db_path: str
) -> List[ConsentRecord]:
    """
    Get all consent records for a user (all scopes).
    
    Args:
        user_id: User ID
        db_path: Path to SQLite database
        
    Returns:
        List of ConsentRecord objects
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT user_id, status, scope, granted_at, revoked_at, expires_at, 
                   ip_address, user_agent, notes
            FROM consent
            WHERE user_id = ?
            ORDER BY granted_at DESC
        """, (user_id,))
        
        rows = cursor.fetchall()
        
        consent_records = []
        for row in rows:
            status = ConsentStatus(row['status'])
            expires_at = None
            if row['expires_at']:
                expires_at = datetime.fromisoformat(row['expires_at'])
                if expires_at < datetime.now() and status == ConsentStatus.ACTIVE:
                    status = ConsentStatus.EXPIRED
            
            record = ConsentRecord(
                user_id=row['user_id'],
                status=status,
                scope=ConsentScope(row['scope']),
                granted_at=datetime.fromisoformat(row['granted_at']),
                revoked_at=datetime.fromisoformat(row['revoked_at']) if row['revoked_at'] else None,
                expires_at=expires_at,
                ip_address=row['ip_address'],
                user_agent=row['user_agent'],
                notes=row['notes']
            )
            consent_records.append(record)
        
        return consent_records

