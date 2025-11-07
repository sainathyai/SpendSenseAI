"""
Rationale Generation & Recommendation Builder for SpendSenseAI.

Generates plain-language explanations with data citations:
- Recommendation builder (combines persona + signals + content + offers)
- Rationale template system
- Data citation extraction
- Plain-language generation
- Tone validation
"""

from typing import List, Dict, Optional, Tuple
from datetime import date
from dataclasses import dataclass
import logging

from personas.persona_definition import PersonaAssignment, PersonaType
from features.subscription_detection import detect_subscriptions_for_customer
from features.credit_utilization import analyze_credit_utilization_for_customer
from features.savings_pattern import analyze_savings_patterns_for_customer
from features.income_stability import analyze_income_stability_for_customer
from recommend.content_catalog import get_content_for_persona, EducationContent
from recommend.partner_offers import get_eligible_offers_for_persona, PartnerOffer
from recommend.counterfactuals import generate_counterfactual_scenarios, CounterfactualScenario
from recommend.llm_generator import generate_rationale_with_llm, Tone, get_llm_generator
from guardrails.consent import verify_consent, ConsentScope


@dataclass
class RecommendationItem:
    """A single recommendation item."""
    recommendation_id: str
    type: str  # 'education' or 'offer'
    title: str
    description: str
    rationale: str  # Plain-language explanation with data citations
    content_id: Optional[str] = None  # For education content
    offer_id: Optional[str] = None  # For partner offers
    priority: int = 0  # Lower number = higher priority
    data_citations: Dict = None  # Supporting data for rationale
    
    def __post_init__(self):
        if self.data_citations is None:
            self.data_citations = {}


@dataclass
class RecommendationSet:
    """Complete set of recommendations for a customer."""
    customer_id: str
    persona_assignment: PersonaAssignment
    education_items: List[RecommendationItem]  # 3-5 items
    partner_offers: List[RecommendationItem]  # 1-3 items
    counterfactual_scenarios: List[CounterfactualScenario] = None  # Optional counterfactuals
    generated_at: date = None
    disclaimer: str = "This information is for educational purposes only and does not constitute financial advice. Please consult with a qualified financial advisor before making financial decisions."
    
    def __post_init__(self):
        if self.generated_at is None:
            self.generated_at = date.today()
        if self.counterfactual_scenarios is None:
            self.counterfactual_scenarios = []


def extract_data_citations(
    customer_id: str,
    db_path: str,
    persona_type: PersonaType
) -> Dict:
    """
    Extract supporting data for rationale generation.
    
    Args:
        customer_id: Customer ID
        db_path: Path to SQLite database
        persona_type: Assigned persona type
        
    Returns:
        Dictionary with data citations
    """
    citations = {
        'persona_type': persona_type.value,
        'customer_id': customer_id
    }
    
    # Extract data based on persona
    if persona_type == PersonaType.HIGH_UTILIZATION:
        card_metrics, agg_metrics = analyze_credit_utilization_for_customer(customer_id, db_path, 30)
        if card_metrics:
            citations['utilization_percentage'] = card_metrics[0].utilization_percentage
            citations['balance'] = card_metrics[0].balance
            citations['limit'] = card_metrics[0].limit
            citations['account_id'] = card_metrics[0].account_id
            citations['monthly_interest'] = agg_metrics.total_monthly_interest
            citations['overdue_cards'] = agg_metrics.overdue_card_count
    
    elif persona_type == PersonaType.SUBSCRIPTION_HEAVY:
        subscriptions, sub_metrics = detect_subscriptions_for_customer(customer_id, db_path, window_days=90)
        citations['subscription_count'] = sub_metrics['subscription_count']
        citations['monthly_recurring_spend'] = sub_metrics['total_monthly_recurring_spend']
        citations['subscription_share'] = sub_metrics['subscription_share_of_total']
        if subscriptions:
            citations['top_subscription'] = subscriptions[0].merchant_name
            citations['top_subscription_amount'] = subscriptions[0].monthly_recurring_spend
    
    elif persona_type == PersonaType.SAVINGS_BUILDER:
        savings_accounts, savings_metrics = analyze_savings_patterns_for_customer(customer_id, db_path, 180)
        citations['savings_balance'] = savings_metrics.total_savings_balance
        citations['growth_rate'] = savings_metrics.overall_growth_rate
        citations['monthly_inflow'] = savings_metrics.average_monthly_inflow
    
    elif persona_type == PersonaType.VARIABLE_INCOME_BUDGETER:
        income_metrics = analyze_income_stability_for_customer(customer_id, db_path, 180)
        citations['median_pay_gap'] = income_metrics.median_pay_gap_days
        citations['cash_flow_buffer'] = income_metrics.cash_flow_buffer_months
        citations['income_variability'] = income_metrics.income_variability
    
    elif persona_type == PersonaType.FINANCIAL_FRAGILITY:
        from ingest.queries import get_accounts_by_customer
        accounts = get_accounts_by_customer(customer_id, db_path)
        checking_accounts = [acc for acc in accounts if acc.subtype.value == "checking"]
        if checking_accounts:
            citations['checking_balance'] = checking_accounts[0].balances.current
    
    return citations


