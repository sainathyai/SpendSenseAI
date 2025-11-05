"""
Unit tests for decision trace logging system.

Tests:
- Decision trace table creation
- Create decision trace
- Save and retrieve traces
- Review status updates
- Pending reviews retrieval
"""

import pytest
import tempfile
import os
import json
from datetime import datetime
from pathlib import Path

from guardrails.decision_trace import (
    ReviewStatus, SignalTrace, DecisionTrace,
    create_decision_trace_tables, create_decision_trace,
    save_decision_trace, get_decision_trace,
    get_decision_traces_for_user, get_pending_reviews,
    update_review_status, export_trace_to_json
)
from personas.persona_definition import PersonaAssignment, PersonaMatch, PersonaType
from recommend.recommendation_builder import RecommendationSet, RecommendationItem


@pytest.fixture
def temp_db():
    """Create temporary database for testing."""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    # Create tables
    create_decision_trace_tables(path)
    
    yield path
    
    # Cleanup
    os.unlink(path)


@pytest.fixture
def sample_persona_assignment():
    """Create sample persona assignment."""
    persona_match = PersonaMatch(
        persona_type=PersonaType.HIGH_UTILIZATION,
        confidence_score=0.85,
        supporting_data={'utilization': 0.68}
    )
    
    return PersonaAssignment(
        primary_persona=persona_match,
        secondary_persona=None,
        window_30d=persona_match,
        window_180d=persona_match
    )


@pytest.fixture
def sample_recommendations():
    """Create sample recommendations."""
    return RecommendationSet(
        customer_id="TEST_USER",
        persona_assignment=PersonaAssignment(
            primary_persona=None,
            secondary_persona=None,
            window_30d=None,
            window_180d=None
        ),
        education_items=[
            RecommendationItem(
                recommendation_id="REC-001",
                type="education",
                title="Test Content",
                description="Test description",
                rationale="Test rationale",
                content_id="CONTENT-001",
                priority=1
            )
        ],
        partner_offers=[],
        generated_at=datetime.now().date()
    )


@pytest.fixture
def sample_signals():
    """Create sample signals."""
    return [
        SignalTrace(
            signal_type="credit_utilization",
            window_days=30,
            metrics={"utilization": 0.68, "balance": 3400.0},
            detected_at=datetime.now()
        )
    ]


class TestDecisionTraceTables:
    """Test decision trace table creation."""
    
    def test_create_decision_trace_tables(self, temp_db):
        """Test that decision trace tables are created."""
        # Tables should already be created by fixture
        # Just verify by trying to insert
        signals = []
        persona_assignment = PersonaAssignment(
            primary_persona=None,
            secondary_persona=None,
            window_30d=None,
            window_180d=None
        )
        recommendations = RecommendationSet(
            customer_id="TEST_USER",
            persona_assignment=persona_assignment,
            education_items=[],
            partner_offers=[],
            generated_at=datetime.now().date()
        )
        
        trace = create_decision_trace(
            "TEST_USER",
            temp_db,
            signals,
            persona_assignment,
            recommendations
        )
        
        assert trace.trace_id is not None


class TestCreateDecisionTrace:
    """Test creating decision traces."""
    
    def test_create_decision_trace(self, temp_db, sample_signals, sample_persona_assignment, sample_recommendations):
        """Test creating a decision trace."""
        sample_recommendations.customer_id = "TEST_USER"
        sample_recommendations.persona_assignment = sample_persona_assignment
        
        trace = create_decision_trace(
            "TEST_USER",
            temp_db,
            sample_signals,
            sample_persona_assignment,
            sample_recommendations
        )
        
        assert trace.user_id == "TEST_USER"
        assert trace.trace_id is not None
        assert len(trace.signals) == len(sample_signals)
        assert trace.review_status == ReviewStatus.PENDING
    
    def test_create_decision_trace_with_custom_id(self, temp_db, sample_signals, sample_persona_assignment, sample_recommendations):
        """Test creating a decision trace with custom ID."""
        trace_id = "CUSTOM-TRACE-001"
        
        trace = create_decision_trace(
            "TEST_USER",
            temp_db,
            sample_signals,
            sample_persona_assignment,
            sample_recommendations,
            trace_id=trace_id
        )
        
        assert trace.trace_id == trace_id


