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
from fastapi.middleware.cors import CORSMiddleware
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
    get_pending_reviews as get_pending_reviews_from_db, update_review_status,
    ReviewStatus, create_decision_trace_tables
)
from recommend.query_interpreter import QueryInterpreter
from ingest.balance_analysis import analyze_customer_balances
from features.subscription_detection import detect_subscriptions_for_customer
from features.credit_utilization import analyze_credit_utilization_for_customer
from features.savings_pattern import analyze_savings_patterns_for_customer
from features.income_stability import analyze_income_stability_for_customer
from ingest.queries import (
    get_accounts_by_customer,
    get_all_customers,
    search_customers,
    get_all_customers_with_summary,
    get_transactions_summary_by_category
)

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

# Enable CORS for local frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
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

@app.get("/users", tags=["users"])
async def list_users(limit: Optional[int] = None):
    """Get list of all users with summary information."""
    try:
        customers = get_all_customers_with_summary(DB_PATH, limit=limit)
        return {
            "total": len(customers),
            "users": customers
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving users: {str(e)}")


@app.get("/users/{user_id}", response_model=UserResponse, tags=["users"])
async def get_user(user_id: str):
    """Get user details."""
    # In a real implementation, this would query a users table
    # For now, we just return basic info
    return UserResponse(
        user_id=user_id,
        created_at=datetime.now()
    )


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


@app.get("/users/search/suggestions", tags=["users"])
async def search_user_suggestions(query: str, limit: int = 10):
    """Get user search suggestions (autocomplete)."""
    try:
        if not query or len(query) < 1:
            return {"suggestions": []}
        
        suggestions = search_customers(DB_PATH, query, limit=limit)
        return {
            "query": query,
            "suggestions": suggestions,
            "count": len(suggestions)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching users: {str(e)}")


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
# Calculator Endpoints
# ============================================================================

@app.post("/calculators/credit-payoff", tags=["calculators"])
async def calculate_credit_payoff_endpoint(
    balance: float,
    apr: float,
    monthly_payment: float
):
    """Calculate credit card payoff timeline."""
    from recommend.calculators import calculate_credit_payoff
    
    try:
        result = calculate_credit_payoff(balance, apr, monthly_payment)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/calculators/emergency-fund", tags=["calculators"])
async def calculate_emergency_fund_endpoint(
    monthly_expenses: float,
    current_savings: float,
    monthly_savings: float,
    target_months: float = 3.0
):
    """Calculate emergency fund timeline."""
    from recommend.calculators import calculate_emergency_fund
    
    try:
        result = calculate_emergency_fund(
            monthly_expenses=monthly_expenses,
            current_savings=current_savings,
            monthly_savings=monthly_savings,
            target_months=target_months
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/calculators/subscription-analysis", tags=["calculators"])
async def analyze_subscriptions_endpoint(
    user_id: str
):
    """Analyze subscription costs for a user."""
    from recommend.calculators import analyze_subscription_costs
    
    try:
        result = analyze_subscription_costs(user_id, DB_PATH)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/calculators/variable-income-budget", tags=["calculators"])
async def plan_variable_budget_endpoint(
    user_id: str
):
    """Plan budget for variable income."""
    from recommend.calculators import plan_variable_income_budget
    
    try:
        result = plan_variable_income_budget(user_id, DB_PATH)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/calculators/{user_id}", tags=["calculators"])
async def get_user_calculators(user_id: str):
    """Get all calculator results for a user."""
    from recommend.calculators import get_calculator_results_for_user
    
    try:
        results = get_calculator_results_for_user(user_id, DB_PATH)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Feedback Endpoints
# ============================================================================

@app.post("/feedback", tags=["feedback"], description="Record user feedback on recommendations.")
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
        pending = get_pending_reviews_from_db(DB_PATH)
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


@app.get("/operator/transactions/{user_id}/summary", tags=["operator"])
async def get_transaction_summary(user_id: str, days: int = 90):
    """Get transaction summary by category for a user (for model review)."""
    try:
        from datetime import date, timedelta
        
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        summary = get_transactions_summary_by_category(
            user_id, DB_PATH,
            start_date=start_date,
            end_date=end_date
        )
        
        return {
            "user_id": user_id,
            "period_days": days,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            **summary
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving transaction summary: {str(e)}")


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
# Query Tool Endpoints
# ============================================================================

class QueryRequest(BaseModel):
    """Request model for natural language query."""
    query: str
    customer_id: Optional[str] = None


@app.post("/operator/query", tags=["operator"])
async def execute_query(request: QueryRequest):
    """
    Execute a natural language query against the database.
    
    Examples:
    - "show balances for CUST000001"
    - "list customers"
    - "subscriptions for CUST000001"
    - "debt info for CUST000001"
    """
    try:
        interpreter = QueryInterpreter(DB_PATH)
        context = {'customer_id': request.customer_id} if request.customer_id else None
        result = interpreter.interpret(request.query, context)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error executing query: {str(e)}")


# ============================================================================
# Behavioral Trend Analysis Endpoints
# ============================================================================

@app.get("/trends/{user_id}", tags=["trends"], description="Get behavioral trend analysis for a user.")
async def get_user_trends(user_id: str, months: int = 3):
    """Get behavioral trend analysis for a user."""
    from features.trend_analysis import analyze_behavior_trends
    
    try:
        trends = analyze_behavior_trends(user_id, DB_PATH, months)
        
        # Convert to dict
        return {
            "user_id": trends.user_id,
            "analysis_date": trends.analysis_date.isoformat(),
            "trends": {
                name: {
                    "metric_name": trend.metric_name,
                    "trend_direction": trend.trend_direction,
                    "trend_percentage": trend.trend_percentage,
                    "month_over_month_change": trend.month_over_month_change,
                    "early_warning": trend.early_warning,
                    "predictive_signal": trend.predictive_signal,
                    "trend_points": [
                        {
                            "date": point.date.isoformat(),
                            "value": point.value,
                            "metric_name": point.metric_name
                        } for point in trend.trend_points
                    ]
                }
                for name, trend in trends.trends.items()
            },
            "persona_evolution": {
                period: persona.value
                for period, persona in (trends.persona_evolution or {}).items()
            } if trends.persona_evolution else {},
            "improvements": trends.improvements or [],
            "warnings": trends.warnings or [],
            "predictive_signals": trends.predictive_signals or []
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating trend analysis: {str(e)}")


@app.get("/trends/{user_id}/early-warnings", tags=["trends"], description="Get early warning signals for a user.")
async def get_early_warnings(user_id: str):
    """Get early warning signals for a user."""
    from features.trend_analysis import detect_early_warning_signals
    
    try:
        warnings = detect_early_warning_signals(user_id, DB_PATH)
        return {
            "user_id": user_id,
            "warnings": warnings,
            "count": len(warnings),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error detecting early warnings: {str(e)}")


@app.get("/trends/{user_id}/persona-evolution", tags=["trends"], description="Get persona evolution for a user.")
async def get_persona_evolution(user_id: str):
    """Get persona evolution tracking for a user."""
    from features.trend_analysis import track_persona_evolution
    
    try:
        persona_evolution = track_persona_evolution(user_id, DB_PATH)
        return {
            "user_id": user_id,
            "persona_evolution": {
                period: persona.value
                for period, persona in persona_evolution.items()
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error tracking persona evolution: {str(e)}")


# ============================================================================
# Recommendation Effectiveness Tracking Endpoints
# ============================================================================

@app.post("/tracking/engagement", tags=["tracking"], description="Track engagement with a recommendation.")
async def track_recommendation_engagement(
    recommendation_id: str,
    action: str,
    time_spent: float = 0.0
):
    """Track engagement with a recommendation."""
    from eval.effectiveness_tracking import track_engagement
    
    try:
        engagement_data = {"time_spent": time_spent}
        metrics = track_engagement(recommendation_id, action, engagement_data)
        
        return {
            "recommendation_id": metrics.recommendation_id,
            "views": metrics.views,
            "clicks": metrics.clicks,
            "completions": metrics.completions,
            "click_through_rate": metrics.click_through_rate,
            "completion_rate": metrics.completion_rate,
            "average_time_spent": metrics.average_time_spent
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error tracking engagement: {str(e)}")


@app.get("/tracking/outcomes/{user_id}", tags=["tracking"], description="Track outcomes for a user.")
async def track_user_outcomes(
    user_id: str,
    recommendation_id: str,
    outcome_type: str
):
    """Track outcome of a recommendation for a user."""
    from eval.effectiveness_tracking import track_outcome
    
    try:
        outcome = track_outcome(user_id, recommendation_id, DB_PATH, outcome_type)
        
        if outcome:
            return {
                "recommendation_id": outcome.recommendation_id,
                "outcome_type": outcome.outcome_type,
                "before_value": outcome.before_value,
                "after_value": outcome.after_value,
                "improvement_percentage": outcome.improvement_percentage,
                "time_to_improvement_days": outcome.time_to_improvement_days,
                "attribution_confidence": outcome.attribution_confidence
            }
        else:
            return {
                "message": "No outcome data available",
                "user_id": user_id,
                "recommendation_id": recommendation_id
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error tracking outcome: {str(e)}")


@app.get("/tracking/effectiveness-report", tags=["tracking"], description="Generate effectiveness report.")
async def get_effectiveness_report(limit: int = 100):
    """Generate effectiveness report for all users."""
    from eval.effectiveness_tracking import generate_effectiveness_report
    from ingest.queries import get_all_customers
    
    try:
        customers = get_all_customers(DB_PATH)
        user_ids = [c.customer_id for c in customers[:limit]]
        
        report = generate_effectiveness_report(user_ids, DB_PATH)
        
        return {
            "report_id": report.report_id,
            "timestamp": report.timestamp.isoformat(),
            "overall_effectiveness_score": report.overall_effectiveness_score,
            "engagement_metrics_count": len(report.engagement_metrics),
            "outcome_metrics_count": len(report.outcome_metrics),
            "content_performance": [
                {
                    "content_id": c.content_id,
                    "views": c.views,
                    "completions": c.completions,
                    "engagement_rate": c.engagement_rate,
                    "average_outcome_improvement": c.average_outcome_improvement,
                    "effectiveness_score": c.effectiveness_score
                }
                for c in report.content_performance
            ],
            "offer_performance": [
                {
                    "offer_id": o.offer_id,
                    "views": o.views,
                    "clicks": o.clicks,
                    "conversions": o.conversions,
                    "conversion_rate": o.conversion_rate,
                    "roi": o.roi
                }
                for o in report.offer_performance
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating effectiveness report: {str(e)}")


# ============================================================================
# System Health & Monitoring Endpoints
# ============================================================================

@app.get("/health", tags=["health"])
async def health_check():
    """Quick health check endpoint."""
    from eval.monitoring import check_database_health
    
    try:
        db_health = check_database_health(DB_PATH)
        return {
            "status": db_health.status,
            "message": db_health.message,
            "timestamp": db_health.timestamp.isoformat(),
            "metrics": db_health.metrics or {}
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "message": f"Health check failed: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }


@app.get("/health/full", tags=["health"], description="Full system health check.")
async def full_health_check():
    """Comprehensive system health check."""
    from eval.monitoring import check_system_health
    from ingest.queries import get_all_customers
    
    try:
        customers = get_all_customers(DB_PATH)
        user_ids = [c.customer_id for c in customers[:100]]
        
        system_health = check_system_health(user_ids, DB_PATH)
        
        return {
            "timestamp": system_health.timestamp.isoformat(),
            "overall_status": system_health.overall_status,
            "health_score": system_health.health_score,
            "health_checks": [
                {
                    "component": check.component,
                    "status": check.status,
                    "message": check.message,
                    "metrics": check.metrics or {}
                }
                for check in system_health.health_checks
            ],
            "performance_metrics": {
                "latency_p50": system_health.performance_metrics.latency_p50,
                "latency_p95": system_health.performance_metrics.latency_p95,
                "latency_p99": system_health.performance_metrics.latency_p99,
                "throughput": system_health.performance_metrics.throughput,
                "error_rate": system_health.performance_metrics.error_rate,
                "active_users": system_health.performance_metrics.active_users
            } if system_health.performance_metrics else None,
            "data_quality_alerts": [
                {
                    "alert_id": alert.alert_id,
                    "alert_type": alert.alert_type,
                    "severity": alert.severity,
                    "message": alert.message,
                    "affected_count": alert.affected_count
                }
                for alert in system_health.data_quality_alerts
            ],
            "anomaly_alerts": [
                {
                    "alert_id": alert.alert_id,
                    "anomaly_type": alert.anomaly_type,
                    "severity": alert.severity,
                    "message": alert.message,
                    "baseline_value": alert.baseline_value,
                    "current_value": alert.current_value,
                    "deviation_percentage": alert.deviation_percentage
                }
                for alert in system_health.anomaly_alerts
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error performing health check: {str(e)}")


@app.get("/health/data-quality", tags=["health"], description="Data quality alerts.")
async def get_data_quality_alerts():
    """Get data quality alerts."""
    from eval.monitoring import check_data_quality
    
    try:
        alerts = check_data_quality(DB_PATH)
        
        return {
            "alerts": [
                {
                    "alert_id": alert.alert_id,
                    "alert_type": alert.alert_type,
                    "severity": alert.severity,
                    "message": alert.message,
                    "affected_count": alert.affected_count,
                    "timestamp": alert.timestamp.isoformat()
                }
                for alert in alerts
            ],
            "count": len(alerts)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking data quality: {str(e)}")


@app.get("/health/performance", tags=["health"], description="Performance metrics.")
async def get_performance_metrics():
    """Get system performance metrics."""
    from eval.monitoring import monitor_performance
    from ingest.queries import get_all_customers
    
    try:
        customers = get_all_customers(DB_PATH)
        user_ids = [c.customer_id for c in customers[:100]]
        
        metrics = monitor_performance(user_ids, DB_PATH)
        
        return {
            "timestamp": metrics.timestamp.isoformat(),
            "latency_p50": metrics.latency_p50,
            "latency_p95": metrics.latency_p95,
            "latency_p99": metrics.latency_p99,
            "throughput": metrics.throughput,
            "error_rate": metrics.error_rate,
            "active_users": metrics.active_users
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving performance metrics: {str(e)}")


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

