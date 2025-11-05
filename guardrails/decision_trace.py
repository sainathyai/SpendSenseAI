"""
Decision Trace Logging System for SpendSenseAI.

Creates audit trail for all recommendations:
- Decision trace structure (user, timestamp, window, signals, personas, recommendations)
- Trace generation at each decision point
- Data citation logging
- Confidence score tracking
- Operator review status
- Trace storage (JSON files or database)
- Trace retrieval API
"""

from typing import List, Dict, Optional, Any
from datetime import datetime, date
from dataclasses import dataclass, asdict
from enum import Enum
import json
from pathlib import Path
import sqlite3
from contextlib import contextmanager

from personas.persona_definition import PersonaAssignment, PersonaType
from recommend.recommendation_builder import RecommendationSet


class ReviewStatus(str, Enum):
    """Operator review status."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    FLAGGED = "flagged"
    OVERRIDDEN = "overridden"


@dataclass
class SignalTrace:
    """Trace of behavioral signals."""
    signal_type: str  # 'subscription', 'credit_utilization', 'savings', 'income'
    window_days: int
    metrics: Dict[str, Any]
    detected_at: datetime


@dataclass
class PersonaTrace:
    """Trace of persona assignment."""
    persona_type: PersonaType
    confidence_score: float
    supporting_data: Dict[str, Any]
    window_days: int
    assigned_at: datetime


@dataclass
class RecommendationTrace:
    """Trace of a single recommendation."""
    recommendation_id: str
    type: str  # 'education' or 'offer'
    title: str
    rationale: str
    data_citations: Dict[str, Any]
    priority: int


@dataclass
class DecisionTrace:
    """Complete decision trace for a recommendation set."""
    trace_id: str
    user_id: str
    timestamp: datetime
    analysis_window_30d: bool
    analysis_window_180d: bool
    
    # Behavioral signals
    signals: List[SignalTrace]
    
    # Persona assignments
    persona_assignment: PersonaAssignment
    
    # Recommendations
    recommendations: RecommendationSet
    
    # Operator review
    review_status: ReviewStatus = ReviewStatus.PENDING
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    review_notes: Optional[str] = None
    override_reason: Optional[str] = None


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


def create_decision_trace_tables(db_path: str) -> None:
    """
    Create decision trace tables in the database.
    
    Args:
        db_path: Path to SQLite database
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        
        # Decision trace table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS decision_traces (
                trace_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                analysis_window_30d INTEGER NOT NULL,
                analysis_window_180d INTEGER NOT NULL,
                review_status TEXT NOT NULL DEFAULT 'pending',
                reviewed_by TEXT,
                reviewed_at TIMESTAMP,
                review_notes TEXT,
                override_reason TEXT,
                trace_data TEXT NOT NULL
            )
        """)
        
        # Create indexes
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_decision_traces_user 
            ON decision_traces(user_id, timestamp)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_decision_traces_review 
            ON decision_traces(review_status, timestamp)
        """)
        
        conn.commit()


def create_decision_trace(
    user_id: str,
    db_path: str,
    signals: List[SignalTrace],
    persona_assignment: PersonaAssignment,
    recommendations: RecommendationSet,
    trace_id: Optional[str] = None
) -> DecisionTrace:
    """
    Create a decision trace for a recommendation set.
    
    Args:
        user_id: User ID
        db_path: Path to SQLite database
        signals: List of SignalTrace objects
        persona_assignment: PersonaAssignment object
        recommendations: RecommendationSet object
        trace_id: Optional trace ID (auto-generated if not provided)
        
    Returns:
        DecisionTrace object
    """
    if trace_id is None:
        timestamp = datetime.now()
        trace_id = f"TRACE-{user_id}-{timestamp.strftime('%Y%m%d%H%M%S')}"
    
    # Determine analysis windows used
    window_30d = persona_assignment.window_30d is not None
    window_180d = persona_assignment.window_180d is not None
    
    trace = DecisionTrace(
        trace_id=trace_id,
        user_id=user_id,
        timestamp=datetime.now(),
        analysis_window_30d=window_30d,
        analysis_window_180d=window_180d,
        signals=signals,
        persona_assignment=persona_assignment,
        recommendations=recommendations,
        review_status=ReviewStatus.PENDING
    )
    
    # Save to database
    save_decision_trace(trace, db_path)
    
    return trace