def generate_rationale_template(
    persona_type: PersonaType,
    recommendation_type: str,
    data_citations: Dict,
    content: Optional[EducationContent] = None,
    offer: Optional[PartnerOffer] = None
) -> str:
    """
    Generate plain-language rationale using templates (fallback method).
    
    Args:
        persona_type: PersonaType enum value
        recommendation_type: 'education' or 'offer'
        data_citations: Dictionary with supporting data
        content: Optional EducationContent object
        offer: Optional PartnerOffer object
        
    Returns:
        Plain-language rationale string
    """
    rationale = ""
    
    # Generate rationale based on persona and recommendation type
    if persona_type == PersonaType.HIGH_UTILIZATION:
        if recommendation_type == 'education':
            if 'utilization_percentage' in data_citations:
                utilization = data_citations['utilization_percentage']
                rationale = f"We noticed your credit card is at {utilization:.1f}% utilization. "
                if utilization >= 80:
                    rationale += "This high utilization can significantly impact your credit score and increase interest costs. "
                elif utilization >= 50:
                    rationale += "Keeping utilization above 50% can hurt your credit score and increase interest charges. "
                
                if 'monthly_interest' in data_citations and data_citations['monthly_interest'] > 0:
                    interest = data_citations['monthly_interest']
                    rationale += f"You're currently paying approximately ${interest:.2f} per month in interest. "
                
                if content:
                    rationale += f"{content.description} "
                    rationale += "This can help you reduce your utilization and save on interest."
        
        elif recommendation_type == 'offer':
            if offer:
                if offer.product_type.value == "balance_transfer_card":
                    if 'utilization_percentage' in data_citations:
                        utilization = data_citations['utilization_percentage']
                        rationale = f"Because your credit utilization is at {utilization:.1f}%, "
                        rationale += f"a balance transfer card with {offer.apr}% APR could help you save on interest while you pay down debt. "
                        rationale += f"{offer.description}"
    
    elif persona_type == PersonaType.SUBSCRIPTION_HEAVY:
        if recommendation_type == 'education':
            if 'subscription_count' in data_citations and 'monthly_recurring_spend' in data_citations:
                count = data_citations['subscription_count']
                spend = data_citations['monthly_recurring_spend']
                rationale = f"Your recurring subscriptions total ${spend:.2f} per month across {count} services. "
                
                if 'top_subscription' in data_citations:
                    top = data_citations['top_subscription']
                    top_amount = data_citations.get('top_subscription_amount', 0)
                    rationale += f"Your largest subscription is {top} at ${top_amount:.2f}/month. "
                
                if content:
                    rationale += f"{content.description} "
                    rationale += "This can help you identify subscriptions you may not need."
        
        elif recommendation_type == 'offer':
            if offer:
                rationale = f"Because you have {data_citations.get('subscription_count', 0)} recurring subscriptions, "
                rationale += f"{offer.description}"
    
    elif persona_type == PersonaType.SAVINGS_BUILDER:
        if recommendation_type == 'education':
            if 'growth_rate' in data_citations:
                growth = data_citations['growth_rate']
                rationale = f"Your savings are growing at {growth:.1f}% over the past 6 months. "
                
                if 'savings_balance' in data_citations:
                    balance = data_citations['savings_balance']
                    rationale += f"You currently have ${balance:,.2f} in savings. "
                
                if content:
                    rationale += f"{content.description} "
                    rationale += "This can help you optimize your savings strategy."
        
        elif recommendation_type == 'offer':
            if offer:
                if offer.product_type.value == "high_yield_savings_account":
                    if 'savings_balance' in data_citations:
                        balance = data_citations['savings_balance']
                        apy = offer.apy
                        rationale = f"Because you have ${balance:,.2f} in savings, "
                        rationale += f"a high-yield savings account with {apy}% APY could help you earn more interest. "
                        rationale += f"{offer.description}"
    
    elif persona_type == PersonaType.VARIABLE_INCOME_BUDGETER:
        if recommendation_type == 'education':
            if 'median_pay_gap' in data_citations:
                pay_gap = data_citations['median_pay_gap']
                rationale = f"Your median pay gap is {pay_gap:.1f} days between paychecks. "
                
                if 'cash_flow_buffer' in data_citations:
                    buffer = data_citations['cash_flow_buffer']
                    rationale += f"Your cash-flow buffer is {buffer:.1f} months. "
                
                if content:
                    rationale += f"{content.description} "
                    rationale += "This can help you manage irregular income more effectively."
    
    elif persona_type == PersonaType.FINANCIAL_FRAGILITY:
        if recommendation_type == 'education':
            if 'checking_balance' in data_citations:
                balance = data_citations['checking_balance']
                rationale = f"Your checking account balance is ${balance:.2f}. "
                
                if balance < 500:
                    rationale += "Building a buffer can help you avoid fees and manage unexpected expenses. "
                
                if content:
                    rationale += f"{content.description}"
    
    # Add "because" clause if we have data
    if rationale and not rationale.endswith("."):
        rationale += "."
    
    return rationale


