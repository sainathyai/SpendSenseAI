"""
Unit tests for recommendation engine.

Tests:
- Content catalog loading and retrieval
- Partner offer eligibility
- Rationale generation
- Recommendation building
"""

import pytest
from datetime import date
from pathlib import Path
import tempfile
import json

from personas.persona_definition import PersonaType, PersonaMatch, PersonaAssignment
from recommend.content_catalog import (
    EducationContent, ContentType, ContentDifficulty,
    get_content_for_persona, get_content_by_id, search_content
)
from recommend.partner_offers import (
    PartnerOffer, ProductType, EligibilityRule,
    check_eligibility, get_eligible_offers_for_persona
)
from recommend.recommendation_builder import (
    RecommendationItem, RecommendationSet,
    extract_data_citations, generate_rationale, validate_tone
)


class TestContentCatalog:
    """Test content catalog functionality."""
    
    def test_get_content_for_persona(self):
        """Test getting content for a persona."""
        content = get_content_for_persona(PersonaType.HIGH_UTILIZATION)
        assert len(content) > 0
        assert all(isinstance(c, EducationContent) for c in content)
        assert all(PersonaType.HIGH_UTILIZATION in c.target_personas for c in content)
    
    def test_get_content_by_id(self):
        """Test getting content by ID."""
        content = get_content_by_id("CONTENT-HU-001")
        assert content is not None
        assert content.content_id == "CONTENT-HU-001"
        assert content.title is not None
    
    def test_search_content(self):
        """Test searching content."""
        results = search_content("debt")
        assert len(results) > 0
        assert all("debt" in c.title.lower() or "debt" in c.description.lower() or any("debt" in tag.lower() for tag in c.tags) for c in results)
    
    def test_search_content_with_persona_filter(self):
        """Test searching content with persona filter."""
        results = search_content("budget", persona_type=PersonaType.VARIABLE_INCOME_BUDGETER)
        assert len(results) > 0
        assert all(PersonaType.VARIABLE_INCOME_BUDGETER in c.target_personas for c in results)


class TestPartnerOffers:
    """Test partner offers functionality."""
    
    def test_check_eligibility_basic(self):
        """Test basic eligibility checking."""
        # Create a simple offer
        offer = PartnerOffer(
            offer_id="TEST-OFFER",
            product_type=ProductType.HYSA,
            provider="Test Bank",
            title="Test Offer",
            description="Test description",
            benefits=["Benefit 1"],
            requirements=["Requirement 1"],
            eligibility_rules=EligibilityRule(
                min_income=30000.0,
                min_credit_score=650
            ),
            target_personas=[PersonaType.SAVINGS_BUILDER]
        )
        
        # Mock database path (won't actually query)
        db_path = "data/spendsense.db"
        
        # Test with sufficient income and credit score
        is_eligible, reasons = check_eligibility(
            offer, "CUST000001", db_path,
            persona_type=PersonaType.SAVINGS_BUILDER,
            estimated_income=50000.0,
            estimated_credit_score=700
        )
        
        # Should be eligible or have specific reasons
        assert isinstance(is_eligible, bool)
        assert isinstance(reasons, list)
    
    def test_harmful_product_blacklist(self):
        """Test that harmful products are rejected."""
        offer = PartnerOffer(
            offer_id="HARMFUL-OFFER",
            product_type=ProductType.PERSONAL_LOAN,
            provider="Predatory Lender",
            title="Payday Loan",
            description="Harmful product",
            benefits=[],
            requirements=[],
            eligibility_rules=EligibilityRule(),
            target_personas=[],
            is_harmful=True
        )
        
        db_path = "data/spendsense.db"
        is_eligible, reasons = check_eligibility(
            offer, "CUST000001", db_path,
            estimated_income=50000.0,
            estimated_credit_score=700
        )
        
        assert not is_eligible
        assert any("harmful" in reason.lower() for reason in reasons)


class TestRationaleGeneration:
    """Test rationale generation."""
    
    def test_validate_tone_acceptable(self):
        """Test tone validation with acceptable language."""
        rationale = "We noticed your credit utilization is at 68%. This high utilization can impact your credit score."
        assert validate_tone(rationale) is True
    
    def test_validate_tone_shaming(self):
        """Test tone validation with shaming language."""
        rationale = "You're overspending and need to stop wasting money."
        assert validate_tone(rationale) is False
    
    def test_generate_rationale_high_utilization(self):
        """Test rationale generation for high utilization persona."""
        data_citations = {
            'utilization_percentage': 68.5,
            'monthly_interest': 45.23
        }
        
        rationale = generate_rationale(
            PersonaType.HIGH_UTILIZATION,
            'education',
            data_citations
        )
        
        assert isinstance(rationale, str)
        assert len(rationale) > 0
        assert validate_tone(rationale) is True
    
    def test_generate_rationale_subscription_heavy(self):
        """Test rationale generation for subscription-heavy persona."""
        data_citations = {
            'subscription_count': 5,
            'monthly_recurring_spend': 147.50,
            'top_subscription': 'Netflix',
            'top_subscription_amount': 15.99
        }
        
        rationale = generate_rationale(
            PersonaType.SUBSCRIPTION_HEAVY,
            'education',
            data_citations
        )
        
        assert isinstance(rationale, str)
        assert "subscription" in rationale.lower() or "recurring" in rationale.lower()


class TestRecommendationSet:
    """Test recommendation set structure."""
    
    def test_recommendation_item(self):
        """Test RecommendationItem structure."""
        item = RecommendationItem(
            recommendation_id="REC-001",
            type="education",
            title="Test Title",
            description="Test Description",
            rationale="Test Rationale",
            content_id="CONTENT-001",
            priority=1
        )
        
        assert item.recommendation_id == "REC-001"
        assert item.type == "education"
        assert item.content_id == "CONTENT-001"
        assert item.offer_id is None
    
    def test_recommendation_set(self):
        """Test RecommendationSet structure."""
        persona_match = PersonaMatch(
            persona_type=PersonaType.HIGH_UTILIZATION,
            confidence_score=0.85,
            supporting_data={}
        )
        
        persona_assignment = PersonaAssignment(
            primary_persona=persona_match,
            secondary_persona=None,
            window_30d=persona_match,
            window_180d=persona_match
        )
        
        rec_set = RecommendationSet(
            customer_id="CUST001",
            persona_assignment=persona_assignment,
            education_items=[],
            partner_offers=[],
            generated_at=date.today()
        )
        
        assert rec_set.customer_id == "CUST001"
        assert rec_set.persona_assignment.primary_persona is not None
        assert len(rec_set.education_items) == 0
        assert len(rec_set.partner_offers) == 0