def save_decision_trace(trace: DecisionTrace, db_path: str) -> None:
    """
    Save decision trace to database.
    
    Args:
        trace: DecisionTrace object
        db_path: Path to SQLite database
    """
    # Serialize trace data
    trace_data = {
        'trace_id': trace.trace_id,
        'user_id': trace.user_id,
        'timestamp': trace.timestamp.isoformat(),
        'analysis_window_30d': trace.analysis_window_30d,
        'analysis_window_180d': trace.analysis_window_180d,
        'signals': [
            {
                'signal_type': s.signal_type,
                'window_days': s.window_days,
                'metrics': s.metrics,
                'detected_at': s.detected_at.isoformat()
            }
            for s in trace.signals
        ],
        'persona_assignment': {
            'primary_persona': {
                'persona_type': trace.persona_assignment.primary_persona.persona_type.value if trace.persona_assignment.primary_persona else None,
                'confidence_score': trace.persona_assignment.primary_persona.confidence_score if trace.persona_assignment.primary_persona else None,
                'supporting_data': trace.persona_assignment.primary_persona.supporting_data if trace.persona_assignment.primary_persona else {}
            } if trace.persona_assignment.primary_persona else None,
            'secondary_persona': {
                'persona_type': trace.persona_assignment.secondary_persona.persona_type.value if trace.persona_assignment.secondary_persona else None,
                'confidence_score': trace.persona_assignment.secondary_persona.confidence_score if trace.persona_assignment.secondary_persona else None,
                'supporting_data': trace.persona_assignment.secondary_persona.supporting_data if trace.persona_assignment.secondary_persona else {}
            } if trace.persona_assignment.secondary_persona else None,
            'window_30d': {
                'persona_type': trace.persona_assignment.window_30d.persona_type.value if trace.persona_assignment.window_30d else None,
                'confidence_score': trace.persona_assignment.window_30d.confidence_score if trace.persona_assignment.window_30d else None,
                'supporting_data': trace.persona_assignment.window_30d.supporting_data if trace.persona_assignment.window_30d else {}
            } if trace.persona_assignment.window_30d else None,
            'window_180d': {
                'persona_type': trace.persona_assignment.window_180d.persona_type.value if trace.persona_assignment.window_180d else None,
                'confidence_score': trace.persona_assignment.window_180d.confidence_score if trace.persona_assignment.window_180d else None,
                'supporting_data': trace.persona_assignment.window_180d.supporting_data if trace.persona_assignment.window_180d else {}
            } if trace.persona_assignment.window_180d else None
        },
        'recommendations': {
            'customer_id': trace.recommendations.customer_id,
            'generated_at': trace.recommendations.generated_at.isoformat(),
            'education_items': [
                {
                    'recommendation_id': rec.recommendation_id,
                    'type': rec.type,
                    'title': rec.title,
                    'description': rec.description,
                    'rationale': rec.rationale,
                    'content_id': rec.content_id,
                    'priority': rec.priority,
                    'data_citations': rec.data_citations
                }
                for rec in trace.recommendations.education_items
            ],
            'partner_offers': [
                {
                    'recommendation_id': rec.recommendation_id,
                    'type': rec.type,
                    'title': rec.title,
                    'description': rec.description,
                    'rationale': rec.rationale,
                    'offer_id': rec.offer_id,
                    'priority': rec.priority,
                    'data_citations': rec.data_citations
                }
                for rec in trace.recommendations.partner_offers
            ]
        },
        'review_status': trace.review_status.value,
        'reviewed_by': trace.reviewed_by,
        'reviewed_at': trace.reviewed_at.isoformat() if trace.reviewed_at else None,
        'review_notes': trace.review_notes,
        'override_reason': trace.override_reason
    }
    
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO decision_traces 
            (trace_id, user_id, timestamp, analysis_window_30d, analysis_window_180d,
             review_status, reviewed_by, reviewed_at, review_notes, override_reason, trace_data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            trace.trace_id,
            trace.user_id,
            trace.timestamp.isoformat(),
            1 if trace.analysis_window_30d else 0,
            1 if trace.analysis_window_180d else 0,
            trace.review_status.value,
            trace.reviewed_by,
            trace.reviewed_at.isoformat() if trace.reviewed_at else None,
            trace.review_notes,
            trace.override_reason,
            json.dumps(trace_data)
        ))
        
        conn.commit()


def get_decision_trace(trace_id: str, db_path: str) -> Optional[DecisionTrace]:
    """
    Get decision trace by ID.
    
    Args:
        trace_id: Trace ID
        db_path: Path to SQLite database
        
    Returns:
        DecisionTrace object or None if not found
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT trace_id, trace_data
            FROM decision_traces
            WHERE trace_id = ?
        """, (trace_id,))
        
        row = cursor.fetchone()
        
        if not row:
            return None
        
        # Deserialize trace data
        trace_data = json.loads(row['trace_data'])
        
        # Reconstruct DecisionTrace object
        # (This is a simplified version - full reconstruction would require
        # importing all the related classes and reconstructing them)
        # For now, we'll return the trace data as a dictionary
        
        return trace_data