def validate_tone(rationale: str) -> bool:
    """
    Validate that rationale doesn't contain shaming language.
    
    Args:
        rationale: Rationale string to validate
        
    Returns:
        True if tone is acceptable, False otherwise
    """
    shaming_keywords = [
        "you're overspending",
        "you're wasting money",
        "your savings rate is too low",
        "you should stop",
        "you're irresponsible",
        "you're bad with money",
        "you need to stop",
        "you're overspending"
    ]
    
    rationale_lower = rationale.lower()
    for keyword in shaming_keywords:
        if keyword in rationale_lower:
            return False
    
    return True


def generate_rationale(
    persona_type: PersonaType,
    recommendation_type: str,
    data_citations: Dict,
    content: Optional[EducationContent] = None,
    offer: Optional[PartnerOffer] = None,
    tone: Tone = Tone.SUPPORTIVE,
    use_llm: bool = True
) -> str:
    """
    Generate plain-language rationale for a recommendation using LLM with tone control.
    
    Args:
        persona_type: PersonaType enum value
        recommendation_type: 'education' or 'offer'
        data_citations: Dictionary with supporting data
        content: Optional EducationContent object
        offer: Optional PartnerOffer object
        tone: Tone enum value (default: SUPPORTIVE)
        use_llm: Whether to use LLM (default: True, falls back to templates if LLM unavailable)
        
    Returns:
        Plain-language rationale string
    """
    # Prepare fallback generator function
    def fallback_generator():
        return generate_rationale_template(
            persona_type, recommendation_type, data_citations, content, offer
        )
    
    # Use LLM if enabled
    if use_llm:
        try:
            # Determine appropriate tone based on persona
            if persona_type == PersonaType.FINANCIAL_FRAGILITY:
                tone = Tone.GENTLE  # Use gentler tone for fragile situations
            elif persona_type == PersonaType.SAVINGS_BUILDER:
                tone = Tone.EMPOWERING  # Empowering tone for positive progress
            
            # Generate using LLM
            rationale = generate_rationale_with_llm(
                recommendation_type=recommendation_type,
                data_citations=data_citations,
                tone=tone,
                persona_type=persona_type.value,
                content_title=content.title if content else None,
                content_description=content.description if content else None,
                offer_title=offer.title if offer else None,
                offer_description=offer.description if offer else None,
                fallback_generator=fallback_generator
            )
            
            # Validate tone
            if not validate_tone(rationale):
                logging.warning(f"LLM-generated rationale failed tone validation, using fallback")
                return fallback_generator()
            
            return rationale
        except Exception as e:
            logging.error(f"LLM generation failed: {str(e)}, using fallback")
            return fallback_generator()
    
    # Use template-based generation
    return fallback_generator()


