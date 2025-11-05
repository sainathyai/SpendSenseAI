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
    'validate_tone'
]
