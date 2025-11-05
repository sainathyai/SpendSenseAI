"""
Unit tests for persona system.
"""

import pytest
from datetime import date, timedelta
from personas.persona_definition import (
    PersonaType, PersonaMatch, check_high_utilization_persona,
    check_variable_income_budgeter_persona, check_subscription_heavy_persona,
    check_savings_builder_persona
)
from personas.financial_fragility import check_financial_fragility_persona
from personas.persona_prioritization import (
    prioritize_personas, assign_primary_and_secondary,
    check_temporal_consistency, PERSONA_PRIORITY
)


class TestPersonaPriority:
    """Test persona prioritization."""
    
    def test_priority_order(self):
        """Test that priority order is correct."""
        assert PERSONA_PRIORITY[PersonaType.HIGH_UTILIZATION] == 1
        assert PERSONA_PRIORITY[PersonaType.FINANCIAL_FRAGILITY] == 2
        assert PERSONA_PRIORITY[PersonaType.VARIABLE_INCOME_BUDGETER] == 3
        assert PERSONA_PRIORITY[PersonaType.SUBSCRIPTION_HEAVY] == 4
        assert PERSONA_PRIORITY[PersonaType.SAVINGS_BUILDER] == 5
    
    def test_prioritize_personas(self):
        """Test persona prioritization."""
        personas = [
            PersonaMatch(
                persona_type=PersonaType.SAVINGS_BUILDER,
                confidence_score=0.9,
                criteria_met=["Growth rate ≥2%"],
                window_days=180,
                focus_areas=["Goal setting"],
                supporting_data={}
            ),
            PersonaMatch(
                persona_type=PersonaType.HIGH_UTILIZATION,
                confidence_score=0.7,
                criteria_met=["Utilization ≥50%"],
                window_days=180,
                focus_areas=["Debt reduction"],
                supporting_data={}
            ),
        ]
        
        prioritized = prioritize_personas(personas)
        
        assert len(prioritized) == 2
        assert prioritized[0].persona_type == PersonaType.HIGH_UTILIZATION
        assert prioritized[1].persona_type == PersonaType.SAVINGS_BUILDER
    
    def test_assign_primary_secondary(self):
        """Test primary and secondary persona assignment."""
        personas = [
            PersonaMatch(
                persona_type=PersonaType.HIGH_UTILIZATION,
                confidence_score=0.9,
                criteria_met=["Utilization ≥50%"],
                window_days=180,
                focus_areas=["Debt reduction"],
                supporting_data={}
            ),
            PersonaMatch(
                persona_type=PersonaType.SUBSCRIPTION_HEAVY,
                confidence_score=0.8,
                criteria_met=["3+ subscriptions"],
                window_days=180,
                focus_areas=["Subscription audit"],
                supporting_data={}
            ),
        ]
        
        primary, secondary = assign_primary_and_secondary(personas)
        
        assert primary.persona_type == PersonaType.HIGH_UTILIZATION
        assert secondary.persona_type == PersonaType.SUBSCRIPTION_HEAVY
    
    def test_temporal_consistency_same_persona(self):
        """Test temporal consistency with same persona."""
        persona_30d = PersonaMatch(
            persona_type=PersonaType.HIGH_UTILIZATION,
            confidence_score=0.9,
            criteria_met=["Utilization ≥50%"],
            window_days=30,
            focus_areas=["Debt reduction"],
            supporting_data={}
        )
        
        persona_180d = PersonaMatch(
            persona_type=PersonaType.HIGH_UTILIZATION,
            confidence_score=0.85,
            criteria_met=["Utilization ≥50%"],
            window_days=180,
            focus_areas=["Debt reduction"],
            supporting_data={}
        )
        
        consistency = check_temporal_consistency(persona_30d, persona_180d)
        
        assert consistency['is_consistent'] is True
        assert consistency['consistency_score'] == 1.0
    
    def test_temporal_consistency_different_personas(self):
        """Test temporal consistency with different personas."""
        persona_30d = PersonaMatch(
            persona_type=PersonaType.HIGH_UTILIZATION,
            confidence_score=0.9,
            criteria_met=["Utilization ≥50%"],
            window_days=30,
            focus_areas=["Debt reduction"],
            supporting_data={}
        )
        
        persona_180d = PersonaMatch(
            persona_type=PersonaType.SAVINGS_BUILDER,
            confidence_score=0.8,
            criteria_met=["Growth rate ≥2%"],
            window_days=180,
            focus_areas=["Goal setting"],
            supporting_data={}
        )
        
        consistency = check_temporal_consistency(persona_30d, persona_180d)
        
        # These are conflicting (High Utilization vs Savings Builder)
        assert consistency['is_consistent'] is False
        assert consistency['consistency_score'] < 1.0


# Note: Integration tests with actual database would require test database setup
# These are unit tests for the logic functions