def build_recommendations(
    customer_id: str,
    db_path: str,
    persona_assignment: PersonaAssignment,
    estimated_income: float = 0.0,
    estimated_credit_score: int = 700,
    check_consent: bool = True,
    grace_period_days: int = 0
) -> RecommendationSet:
    """
    Build complete recommendation set for a customer.
    
    Args:
        customer_id: Customer ID
        db_path: Path to SQLite database
        persona_assignment: PersonaAssignment object
        estimated_income: Estimated annual income
        estimated_credit_score: Estimated credit score
        check_consent: Whether to verify consent before building recommendations
        grace_period_days: Grace period in days after consent revocation
        
    Returns:
        RecommendationSet object (empty if consent check fails)
    """
    # Check consent if required
    if check_consent:
        is_consented, reason = verify_consent(
            customer_id,
            db_path,
            required_scope=ConsentScope.ALL,
            grace_period_days=grace_period_days
        )
        
        if not is_consented:
            # Return empty recommendations if consent check fails
            return RecommendationSet(
                customer_id=customer_id,
                persona_assignment=persona_assignment,
                education_items=[],
                partner_offers=[],
                generated_at=date.today()
            )
    
    # If no persona assigned, use fallback to generate generic recommendations
    if not persona_assignment.primary_persona:
        # Generate generic recommendations for customers without a specific persona
        # Use general financial education content
        from recommend.content_catalog import DEFAULT_CONTENT_CATALOG
        
        # Get general content (content that targets multiple personas or general advice)
        general_content = []
        for content in DEFAULT_CONTENT_CATALOG.values():
            # Include content that targets multiple personas or is beginner-friendly
            if len(content.target_personas) > 1 or content.difficulty.value == 'beginner':
                general_content.append(content)
        
        # Sort by estimated time and take top 5
        general_content.sort(key=lambda c: c.estimated_time_minutes)
        general_content = general_content[:5]
        
        # Build generic education recommendations
        education_items = []
        for i, content in enumerate(general_content):
            # Extract basic data citations
            basic_citations = extract_data_citations(customer_id, db_path, PersonaType.HIGH_UTILIZATION)  # Use any persona type for basic data
            
            rationale = f"{content.description} This general financial guidance can help improve your financial situation."
            
            recommendation = RecommendationItem(
                recommendation_id=f"REC-{customer_id}-EDU-GEN-{i+1}",
                type='education',
                title=content.title,
                description=content.description,
                rationale=rationale,
                content_id=content.content_id,
                priority=i+1,
                data_citations=basic_citations
            )
            education_items.append(recommendation)
        
        # Generate counterfactual scenarios (these don't require a persona)
        counterfactual_scenarios = generate_counterfactual_scenarios(customer_id, db_path)
        
        return RecommendationSet(
            customer_id=customer_id,
            persona_assignment=persona_assignment,
            education_items=education_items,
            partner_offers=[],  # No offers without persona
            counterfactual_scenarios=counterfactual_scenarios,
            generated_at=date.today()
        )
    
    persona_type = persona_assignment.primary_persona.persona_type
    
    # Extract data citations
    data_citations = extract_data_citations(customer_id, db_path, persona_type)
    
    # Get education content (3-5 items)
    education_content = get_content_for_persona(persona_type, limit=5)
    
    # Build education recommendations
    education_items = []
    for i, content in enumerate(education_content[:5]):  # Max 5 items
        data_citations_content = extract_data_citations(customer_id, db_path, persona_type)
        rationale = generate_rationale(persona_type, 'education', data_citations_content, content=content)
        
        # Validate tone
        if not validate_tone(rationale):
            # Regenerate with neutral tone
            rationale = f"{content.description} This can help you improve your financial situation."
        
        recommendation = RecommendationItem(
            recommendation_id=f"REC-{customer_id}-EDU-{i+1}",
            type='education',
            title=content.title,
            description=content.description,
            rationale=rationale,
            content_id=content.content_id,
            priority=i+1,
            data_citations=data_citations_content
        )
        education_items.append(recommendation)
    
    # Get eligible partner offers (1-3 items)
    eligible_offers = get_eligible_offers_for_persona(
        persona_type, customer_id, db_path,
        estimated_income=estimated_income,
        estimated_credit_score=estimated_credit_score
    )
    
    # Generate counterfactual scenarios
    counterfactual_scenarios = generate_counterfactual_scenarios(customer_id, db_path)
    
    # Build partner offer recommendations
    partner_items = []
    for i, offer in enumerate(eligible_offers[:3]):  # Max 3 offers
        data_citations_offer = extract_data_citations(customer_id, db_path, persona_type)
        rationale = generate_rationale(persona_type, 'offer', data_citations_offer, offer=offer)
        
        # Validate tone
        if not validate_tone(rationale):
            rationale = f"{offer.description} This may be suitable for your financial situation."
        
        recommendation = RecommendationItem(
            recommendation_id=f"REC-{customer_id}-OFFER-{i+1}",
            type='offer',
            title=offer.title,
            description=offer.description,
            rationale=rationale,
            offer_id=offer.offer_id,
            priority=i+1,
            data_citations=data_citations_offer
        )
        partner_items.append(recommendation)
    
    return RecommendationSet(
        customer_id=customer_id,
        persona_assignment=persona_assignment,
        education_items=education_items,
        partner_offers=partner_items,
        counterfactual_scenarios=counterfactual_scenarios,
        generated_at=date.today()
    )


