"""
Recommendation Engine for SpendSenseAI.

Provides:
- Education Content Catalog
- Partner Offer System with Eligibility
- Rationale Generation & Recommendation Builder
"""

from .content_catalog import (
    EducationContent,
    ContentType,
    ContentDifficulty,
    get_content_for_persona,
    get_content_by_id,
    search_content,
    load_content_catalog,
    save_content_catalog
)

from .partner_offers import (
    PartnerOffer,
    ProductType,
    EligibilityRule,
    check_eligibility,
    get_eligible_offers_for_persona,
    load_partner_offers
)

from .recommendation_builder import (
    RecommendationItem,
    RecommendationSet,
    build_recommendations,
    format_recommendations_for_api,
    extract_data_citations,
    generate_rationale,
    validate_tone
)

from .counterfactuals import (
    CounterfactualScenario,
    generate_counterfactual_scenarios,
    calculate_interest_savings,
    calculate_emergency_fund_timeline,
    calculate_subscription_savings,
    format_counterfactual_for_display
)

from .calculators import (
    CreditPayoffResult,
    EmergencyFundResult,
    SubscriptionAnalyzerResult,
    BudgetPlannerResult,
    calculate_credit_payoff,
    calculate_emergency_fund,
    analyze_subscription_costs,
    plan_variable_income_budget,
    get_calculator_results_for_user
)

from .notifications import (
    NotificationChannel,
    NotificationTrigger,
    NotificationTemplate,
    Notification,
    NotificationPreferences,
    personalize_template,
    should_send_notification,
    generate_notification_for_persona,
    create_notification_preferences,
    generate_notification_templates_for_personas,
    format_notification_for_display
)

__all__ = [
    # Content Catalog
    'EducationContent',
    'ContentType',
    'ContentDifficulty',
    'get_content_for_persona',
    'get_content_by_id',
    'search_content',
    'load_content_catalog',
    'save_content_catalog',
    
    # Partner Offers
    'PartnerOffer',
    'ProductType',
    'EligibilityRule',
    'check_eligibility',
    'get_eligible_offers_for_persona',
    'load_partner_offers',
    
    # Recommendation Builder
    'RecommendationItem',
    'RecommendationSet',
    'build_recommendations',
    'format_recommendations_for_api',
    'extract_data_citations',
    'generate_rationale',
    'validate_tone',
    
    # Counterfactuals
    'CounterfactualScenario',
    'generate_counterfactual_scenarios',
    'calculate_interest_savings',
    'calculate_emergency_fund_timeline',
    'calculate_subscription_savings',
    'format_counterfactual_for_display',
    
    # Calculators
    'CreditPayoffResult',
    'EmergencyFundResult',
    'SubscriptionAnalyzerResult',
    'BudgetPlannerResult',
    'calculate_credit_payoff',
    'calculate_emergency_fund',
    'analyze_subscription_costs',
    'plan_variable_income_budget',
    'get_calculator_results_for_user',
    
    # Notifications
    'NotificationChannel',
    'NotificationTrigger',
    'NotificationTemplate',
    'Notification',
    'NotificationPreferences',
    'personalize_template',
    'should_send_notification',
    'generate_notification_for_persona',
    'create_notification_preferences',
    'generate_notification_templates_for_personas',
    'format_notification_for_display'
]