def get_decision_traces_for_user(
    user_id: str,
    db_path: str,
    limit: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Get all decision traces for a user.
    
    Args:
        user_id: User ID
        db_path: Path to SQLite database
        limit: Optional limit on number of traces
        
    Returns:
        List of trace data dictionaries
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        
        query = """
            SELECT trace_id, trace_data, timestamp, review_status
            FROM decision_traces
            WHERE user_id = ?
            ORDER BY timestamp DESC
        """
        
        if limit:
            query += f" LIMIT {limit}"
        
        cursor.execute(query, (user_id,))
        
        rows = cursor.fetchall()
        
        traces = []
        for row in rows:
            trace_data = json.loads(row['trace_data'])
            trace_data['trace_id'] = row['trace_id']
            trace_data['timestamp'] = row['timestamp']
            trace_data['review_status'] = row['review_status']
            traces.append(trace_data)
        
        return traces


def get_pending_reviews(
    db_path: str,
    limit: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Get all pending reviews for operator dashboard.
    
    Args:
        db_path: Path to SQLite database
        limit: Optional limit on number of traces
        
    Returns:
        List of trace data dictionaries
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        
        query = """
            SELECT trace_id, user_id, timestamp, trace_data
            FROM decision_traces
            WHERE review_status = 'pending'
            ORDER BY timestamp DESC
        """
        
        if limit:
            query += f" LIMIT {limit}"
        
        cursor.execute(query)
        
        rows = cursor.fetchall()
        
        traces = []
        for row in rows:
            trace_data = json.loads(row['trace_data'])
            trace_data['trace_id'] = row['trace_id']
            trace_data['user_id'] = row['user_id']
            trace_data['timestamp'] = row['timestamp']
            traces.append(trace_data)
        
        return traces


def update_review_status(
    trace_id: str,
    db_path: str,
    review_status: ReviewStatus,
    reviewed_by: str,
    review_notes: Optional[str] = None,
    override_reason: Optional[str] = None
) -> bool:
    """
    Update review status for a decision trace.
    
    Args:
        trace_id: Trace ID
        db_path: Path to SQLite database
        review_status: New review status
        reviewed_by: Operator ID who reviewed
        review_notes: Optional review notes
        override_reason: Optional override reason
        
    Returns:
        True if updated successfully, False otherwise
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        
        # Get existing trace data
        cursor.execute("""
            SELECT trace_data
            FROM decision_traces
            WHERE trace_id = ?
        """, (trace_id,))
        
        row = cursor.fetchone()
        
        if not row:
            return False
        
        # Update trace data
        trace_data = json.loads(row['trace_data'])
        trace_data['review_status'] = review_status.value
        trace_data['reviewed_by'] = reviewed_by
        trace_data['reviewed_at'] = datetime.now().isoformat()
        trace_data['review_notes'] = review_notes
        trace_data['override_reason'] = override_reason
        
        # Update database
        cursor.execute("""
            UPDATE decision_traces
            SET review_status = ?, reviewed_by = ?, reviewed_at = ?,
                review_notes = ?, override_reason = ?, trace_data = ?
            WHERE trace_id = ?
        """, (
            review_status.value,
            reviewed_by,
            datetime.now().isoformat(),
            review_notes,
            override_reason,
            json.dumps(trace_data),
            trace_id
        ))
        
        conn.commit()
        
        return True


def export_trace_to_json(trace: DecisionTrace, output_path: str) -> None:
    """
    Export decision trace to JSON file.
    
    Args:
        trace: DecisionTrace object
        output_path: Path to output JSON file
    """
    trace_dict = asdict(trace)
    
    # Convert enums and datetime objects to strings
    trace_dict['timestamp'] = trace.timestamp.isoformat()
    trace_dict['review_status'] = trace.review_status.value
    
    if trace.reviewed_at:
        trace_dict['reviewed_at'] = trace.reviewed_at.isoformat()
    
    for signal in trace_dict['signals']:
        signal['detected_at'] = signal['detected_at'].isoformat()
        if 'persona_type' in signal:
            signal['persona_type'] = signal['persona_type'].value
    
    with open(output_path, 'w') as f:
        json.dump(trace_dict, f, indent=2, default=str)