def format_recommendations_for_api(recommendation_set: RecommendationSet) -> Dict:
    """
    Format recommendations for API response.
    
    Args:
        recommendation_set: RecommendationSet object
        
    Returns:
        Dictionary formatted for API
    """
    return {
        'customer_id': recommendation_set.customer_id,
        'generated_at': recommendation_set.generated_at.isoformat(),
        'persona': {
            'primary': recommendation_set.persona_assignment.primary_persona.persona_type.value if recommendation_set.persona_assignment.primary_persona else None,
            'secondary': recommendation_set.persona_assignment.secondary_persona.persona_type.value if recommendation_set.persona_assignment.secondary_persona else None,
            'window_30d': recommendation_set.persona_assignment.window_30d.persona_type.value if recommendation_set.persona_assignment.window_30d else None,
            'window_180d': recommendation_set.persona_assignment.window_180d.persona_type.value if recommendation_set.persona_assignment.window_180d else None
        },
        'education_items': [
            {
                'recommendation_id': rec.recommendation_id,
                'title': rec.title,
                'description': rec.description,
                'rationale': rec.rationale,
                'content_id': rec.content_id,
                'priority': rec.priority,
                'data_citations': rec.data_citations or {},
                'content_url': f"https://example.com/content/{rec.content_id}" if rec.content_id else None
            }
            for rec in recommendation_set.education_items
        ],
        'partner_offers': [
            {
                'recommendation_id': rec.recommendation_id,
                'title': rec.title,
                'description': rec.description,
                'rationale': rec.rationale,
                'offer_id': rec.offer_id,
                'priority': rec.priority,
                'data_citations': rec.data_citations or {},
                'eligibility_reason': rec.rationale.split('.')[0] if rec.rationale else None
            }
            for rec in recommendation_set.partner_offers
        ],
        'counterfactual_scenarios': [
            {
                'scenario_id': cf.scenario_id,
                'title': cf.title,
                'description': cf.description,
                'current_state': cf.current_state,
                'hypothetical_state': cf.hypothetical_state,
                'impact': cf.impact,
                'time_to_achieve': cf.time_to_achieve,
                'confidence': cf.confidence
            }
            for cf in recommendation_set.counterfactual_scenarios
        ],
        'disclaimer': recommendation_set.disclaimer
    }

