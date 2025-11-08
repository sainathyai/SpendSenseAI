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
from ingest.database import create_database
from eval.effectiveness_tracking import (
    track_engagement,
    track_outcome,
    generate_effectiveness_report,
    create_effectiveness_tables
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


class EngagementTrackRequest(BaseModel):
    """Request body for tracking recommendation engagement."""
    recommendation_id: str
    action: str
    user_id: Optional[str] = None
    time_spent: float = 0.0
    content_id: Optional[str] = None
    offer_id: Optional[str] = None


class OutcomeTrackRequest(BaseModel):
    """Request body for tracking recommendation outcomes."""
    user_id: str
    recommendation_id: str
    outcome_type: str
    time_window_days: Optional[int] = 30
    content_id: Optional[str] = None
    offer_id: Optional[str] = None


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


@app.get("/balances/{user_id}", tags=["profile"])
async def get_user_balances(user_id: str):
    """Get account balances and financial summary for a user."""
    try:
        from ingest.queries import get_credit_card_liabilities_by_customer
        
        balance_analysis = analyze_customer_balances(user_id, DB_PATH)
        
        # Get credit card liabilities for APR data
        credit_liabilities = get_credit_card_liabilities_by_customer(user_id, DB_PATH)
        liability_map = {liab.account_id: liab for liab in credit_liabilities}
        
        # Format response - balance_analysis is a dict, not an object
        accounts = []
        account_balances = balance_analysis.get('account_balances', [])
        
        def synthesize_apr(balance: float, utilization: float) -> float:
            """Synthesize APR based on balance and utilization."""
            base_apr = 18.0  # Base APR for good credit
            utilization_multiplier = min(utilization / 100, 1.0)
            balance_multiplier = 1.2 if balance > 10000 else 1.0
            
            apr = base_apr + (utilization_multiplier * 7)
            apr *= balance_multiplier
            
            return round(apr, 1)
        
        for account in account_balances:
            # account is an AccountBalance dataclass
            account_data = {
                "account_id": account.account_id,
                "type": account.account_type,
                "subtype": account.account_subtype,
                "balances": {
                    "current": account.current_balance,
                    "available": account.available_balance,
                    "limit": account.credit_limit
                }
            }
            
            # Add APR for credit cards
            if account.account_type == 'credit' and account.current_balance > 0:
                # Try to get APR from liability data first
                liability = liability_map.get(account.account_id)
                if liability and liability.aprs:
                    # Use actual APR from liability data
                    account_data["apr"] = liability.aprs[0].percentage
                else:
                    # Synthesize APR based on utilization
                    limit = account.credit_limit or 0
                    utilization = (account.current_balance / limit * 100) if limit > 0 else 0
                    account_data["apr"] = synthesize_apr(account.current_balance, utilization)
                
                # Add utilization rate
                if account.credit_limit and account.credit_limit > 0:
                    account_data["utilization_rate"] = round((account.current_balance / account.credit_limit) * 100, 1)
            
            accounts.append(account_data)
        
        summary = balance_analysis.get('summary', {})
        total_assets = summary.get('total_assets', 0.0)
        total_debts = summary.get('total_debts', 0.0)
        
        return {
            "user_id": user_id,
            "total_assets": total_assets,
            "total_debts": total_debts,
            "net_worth": total_assets - total_debts,
            "accounts": accounts,
            "generated_at": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving balances: {str(e)}")


# ============================================================================
# Recommendation Endpoints
# ============================================================================

@app.get("/recommendations/{user_id}", tags=["recommendations"])
async def get_recommendations(
    user_id: str,
    estimated_income: float = 0.0,
    estimated_credit_score: int = 700,
    check_consent: bool = True,
    grace_period_days: int = 30  # Default grace period of 30 days
):
    """Get recommendations with rationales for a user."""
    try:
        # Assign persona (now always returns a persona, defaulting to SAVINGS_BUILDER if none match)
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
        result = format_recommendations_for_api(recommendations)
        
        # Add helpful message if no recommendations
        if not result.get('education_items') and not result.get('partner_offers'):
            result['message'] = "No recommendations available. This may be due to insufficient data or no matching content/offers for your persona."
        
        return result
    except Exception as e:
        import traceback
        error_detail = f"Error generating recommendations: {str(e)}\n{traceback.format_exc()}"
        raise HTTPException(status_code=500, detail=error_detail)


# ============================================================================
# Calculator Endpoints
# ============================================================================

@app.post("/calculators/credit-payoff", tags=["calculators"])
def calculate_credit_payoff_endpoint(
    balance: float,
    credit_limit: float,
    apr: float,
    monthly_payment: float
):
    """Calculate credit card payoff timeline."""
    from recommend.calculators import calculate_credit_payoff
    
    try:
        result = calculate_credit_payoff(
            current_balance=balance,
            credit_limit=credit_limit,
            target_utilization=0.30,  # Target 30% utilization
            monthly_payment=monthly_payment,
            apr=apr
        )
        
        # Convert to dict for API response
        return {
            "months_to_goal": result.months_to_goal,
            "total_interest_paid": result.total_interest_paid,
            "total_payments": result.total_payments,
            "current_balance": result.current_balance,
            "current_utilization": result.current_utilization,
            "target_balance": result.target_balance,
            "balance_reduction_needed": result.balance_reduction_needed,
            "monthly_payment": result.monthly_payment
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/calculators/emergency-fund", tags=["calculators"])
def calculate_emergency_fund_endpoint(
    monthly_expenses: float,
    current_savings: float,
    monthly_savings: float,
    target_months: float = 3.0
):
    """Calculate emergency fund timeline."""
    from recommend.calculators import calculate_emergency_fund
    
    try:
        result = calculate_emergency_fund(
            current_savings=current_savings,
            monthly_expenses=monthly_expenses,
            target_months=target_months,
            monthly_savings=monthly_savings
        )
        
        # Convert to dict for API response
        return {
            "target_emergency_fund": result.target_emergency_fund,
            "current_savings": result.current_savings,
            "monthly_expenses": result.monthly_expenses,
            "months_coverage": result.months_coverage,
            "remaining_needed": result.remaining_needed,
            "monthly_savings": result.monthly_savings,
            "months_to_goal": result.months_to_goal,
            "achievable": result.achievable
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/calculators/subscription-analysis", tags=["calculators"])
async def analyze_subscriptions_endpoint(
    user_id: str
):
    """Analyze subscription costs for a user."""
    from recommend.calculators import analyze_subscription_costs
    from features.subscription_detection import detect_subscriptions_for_customer
    
    try:
        # Detect subscriptions for the customer
        subscriptions, sub_metrics = detect_subscriptions_for_customer(user_id, DB_PATH, window_days=90)
        
        # If no subscriptions found, return empty result
        if not subscriptions:
            return {
                "total_subscriptions": 0,
                "monthly_recurring_spend": 0.0,
                "annual_recurring_spend": 0.0,
                "subscriptions_to_cancel": [],
                "potential_monthly_savings": 0.0,
                "potential_annual_savings": 0.0
            }
        
        # Analyze subscription costs
        result = analyze_subscription_costs(subscriptions)
        
        # Convert to dict for API response
        return {
            "total_subscriptions": result.total_subscriptions,
            "monthly_recurring_spend": result.monthly_recurring_spend,
            "annual_recurring_spend": result.annual_recurring_spend,
            "subscriptions_to_cancel": result.subscriptions_to_cancel,
            "potential_monthly_savings": result.potential_monthly_savings,
            "potential_annual_savings": result.potential_annual_savings
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/calculators/variable-income-budget", tags=["calculators"])
async def plan_variable_budget_endpoint(
    user_id: str
):
    """Plan budget for variable income."""
    from recommend.calculators import plan_variable_income_budget
    from features.income_stability import analyze_income_stability_for_customer
    from ingest.balance_analysis import analyze_customer_balances
    
    try:
        # Get income stability metrics
        income_metrics = analyze_income_stability_for_customer(user_id, DB_PATH, 180)
        
        # Get balance data to estimate monthly income
        balance_data = analyze_customer_balances(user_id, DB_PATH)
        
        # Estimate monthly income from balance data or use default
        estimated_monthly_income = 3000.0  # Default estimate
        if balance_data and 'total_assets' in balance_data:
            # Use a conservative estimate based on assets
            estimated_monthly_income = max(3000.0, balance_data.get('total_assets', 0) / 12)
        
        # Get income variability (default to 0.3 if not available)
        income_variability = getattr(income_metrics, 'income_variability', 0.3)
        
        # Estimate essential expenses (50% of income as a default)
        essential_expenses = estimated_monthly_income * 0.50
        
        # Plan the budget
        result = plan_variable_income_budget(
            monthly_income=estimated_monthly_income,
            income_variability=income_variability,
            essential_expenses=essential_expenses,
            savings_target_percentage=0.20
        )
        
        # Convert to dict for API response
        return {
            "monthly_income": result.monthly_income,
            "income_variability": result.income_variability,
            "essential_expenses": result.essential_expenses,
            "discretionary_expenses": result.discretionary_expenses,
            "savings_target": result.savings_target,
            "recommended_budget": result.recommended_budget,
            "percentage_budget": result.percentage_budget
        }
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
async def track_recommendation_engagement(request: EngagementTrackRequest):
    """Track engagement with a recommendation."""
    try:
        metrics = track_engagement(
            recommendation_id=request.recommendation_id,
            action=request.action,
            engagement_data={
                "time_spent": request.time_spent,
                "content_id": request.content_id,
                "offer_id": request.offer_id
            },
            user_id=request.user_id,
            db_path=DB_PATH
        )

        return {
            "recommendation_id": metrics.recommendation_id,
            "user_id": metrics.user_id,
            "content_id": metrics.content_id,
            "offer_id": metrics.offer_id,
            "views": metrics.views,
            "clicks": metrics.clicks,
            "completions": metrics.completions,
            "click_through_rate": metrics.click_through_rate,
            "completion_rate": metrics.completion_rate,
            "average_time_spent": metrics.average_time_spent
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error tracking engagement: {str(e)}")


@app.post("/tracking/outcomes", tags=["tracking"], description="Track outcomes for a user.")
async def track_user_outcomes(request: OutcomeTrackRequest):
    """Track outcome of a recommendation for a user."""
    try:
        outcome = track_outcome(
            request.user_id,
            request.recommendation_id,
            DB_PATH,
            request.outcome_type,
            time_window_days=request.time_window_days or 30,
            metadata={
                "content_id": request.content_id,
                "offer_id": request.offer_id
            }
        )

        if outcome:
            return {
                "user_id": outcome.user_id,
                "recommendation_id": outcome.recommendation_id,
                "outcome_type": outcome.outcome_type,
                "before_value": outcome.before_value,
                "after_value": outcome.after_value,
                "improvement_percentage": outcome.improvement_percentage,
                "time_to_improvement_days": outcome.time_to_improvement_days,
                "attribution_confidence": outcome.attribution_confidence,
                "content_id": outcome.content_id,
                "offer_id": outcome.offer_id,
                "observed_at": outcome.observed_at.isoformat()
            }
        return {
            "message": "No outcome data available",
            "user_id": request.user_id,
            "recommendation_id": request.recommendation_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error tracking outcome: {str(e)}")


@app.get("/tracking/effectiveness-report", tags=["tracking"], description="Generate effectiveness report.")
async def get_effectiveness_report(limit: int = 100):
    """Generate effectiveness report for all users."""
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


@app.post("/health/test-alert", tags=["health"], description="Test alert notification system.")
async def test_alert_notification(level: str = "info"):
    """Test alert notification system with a sample alert."""
    from eval.alert_notifier import send_alert_notification, load_alert_configs
    from datetime import datetime
    
    try:
        configs = load_alert_configs()
        
        test_alert = {
            "alert_id": f"TEST-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "level": level,
            "title": "Test Alert",
            "message": "This is a test alert to verify the notification system is working correctly.",
            "timestamp": datetime.now(),
            "component": "testing",
            "metadata": {
                "test": True,
                "level": level
            }
        }
        
        notifications = send_alert_notification(test_alert, configs)
        
        return {
            "message": "Test alert sent",
            "alert": test_alert,
            "notifications": [
                {
                    "channel": n.channel.value,
                    "success": n.success,
                    "sent_at": n.sent_at.isoformat(),
                    "error_message": n.error_message
                }
                for n in notifications
            ],
            "total_channels": len(notifications),
            "successful_channels": sum(1 for n in notifications if n.success)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error testing alert notification: {str(e)}")


@app.get("/health/dashboard", tags=["health"], description="Get comprehensive dashboard metrics.")
async def get_dashboard_metrics():
    """Get comprehensive dashboard metrics for health dashboard."""
    from eval.monitoring import check_system_health, check_data_quality, monitor_performance
    from eval.cost_tracking import get_cost_summary, create_cost_tracking_tables
    from ingest.queries import get_all_customers
    from ingest.database import get_connection
    from datetime import datetime, timedelta, date
    
    try:
        # Initialize cost tracking tables
        create_cost_tracking_tables(DB_PATH)
        
        # Get system health
        customers = get_all_customers(DB_PATH)
        user_ids = [c.customer_id if hasattr(c, 'customer_id') else c for c in customers[:100]]
        
        system_health = check_system_health(user_ids, DB_PATH, send_notifications=False)
        
        # Get performance metrics
        perf_metrics = monitor_performance(user_ids, DB_PATH)
        
        # Get data quality alerts
        data_quality_alerts = check_data_quality(DB_PATH)
        
        # Get cost summary
        cost_summary = get_cost_summary(DB_PATH)
        
        # Get user activity
        today = date.today()
        week_ago = today - timedelta(days=7)
        
        with get_connection(DB_PATH) as conn:
            cursor = conn.cursor()
            
            # Active users today
            cursor.execute("""
                SELECT COUNT(DISTINCT customer_id) 
                FROM accounts 
                WHERE DATE(updated_at) = ?
            """, (today.isoformat(),))
            active_today = cursor.fetchone()[0] or 0
            
            # Active users this week
            cursor.execute("""
                SELECT COUNT(DISTINCT customer_id) 
                FROM accounts 
                WHERE DATE(updated_at) >= ?
            """, (week_ago.isoformat(),))
            active_week = cursor.fetchone()[0] or 0
            
            # Recommendations served today (from effectiveness tracking)
            try:
                cursor.execute("""
                    SELECT COUNT(DISTINCT recommendation_id) 
                    FROM recommendation_engagement 
                    WHERE DATE(created_at) = ?
                """, (today.isoformat(),))
                recommendations_today = cursor.fetchone()[0] or 0
            except Exception:
                recommendations_today = 0
            
            # Consent granted today
            try:
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM consent 
                    WHERE DATE(granted_at) = ? AND status = 'active'
                """, (today.isoformat(),))
                consent_today = cursor.fetchone()[0] or 0
            except Exception:
                consent_today = 0
            
            # Database size
            cursor.execute("SELECT COUNT(*) FROM accounts")
            total_accounts = cursor.fetchone()[0] or 0
            
            cursor.execute("SELECT COUNT(*) FROM transactions")
            total_transactions = cursor.fetchone()[0] or 0
            
            # Data freshness (most recent transaction)
            try:
                cursor.execute("""
                    SELECT MAX(date) 
                    FROM transactions
                """)
                latest_transaction = cursor.fetchone()[0]
                if latest_transaction:
                    latest_date = datetime.fromisoformat(latest_transaction) if isinstance(latest_transaction, str) else latest_transaction
                    data_freshness_hours = (datetime.now() - latest_date).total_seconds() / 3600
                else:
                    data_freshness_hours = 0
            except Exception:
                data_freshness_hours = 0
        
        # Calculate uptime (simplified - would need actual start time)
        uptime_seconds = 86400  # Placeholder
        
        return {
            "timestamp": datetime.now().isoformat(),
            "overall_status": system_health.overall_status,
            "health_score": system_health.health_score,
            "uptime_seconds": uptime_seconds,
            "active_alerts_count": len(data_quality_alerts) + len(system_health.anomaly_alerts),
            "performance_metrics": {
                "latency_p50": perf_metrics.latency_p50,
                "latency_p95": perf_metrics.latency_p95,
                "latency_p99": perf_metrics.latency_p99,
                "throughput": perf_metrics.throughput,
                "error_rate": perf_metrics.error_rate,
                "active_users": perf_metrics.active_users,
                "latency_history": []  # Would need historical data
            },
            "user_activity": {
                "active_today": active_today,
                "active_week": active_week,
                "recommendations_served_today": recommendations_today,
                "consent_granted_today": consent_today
            },
            "data_quality": {
                "total_accounts": total_accounts,
                "total_transactions": total_transactions,
                "data_freshness_hours": data_freshness_hours,
                "alerts": [
                    {
                        "alert_id": alert.alert_id,
                        "alert_type": alert.alert_type,
                        "severity": alert.severity,
                        "message": alert.message,
                        "affected_count": alert.affected_count,
                        "timestamp": alert.timestamp.isoformat()
                    }
                    for alert in data_quality_alerts
                ]
            },
            "costs": {
                "llm_cost_today": cost_summary.get("today_cost", 0.0),
                "llm_cost_month": cost_summary.get("month_cost", 0.0),
                "llm_requests_today": cost_summary.get("today_requests", 0),
                "avg_cost_per_request": cost_summary.get("avg_cost_per_request", 0.0),
                "cost_history": [
                    {
                        "date": daily["date"],
                        "daily_cost": daily["total_cost"]
                    }
                    for daily in cost_summary.get("daily_costs", [])[:30]  # Last 30 days
                ]
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating dashboard metrics: {str(e)}")


# ============================================================================
# A/B Testing Endpoints
# ============================================================================

@app.post("/experiments", tags=["experiments"], description="Create a new A/B test experiment.")
async def create_experiment(
    experiment_id: str,
    name: str,
    description: str,
    variants: List[Dict[str, Any]]
):
    """Create a new A/B test experiment."""
    from eval.ab_testing import create_experiment, Experiment, ExperimentVariant, ExperimentStatus, VariantType
    from datetime import datetime
    
    try:
        variant_objects = []
        for v in variants:
            variant_objects.append(ExperimentVariant(
                variant_id=v["variant_id"],
                variant_type=VariantType(v["variant_type"]),
                name=v["name"],
                description=v.get("description", ""),
                configuration=v.get("configuration", {}),
                traffic_percentage=v.get("traffic_percentage", 50.0)
            ))
        
        experiment = Experiment(
            experiment_id=experiment_id,
            name=name,
            description=description,
            status=ExperimentStatus.DRAFT,
            variants=variant_objects,
            start_date=datetime.now(),
            target_sample_size=None,
            min_sample_size=100
        )
        
        exp_id = create_experiment(experiment, DB_PATH)
        
        return {
            "experiment_id": exp_id,
            "message": "Experiment created successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating experiment: {str(e)}")


@app.get("/experiments/{experiment_id}", tags=["experiments"], description="Get experiment details.")
async def get_experiment_details(experiment_id: str):
    """Get experiment details."""
    from eval.ab_testing import get_experiment
    
    try:
        experiment = get_experiment(experiment_id, DB_PATH)
        if not experiment:
            raise HTTPException(status_code=404, detail="Experiment not found")
        
        return {
            "experiment_id": experiment.experiment_id,
            "name": experiment.name,
            "description": experiment.description,
            "status": experiment.status.value,
            "start_date": experiment.start_date.isoformat(),
            "end_date": experiment.end_date.isoformat() if experiment.end_date else None,
            "variants": [
                {
                    "variant_id": v.variant_id,
                    "variant_type": v.variant_type.value,
                    "name": v.name,
                    "description": v.description,
                    "traffic_percentage": v.traffic_percentage
                }
                for v in experiment.variants
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving experiment: {str(e)}")


@app.get("/experiments/{experiment_id}/results", tags=["experiments"], description="Get experiment results.")
async def get_experiment_results(experiment_id: str):
    """Get experiment results with statistical analysis."""
    from eval.ab_testing import analyze_experiment_results
    
    try:
        results = analyze_experiment_results(experiment_id, DB_PATH)
        
        return {
            "experiment_id": experiment_id,
            "results": [
                {
                    "variant_id": r.variant_id,
                    "variant_type": r.variant_type.value,
                    "sample_size": r.sample_size,
                    "engagement_rate": r.engagement_rate,
                    "completion_rate": r.completion_rate,
                    "conversion_rate": r.conversion_rate,
                    "average_outcome_improvement": r.average_outcome_improvement,
                    "statistical_significance": r.statistical_significance,
                    "confidence_interval_lower": r.confidence_interval_lower,
                    "confidence_interval_upper": r.confidence_interval_upper,
                    "is_winner": r.is_winner
                }
                for r in results
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing experiment: {str(e)}")


@app.post("/experiments/{experiment_id}/start", tags=["experiments"], description="Start an experiment.")
async def start_experiment(experiment_id: str):
    """Start an experiment."""
    from eval.ab_testing import get_experiment, create_ab_testing_tables, ExperimentStatus
    from ingest.database import get_connection
    
    try:
        create_ab_testing_tables(DB_PATH)
        
        with get_connection(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE ab_experiments 
                SET status = ? 
                WHERE experiment_id = ?
            """, (ExperimentStatus.RUNNING.value, experiment_id))
            conn.commit()
        
        return {
            "experiment_id": experiment_id,
            "status": "running",
            "message": "Experiment started successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting experiment: {str(e)}")


# ============================================================================
# Advanced Cohort Analysis Endpoints
# ============================================================================

@app.get("/cohorts/predictive", tags=["cohorts"], description="Get predictive cohorts.")
async def get_predictive_cohorts():
    """Get predictive cohorts based on behavior patterns."""
    from eval.cohort_analysis import create_predictive_cohorts
    from ingest.queries import get_all_customers
    
    try:
        customers = get_all_customers(DB_PATH)
        user_ids = [c.customer_id if hasattr(c, 'customer_id') else c for c in customers]
        
        cohorts = create_predictive_cohorts(user_ids, DB_PATH)
        
        return {
            "cohorts": {
                cohort_name: {
                    "user_count": len(user_ids),
                    "user_ids": user_ids[:10]  # Limit for response
                }
                for cohort_name, user_ids in cohorts.items()
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating predictive cohorts: {str(e)}")


@app.get("/cohorts/fairness", tags=["cohorts"], description="Analyze fairness across cohorts.")
async def analyze_cohort_fairness():
    """Analyze fairness metrics across cohorts."""
    from eval.cohort_analysis import analyze_all_cohorts, analyze_fairness_across_cohorts
    from ingest.queries import get_all_customers
    
    try:
        customers = get_all_customers(DB_PATH)
        user_ids = [c.customer_id if hasattr(c, 'customer_id') else c for c in customers]
        
        cohorts = analyze_all_cohorts(user_ids, DB_PATH)
        fairness_metrics = analyze_fairness_across_cohorts(cohorts)
        
        return {
            "fairness_metrics": fairness_metrics,
            "cohort_count": len(cohorts)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing fairness: {str(e)}")


# ============================================================================
# Advanced Anomaly Detection Endpoints
# ============================================================================

@app.get("/anomalies/user/{user_id}", tags=["anomalies"], description="Detect user-level anomalies.")
async def detect_user_anomalies(user_id: str):
    """Detect anomalies for a specific user."""
    from eval.advanced_anomaly_detection import detect_user_anomalies, prioritize_anomalies, save_user_anomaly
    
    try:
        anomalies = detect_user_anomalies(user_id, DB_PATH)
        prioritized = prioritize_anomalies(anomalies)
        
        # Save anomalies
        for anomaly in prioritized:
            save_user_anomaly(anomaly, DB_PATH)
        
        return {
            "user_id": user_id,
            "anomalies": [
                {
                    "anomaly_id": a.anomaly_id,
                    "anomaly_type": a.anomaly_type.value,
                    "severity": a.severity.value,
                    "description": a.description,
                    "detected_at": a.detected_at.isoformat(),
                    "deviation_percentage": a.deviation_percentage
                }
                for a in prioritized
            ],
            "count": len(prioritized)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error detecting anomalies: {str(e)}")


# ============================================================================
# Admin / Maintenance Endpoints
# ============================================================================

@app.post("/admin/reseed-liabilities")
async def reseed_liabilities_endpoint():
    """
    Reload liabilities data from CSV (for admin use).
    """
    from pathlib import Path
    from ingest.database import get_connection, load_from_csv
    
    try:
        data_dir = Path("data/processed")
        
        # Delete existing liabilities
        with get_connection(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM credit_card_liabilities")
            conn.commit()
        
        # Reload from CSV
        liabilities_file = data_dir / "liabilities.csv"
        
        if not liabilities_file.exists():
            return {
                "status": "error",
                "message": f"liabilities.csv not found in {data_dir.absolute()}"
            }
        
        # Load liabilities
        import csv
        with get_connection(DB_PATH) as conn:
            cursor = conn.cursor()
            with open(liabilities_file, 'r') as f:
                reader = csv.DictReader(f)
                count = 0
                for row in reader:
                    cursor.execute("""
                        INSERT INTO credit_card_liabilities (
                            account_id, apr_type, apr_percentage, minimum_payment_amount,
                            last_payment_amount, is_overdue, next_payment_due_date,
                            last_statement_balance
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        row['account_id'],
                        row.get('apr_type', 'purchase_apr'),
                        float(row['apr_percentage']) if row.get('apr_percentage') else 0.0,
                        float(row['minimum_payment_amount']) if row.get('minimum_payment_amount') else 0.0,
                        float(row['last_payment_amount']) if row.get('last_payment_amount') else None,
                        int(row['is_overdue']) if row.get('is_overdue') else 0,
                        row.get('next_payment_due_date'),
                        float(row['last_statement_balance']) if row.get('last_statement_balance') else None
                    ))
                    count += 1
            conn.commit()
        
        # Count overdue
        with get_connection(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM credit_card_liabilities WHERE is_overdue = 1")
            overdue_count = cursor.fetchone()[0]
        
        return {
            "status": "success",
            "message": "Liabilities reloaded successfully",
            "liabilities_loaded": count,
            "overdue_accounts": overdue_count
        }
        
    except Exception as e:
        import traceback
        return {
            "status": "error",
            "message": str(e),
            "traceback": traceback.format_exc()
        }


@app.post("/admin/grant-all-consent")
async def grant_all_consent_endpoint():
    """
    Grant consent to all customers (for admin use).
    """
    from guardrails.consent import grant_consent, ConsentScope
    from ingest.database import get_connection
    
    try:
        # Get all customer IDs
        with get_connection(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT DISTINCT customer_id FROM accounts ORDER BY customer_id')
            customers = [row[0] for row in cursor.fetchall()]
        
        # Grant consent to each customer
        granted_count = 0
        for customer_id in customers:
            try:
                grant_consent(
                    customer_id, 
                    DB_PATH, 
                    scope=ConsentScope.ALL,
                    notes="Auto-granted consent for demo"
                )
                granted_count += 1
            except Exception as e:
                print(f"Error granting consent to {customer_id}: {e}")
        
        return {
            "status": "success",
            "message": f"Consent granted to {granted_count} customers",
            "total_customers": len(customers),
            "granted": granted_count
        }
        
    except Exception as e:
        import traceback
        return {
            "status": "error",
            "message": str(e),
            "traceback": traceback.format_exc()
        }


@app.post("/admin/recalculate-overdue")
async def recalculate_overdue_endpoint():
    """
    Manually trigger overdue status recalculation (for admin use).
    """
    from datetime import date, timedelta
    from ingest.database import get_connection
    
    try:
        with get_connection(DB_PATH) as conn:
            cursor = conn.cursor()
            
            # Move all payment due dates back by 30 days to simulate overdue
            cursor.execute("""
                UPDATE credit_card_liabilities
                SET next_payment_due_date = date(next_payment_due_date, '-30 days')
                WHERE next_payment_due_date IS NOT NULL
            """)
            
            # Set is_overdue = 1 for cards with balance > 0 and due date in the past
            cursor.execute("""
                UPDATE credit_card_liabilities
                SET is_overdue = 1
                WHERE next_payment_due_date < date('now')
                AND account_id IN (
                    SELECT account_id FROM accounts WHERE balances_current > 0
                )
            """)
            
            # Count overdue accounts
            cursor.execute("""
                SELECT COUNT(*) FROM credit_card_liabilities
                WHERE is_overdue = 1
            """)
            overdue_count = cursor.fetchone()[0]
            
            conn.commit()
            
        return {
            "status": "success",
            "message": "Overdue status recalculated",
            "overdue_accounts": overdue_count
        }
        
    except Exception as e:
        import traceback
        return {
            "status": "error",
            "message": str(e),
            "traceback": traceback.format_exc()
        }


@app.post("/admin/seed-database")
async def seed_database_endpoint():
    """
    Manually trigger database seeding (for admin use).
    """
    from pathlib import Path
    from ingest.database import get_connection
    
    try:
        # Check if database is already seeded
        with get_connection(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM accounts")
            count = cursor.fetchone()[0]
            
            if count > 0:
                return {
                    "status": "skipped",
                    "message": f"Database already contains {count} accounts",
                    "accounts": count
                }
        
        # Check if data files exist
        data_dir = Path("data/processed")
        accounts_file = data_dir / "accounts.csv"
        
        if not data_dir.exists():
            return {
                "status": "error",
                "message": f"Data directory not found: {data_dir.absolute()}"
            }
        
        if not accounts_file.exists():
            files = list(data_dir.glob("*.csv"))
            return {
                "status": "error",
                "message": f"accounts.csv not found in {data_dir.absolute()}",
                "available_files": [f.name for f in files]
            }
        
        # Seed the database
        from ingest.database import load_from_csv
        accounts_file = data_dir / "accounts.csv"
        transactions_file = data_dir / "transactions.csv"
        liabilities_file = data_dir / "liabilities.csv"
        
        counts = load_from_csv(
            str(accounts_file),
            str(transactions_file),
            str(liabilities_file),
            DB_PATH
        )
        
        # Verify seeding
        with get_connection(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM accounts")
            account_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM transactions")
            tx_count = cursor.fetchone()[0]
        
        return {
            "status": "success",
            "message": "Database seeded successfully",
            "accounts": account_count,
            "transactions": tx_count
        }
        
    except Exception as e:
        import traceback
        return {
            "status": "error",
            "message": str(e),
            "traceback": traceback.format_exc()
        }


# ============================================================================
# Startup
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize database tables on startup."""
    import os
    from pathlib import Path
    
    # Ensure core data tables exist
    create_database(DB_PATH)

    # Ensure decision trace tables exist
    create_decision_trace_tables(DB_PATH)
    create_effectiveness_tables(DB_PATH)
    
    # Initialize cost tracking tables
    from eval.cost_tracking import create_cost_tracking_tables
    create_cost_tracking_tables(DB_PATH)
    
    # Initialize A/B testing tables
    from eval.ab_testing import create_ab_testing_tables
    create_ab_testing_tables(DB_PATH)
    
    # Initialize consent tables
    from guardrails.consent import create_consent_tables
    create_consent_tables(DB_PATH)
    
    # Auto-seed database if empty
    try:
        from ingest.database import get_connection
        with get_connection(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM accounts")
            count = cursor.fetchone()[0]
            
            if count == 0:
                print("[STARTUP] Database is empty, attempting to seed...")
                data_dir = Path("data/processed")
                if data_dir.exists() and (data_dir / "accounts.csv").exists():
                    print(f"[STARTUP] Found data files in {data_dir}, seeding database...")
                    from ingest.database import load_from_csv
                    accounts_file = data_dir / "accounts.csv"
                    transactions_file = data_dir / "transactions.csv"
                    liabilities_file = data_dir / "liabilities.csv"
                    counts = load_from_csv(
                        str(accounts_file),
                        str(transactions_file),
                        str(liabilities_file),
                        DB_PATH
                    )
                    print(f"[STARTUP] Database seeding completed: {counts['accounts']} accounts, {counts['transactions']} transactions")
                else:
                    print(f"[STARTUP] WARNING: data/processed not found or accounts.csv missing")
            else:
                print(f"[STARTUP] Database already contains {count} accounts, skipping seed")
    except Exception as e:
        print(f"[STARTUP] Error during database seeding: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