class TestRetrieveDecisionTrace:
    """Test retrieving decision traces."""
    
    def test_get_decision_trace(self, temp_db, sample_signals, sample_persona_assignment, sample_recommendations):
        """Test retrieving a decision trace."""
        sample_recommendations.customer_id = "TEST_USER"
        sample_recommendations.persona_assignment = sample_persona_assignment
        
        trace = create_decision_trace(
            "TEST_USER",
            temp_db,
            sample_signals,
            sample_persona_assignment,
            sample_recommendations
        )
        
        retrieved = get_decision_trace(trace.trace_id, temp_db)
        
        assert retrieved is not None
        assert retrieved['trace_id'] == trace.trace_id
        assert retrieved['user_id'] == "TEST_USER"
    
    def test_get_decision_traces_for_user(self, temp_db, sample_signals, sample_persona_assignment, sample_recommendations):
        """Test retrieving all traces for a user."""
        sample_recommendations.customer_id = "TEST_USER"
        sample_recommendations.persona_assignment = sample_persona_assignment
        
        # Create multiple traces
        for i in range(3):
            create_decision_trace(
                "TEST_USER",
                temp_db,
                sample_signals,
                sample_persona_assignment,
                sample_recommendations
            )
        
        traces = get_decision_traces_for_user("TEST_USER", temp_db)
        
        assert len(traces) >= 3
        assert all(t['user_id'] == "TEST_USER" for t in traces)


class TestReviewStatus:
    """Test review status updates."""
    
    def test_update_review_status(self, temp_db, sample_signals, sample_persona_assignment, sample_recommendations):
        """Test updating review status."""
        sample_recommendations.customer_id = "TEST_USER"
        sample_recommendations.persona_assignment = sample_persona_assignment
        
        trace = create_decision_trace(
            "TEST_USER",
            temp_db,
            sample_signals,
            sample_persona_assignment,
            sample_recommendations
        )
        
        success = update_review_status(
            trace.trace_id,
            temp_db,
            ReviewStatus.APPROVED,
            reviewed_by="OPERATOR001",
            review_notes="Looks good"
        )
        
        assert success is True
        
        retrieved = get_decision_trace(trace.trace_id, temp_db)
        assert retrieved['review_status'] == ReviewStatus.APPROVED.value
        assert retrieved['reviewed_by'] == "OPERATOR001"
    
    def test_get_pending_reviews(self, temp_db, sample_signals, sample_persona_assignment, sample_recommendations):
        """Test getting pending reviews."""
        sample_recommendations.customer_id = "TEST_USER"
        sample_recommendations.persona_assignment = sample_persona_assignment
        
        # Create traces with different statuses
        trace1 = create_decision_trace(
            "USER1",
            temp_db,
            sample_signals,
            sample_persona_assignment,
            sample_recommendations
        )
        
        trace2 = create_decision_trace(
            "USER2",
            temp_db,
            sample_signals,
            sample_persona_assignment,
            sample_recommendations
        )
        
        # Approve one
        update_review_status(trace1.trace_id, temp_db, ReviewStatus.APPROVED, "OPERATOR001")
        
        # Get pending reviews
        pending = get_pending_reviews(temp_db)
        
        assert len(pending) >= 1
        assert all(t['review_status'] == ReviewStatus.PENDING.value for t in pending)


class TestExportTrace:
    """Test exporting traces."""
    
    def test_export_trace_to_json(self, temp_db, sample_signals, sample_persona_assignment, sample_recommendations, tmp_path):
        """Test exporting trace to JSON."""
        sample_recommendations.customer_id = "TEST_USER"
        sample_recommendations.persona_assignment = sample_persona_assignment
        
        trace = create_decision_trace(
            "TEST_USER",
            temp_db,
            sample_signals,
            sample_persona_assignment,
            sample_recommendations
        )
        
        output_path = tmp_path / "trace.json"
        export_trace_to_json(trace, str(output_path))
        
        assert output_path.exists()
        
        with open(output_path) as f:
            data = json.load(f)
        
        assert data['trace_id'] == trace.trace_id
        assert data['user_id'] == "TEST_USER"

