"""
REST API Implementation for SpendSenseAI.

Provides service endpoints for all functionality:
- User management
- Consent management
- Profile endpoints
- Recommendation endpoints
- Feedback endpoints
- Operator endpoints
"""

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from enum import Enum

from personas.persona_prioritization import assign_personas_with_prioritization
from personas.persona_definition import PersonaAssignment, PersonaType
from recommend.recommendation_builder import build_recommendations, format_recommendations_for_api
from guardrails.consent import (
    grant_consent, revoke_consent, get_consent, verify_consent,
    get_consent_audit_trail, get_all_consents_for_user,
    ConsentScope, ConsentStatus
)
from guardrails.decision_trace import (
    get_decision_trace, get_decision_traces_for_user,
    get_pending_reviews, update_review_status,
    ReviewStatus, create_decision_trace_tables
)
from features.subscription_detection import detect_subscriptions_for_customer
from features.credit_utilization import analyze_credit_utilization_for_customer
from features.savings_pattern import analyze_savings_patterns_for_customer
from features.income_stability import analyze_income_stability_for_customer
from ingest.queries import get_accounts_by_customer

import os

# Database path
DB_PATH = os.getenv("SPENDSENSE_DB_PATH", "data/spendsense.db")

# Initialize FastAPI app
app = FastAPI(
    title="SpendSenseAI API",
    description="API for personalized financial education and recommendations",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# ============================================================================
# Request/Response Models
# ============================================================================

class UserCreate(BaseModel):
    """Request model for creating a user."""
    user_id: str
    email: Optional[str] = None
    name: Optional[str] = None


class UserResponse(BaseModel):
    """Response model for user."""
    user_id: str
    email: Optional[str] = None
    name: Optional[str] = None
    created_at: Optional[datetime] = None


class ConsentGrant(BaseModel):
    """Request model for granting consent."""
    user_id: str
    scope: str = "all"  # "all", "recommendations", "personalized_offers", "educational_content"
    expires_at: Optional[datetime] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    notes: Optional[str] = None


class ConsentResponse(BaseModel):
    """Response model for consent."""
    user_id: str
    status: str
    scope: str
    granted_at: datetime
    revoked_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None


class SignalResponse(BaseModel):
    """Response model for behavioral signal."""
    signal_type: str
    window_days: int
    metrics: Dict[str, Any]
    detected_at: datetime


class PersonaResponse(BaseModel):
    """Response model for persona."""
    persona_type: str
    confidence_score: float
    supporting_data: Dict[str, Any]


class ProfileResponse(BaseModel):
    """Response model for user profile."""
    user_id: str
    primary_persona: Optional[PersonaResponse] = None
    secondary_persona: Optional[PersonaResponse] = None
    window_30d: Optional[PersonaResponse] = None
    window_180d: Optional[PersonaResponse] = None
    signals: List[SignalResponse] = []
    generated_at: datetime


class RecommendationRequest(BaseModel):
    """Request model for recommendations."""
    estimated_income: Optional[float] = 0.0
    estimated_credit_score: Optional[int] = 700
    check_consent: bool = True
    grace_period_days: int = 0


class FeedbackCreate(BaseModel):
    """Request model for feedback."""
    user_id: str
    recommendation_id: Optional[str] = None
    feedback_type: str  # "helpful", "not_helpful", "irrelevant", "other"
    comment: Optional[str] = None
    rating: Optional[int] = Field(None, ge=1, le=5)


class ReviewUpdate(BaseModel):
    """Request model for updating review status."""
    review_status: str  # "approved", "rejected", "flagged", "overridden"
    reviewed_by: str
    review_notes: Optional[str] = None
    override_reason: Optional[str] = None


# ============================================================================
# Helper Functions
# ============================================================================

def get_db_path():
    """Get database path."""
    return DB_PATH


def get_signals_for_user(user_id: str, db_path: str) -> List[SignalResponse]:
    """Get all behavioral signals for a user."""
    signals = []
    
    # Subscription signals
    try:
        subscriptions, sub_metrics = detect_subscriptions_for_customer(user_id, db_path, window_days=90)
        if sub_metrics.get('subscription_count', 0) > 0:
            signals.append(SignalResponse(
                signal_type="subscription",
                window_days=90,
                metrics=sub_metrics,
                detected_at=datetime.now()
            ))
    except Exception:
        pass
    
    # Credit utilization signals
    try:
        card_metrics, agg_metrics = analyze_credit_utilization_for_customer(user_id, db_path, 30)
        if card_metrics:
            signals.append(SignalResponse(
                signal_type="credit_utilization",
                window_days=30,
                metrics={
                    'aggregate_utilization': agg_metrics.aggregate_utilization,
                    'total_monthly_interest': agg_metrics.total_monthly_interest,
                    'overdue_card_count': agg_metrics.overdue_card_count
                },
                detected_at=datetime.now()
            ))
    except Exception:
        pass
    
    # Savings signals
    try:
        savings_accounts, savings_metrics = analyze_savings_patterns_for_customer(user_id, db_path, 180)
        if savings_accounts:
            signals.append(SignalResponse(
                signal_type="savings",
                window_days=180,
                metrics={
                    'total_savings_balance': savings_metrics.total_savings_balance,
                    'overall_growth_rate': savings_metrics.overall_growth_rate,
                    'average_monthly_inflow': savings_metrics.average_monthly_inflow
                },
                detected_at=datetime.now()
            ))
    except Exception:
        pass
    
    # Income signals
    try:
        income_metrics = analyze_income_stability_for_customer(user_id, db_path, 180)
        signals.append(SignalResponse(
            signal_type="income",
            window_days=180,
            metrics={
                'median_pay_gap_days': income_metrics.median_pay_gap_days,
                'cash_flow_buffer_months': income_metrics.cash_flow_buffer_months,
                'income_variability': income_metrics.income_variability
            },
            detected_at=datetime.now()
        ))
    except Exception:
        pass
    
    return signals


def persona_to_response(persona_assignment: PersonaAssignment) -> Dict[str, Any]:
    """Convert persona assignment to response format."""
    def persona_match_to_response(match):
        if not match:
            return None
        return PersonaResponse(
            persona_type=match.persona_type.value,
            confidence_score=match.confidence_score,
            supporting_data=match.supporting_data
        )
    
    return {
        'primary_persona': persona_match_to_response(persona_assignment.primary_persona),
        'secondary_persona': persona_match_to_response(persona_assignment.secondary_persona),
        'window_30d': persona_match_to_response(persona_assignment.window_30d),
        'window_180d': persona_match_to_response(persona_assignment.window_180d)
    }


# ============================================================================
# User Management Endpoints
# ============================================================================

@app.post("/users", response_model=UserResponse, tags=["users"])
async def create_user(user: UserCreate):
    """Create a new user."""
    # In a real implementation, this would save to a users table
    # For now, we just return the user data
    return UserResponse(
        user_id=user.user_id,
        email=user.email,
        name=user.name,
        created_at=datetime.now()
    )


@app.get("/users/{user_id}", response_model=UserResponse, tags=["users"])
async def get_user(user_id: str):
    """Get user details."""
    # In a real implementation, this would query a users table
    # For now, we just return basic info
    return UserResponse(
        user_id=user_id,
        created_at=datetime.now()
    )


# ============================================================================
# Consent Endpoints
# ============================================================================

@app.post("/consent", response_model=ConsentResponse, tags=["consent"])
async def grant_user_consent(consent: ConsentGrant):
    """Grant consent to a user."""
    try:
        scope = ConsentScope(consent.scope.lower())
        consent_record = grant_consent(
            consent.user_id,
            DB_PATH,
            scope=scope,
            expires_at=consent.expires_at,
            ip_address=consent.ip_address,
            user_agent=consent.user_agent,
            notes=consent.notes
        )
        
        return ConsentResponse(
            user_id=consent_record.user_id,
            status=consent_record.status.value,
            scope=consent_record.scope.value,
            granted_at=consent_record.granted_at,
            revoked_at=consent_record.revoked_at,
            expires_at=consent_record.expires_at
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error granting consent: {str(e)}")


@app.delete("/consent/{user_id}", tags=["consent"])
async def revoke_user_consent(user_id: str, scope: Optional[str] = None):
    """Revoke consent for a user."""
    try:
        consent_scope = None
        if scope:
            consent_scope = ConsentScope(scope.lower())
        
        revoked = revoke_consent(user_id, DB_PATH, scope=consent_scope)
        
        return {
            "message": f"Revoked {len(revoked)} consent record(s)",
            "revoked_count": len(revoked)
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error revoking consent: {str(e)}")


@app.get("/consent/{user_id}", response_model=List[ConsentResponse], tags=["consent"])
async def get_user_consents(user_id: str):
    """Get all consent records for a user."""
    try:
        consents = get_all_consents_for_user(user_id, DB_PATH)
        
        return [
            ConsentResponse(
                user_id=c.user_id,
                status=c.status.value,
                scope=c.scope.value,
                granted_at=c.granted_at,
                revoked_at=c.revoked_at,
                expires_at=c.expires_at
            )
            for c in consents
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving consent: {str(e)}")


# ============================================================================
# Profile Endpoints
# ============================================================================

@app.get("/profile/{user_id}", response_model=ProfileResponse, tags=["profile"])
async def get_user_profile(user_id: str):
    """Get behavioral profile (signals + persona) for a user."""
    try:
        # Assign persona
        persona_assignment = assign_personas_with_prioritization(user_id, DB_PATH)
        
        # Get signals
        signals = get_signals_for_user(user_id, DB_PATH)
        
        # Convert persona to response
        persona_data = persona_to_response(persona_assignment)
        
        return ProfileResponse(
            user_id=user_id,
            primary_persona=persona_data['primary_persona'],
            secondary_persona=persona_data['secondary_persona'],
            window_30d=persona_data['window_30d'],
            window_180d=persona_data['window_180d'],
            signals=signals,
            generated_at=datetime.now()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving profile: {str(e)}")


# ============================================================================
# Recommendation Endpoints
# ============================================================================

@app.get("/recommendations/{user_id}", tags=["recommendations"])
async def get_recommendations(
    user_id: str,
    estimated_income: float = 0.0,
    estimated_credit_score: int = 700,
    check_consent: bool = True,
    grace_period_days: int = 0
):
    """Get recommendations with rationales for a user."""
    try:
        # Assign persona
        persona_assignment = assign_personas_with_prioritization(user_id, DB_PATH)
        
        # Build recommendations
        recommendations = build_recommendations(
            user_id,
            DB_PATH,
            persona_assignment,
            estimated_income=estimated_income,
            estimated_credit_score=estimated_credit_score,
            check_consent=check_consent,
            grace_period_days=grace_period_days
        )
        
        # Format for API
        return format_recommendations_for_api(recommendations)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating recommendations: {str(e)}")


# ============================================================================
# Feedback Endpoints
# ============================================================================

@app.post("/feedback", tags=["feedback"])
async def create_feedback(feedback: FeedbackCreate):
    """Record user feedback on recommendations."""
    # In a real implementation, this would save to a feedback table
    # For now, we just return success
    return {
        "message": "Feedback recorded",
        "user_id": feedback.user_id,
        "recommendation_id": feedback.recommendation_id,
        "feedback_type": feedback.feedback_type,
        "rating": feedback.rating,
        "recorded_at": datetime.now().isoformat()
    }


# ============================================================================
# Operator Endpoints
# ============================================================================

@app.get("/operator/review", tags=["operator"])
async def get_pending_reviews():
    """Get approval queue of pending reviews."""
    try:
        pending = get_pending_reviews(DB_PATH)
        return {
            "pending_count": len(pending),
            "reviews": pending
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving pending reviews: {str(e)}")


@app.get("/operator/signals/{user_id}", tags=["operator"])
async def get_user_signals(user_id: str):
    """View behavioral signals for a user."""
    try:
        signals = get_signals_for_user(user_id, DB_PATH)
        return {
            "user_id": user_id,
            "signals": [s.dict() for s in signals],
            "signal_count": len(signals)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving signals: {str(e)}")


@app.post("/operator/override/{trace_id}", tags=["operator"])
async def override_recommendation(trace_id: str, review: ReviewUpdate):
    """Override a recommendation decision."""
    try:
        review_status = ReviewStatus(review.review_status.lower())
        
        success = update_review_status(
            trace_id,
            DB_PATH,
            review_status,
            reviewed_by=review.reviewed_by,
            review_notes=review.review_notes,
            override_reason=review.override_reason
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Trace not found")
        
        return {
            "message": "Recommendation override recorded",
            "trace_id": trace_id,
            "review_status": review_status.value,
            "reviewed_by": review.reviewed_by,
            "reviewed_at": datetime.now().isoformat()
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error overriding recommendation: {str(e)}")


@app.get("/operator/trace/{trace_id}", tags=["operator"])
async def get_decision_trace(trace_id: str):
    """View decision trace for a recommendation."""
    try:
        trace = get_decision_trace(trace_id, DB_PATH)
        
        if not trace:
            raise HTTPException(status_code=404, detail="Trace not found")
        
        return trace
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving trace: {str(e)}")


# ============================================================================
# Health Check
# ============================================================================

@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "database": "connected" if os.path.exists(DB_PATH) else "not_found"
    }


# ============================================================================
# Startup
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize database tables on startup."""
    # Ensure decision trace tables exist
    create_decision_trace_tables(DB_PATH)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

