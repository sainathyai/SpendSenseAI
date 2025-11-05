"""
Persona Prioritization & Conflict Resolution for SpendSenseAI.

Handles users matching multiple personas with prioritization rules:
1. High Utilization (immediate financial risk)
2. Financial Fragility (if implemented)
3. Variable Income Budgeter (income instability)
4. Subscription-Heavy (spending optimization)
5. Savings Builder (growth opportunity)
"""

from typing import List, Optional, Dict
from datetime import date
from dataclasses import dataclass

from personas.persona_definition import PersonaMatch, PersonaType, PersonaAssignment
from personas.financial_fragility import check_financial_fragility_persona


# Persona priority order (lower number = higher priority)
PERSONA_PRIORITY = {
    PersonaType.HIGH_UTILIZATION: 1,  # Highest priority - immediate financial risk
    PersonaType.FINANCIAL_FRAGILITY: 2,  # Second priority - immediate financial stress
    PersonaType.VARIABLE_INCOME_BUDGETER: 3,  # Third priority - income instability
    PersonaType.SUBSCRIPTION_HEAVY: 4,  # Fourth priority - spending optimization
    PersonaType.SAVINGS_BUILDER: 5,  # Lowest priority - growth opportunity
}


def prioritize_personas(personas: List[PersonaMatch]) -> List[PersonaMatch]:
    """
    Prioritize personas based on priority rules.
    
    Args:
        personas: List of PersonaMatch objects
        
    Returns:
        Sorted list of personas (highest priority first)
    """
    if not personas:
        return []
    
    # Sort by priority (lower number = higher priority)
    # Then by confidence score (higher confidence = higher priority)
    sorted_personas = sorted(
        personas,
        key=lambda p: (
            PERSONA_PRIORITY.get(p.persona_type, 999),  # Priority order
            -p.confidence_score  # Negative for descending confidence
        )
    )
    
    return sorted_personas


def assign_primary_and_secondary(
    personas: List[PersonaMatch]
) -> tuple[Optional[PersonaMatch], Optional[PersonaMatch]]:
    """
    Assign primary and secondary personas from matched personas.
    
    Args:
        personas: List of PersonaMatch objects (should be prioritized)
        
    Returns:
        Tuple of (primary_persona, secondary_persona)
    """
    if not personas:
        return None, None
    
    primary = personas[0] if personas else None
    
    # Secondary is the next highest priority persona that's different
    secondary = None
    for persona in personas[1:]:
        if persona.persona_type != primary.persona_type:
            secondary = persona
            break
    
    return primary, secondary


def check_temporal_consistency(
    persona_30d: Optional[PersonaMatch],
    persona_180d: Optional[PersonaMatch]
) -> Dict[str, any]:
    """
    Check temporal consistency between 30-day and 180-day personas.
    
    Args:
        persona_30d: Persona match for 30-day window
        persona_180d: Persona match for 180-day window
        
    Returns:
        Dictionary with consistency information
    """
    if not persona_30d and not persona_180d:
        return {
            'is_consistent': True,
            'consistency_score': 1.0,
            'primary_window': None,
            'reason': 'No personas matched'
        }
    
    if not persona_30d:
        return {
            'is_consistent': True,
            'consistency_score': 1.0,
            'primary_window': '180d',
            'reason': 'Only 180-day persona matched'
        }
    
    if not persona_180d:
        return {
            'is_consistent': True,
            'consistency_score': 1.0,
            'primary_window': '30d',
            'reason': 'Only 30-day persona matched'
        }
    
    # Both personas exist - check if they match
    if persona_30d.persona_type == persona_180d.persona_type:
        return {
            'is_consistent': True,
            'consistency_score': 1.0,
            'primary_window': '180d',
            'reason': 'Same persona in both windows'
        }
    else:
        # Different personas - check if they're compatible
        # Some personas can coexist (e.g., High Utilization + Financial Fragility)
        # Others are mutually exclusive (e.g., High Utilization + Savings Builder)
        
        compatible_pairs = [
            (PersonaType.HIGH_UTILIZATION, PersonaType.FINANCIAL_FRAGILITY),
            (PersonaType.VARIABLE_INCOME_BUDGETER, PersonaType.SUBSCRIPTION_HEAVY),
            (PersonaType.SUBSCRIPTION_HEAVY, PersonaType.SAVINGS_BUILDER),
        ]
        
        pair = (persona_30d.persona_type, persona_180d.persona_type)
        reverse_pair = (persona_180d.persona_type, persona_30d.persona_type)
        
        is_compatible = pair in compatible_pairs or reverse_pair in compatible_pairs
        
        return {
            'is_consistent': is_compatible,
            'consistency_score': 0.5 if is_compatible else 0.3,
            'primary_window': '180d',  # Use 180-day as primary
            'reason': 'Different personas, compatible' if is_compatible else 'Different personas, conflicting'
        }


def assign_personas_with_prioritization(
    customer_id: str,
    db_path: str
) -> PersonaAssignment:
    """
    Assign personas with prioritization and conflict resolution.
    
    Args:
        customer_id: Customer ID
        db_path: Path to SQLite database
        
    Returns:
        PersonaAssignment object with primary and secondary personas
    """
    from personas.persona_definition import (
        check_high_utilization_persona,
        check_variable_income_budgeter_persona,
        check_subscription_heavy_persona,
        check_savings_builder_persona
    )
    
    # Collect all persona matches for 30-day window
    personas_30d = []
    
    high_util_30d = check_high_utilization_persona(customer_id, db_path, 30)
    if high_util_30d:
        personas_30d.append(high_util_30d)
    
    financial_fragility_30d = check_financial_fragility_persona(customer_id, db_path, 30)
    if financial_fragility_30d:
        personas_30d.append(financial_fragility_30d)
    
    variable_income_30d = check_variable_income_budgeter_persona(customer_id, db_path, 30)
    if variable_income_30d:
        personas_30d.append(variable_income_30d)
    
    subscription_heavy_30d = check_subscription_heavy_persona(customer_id, db_path, 30)
    if subscription_heavy_30d:
        personas_30d.append(subscription_heavy_30d)
    
    savings_builder_30d = check_savings_builder_persona(customer_id, db_path, 30)
    if savings_builder_30d:
        personas_30d.append(savings_builder_30d)
    
    # Collect all persona matches for 180-day window
    personas_180d = []
    
    high_util_180d = check_high_utilization_persona(customer_id, db_path, 180)
    if high_util_180d:
        personas_180d.append(high_util_180d)
    
    financial_fragility_180d = check_financial_fragility_persona(customer_id, db_path, 180)
    if financial_fragility_180d:
        personas_180d.append(financial_fragility_180d)
    
    variable_income_180d = check_variable_income_budgeter_persona(customer_id, db_path, 180)
    if variable_income_180d:
        personas_180d.append(variable_income_180d)
    
    subscription_heavy_180d = check_subscription_heavy_persona(customer_id, db_path, 180)
    if subscription_heavy_180d:
        personas_180d.append(subscription_heavy_180d)
    
    savings_builder_180d = check_savings_builder_persona(customer_id, db_path, 180)
    if savings_builder_180d:
        personas_180d.append(savings_builder_180d)
    
    # Prioritize personas
    personas_30d_sorted = prioritize_personas(personas_30d)
    personas_180d_sorted = prioritize_personas(personas_180d)
    
    # Get primary personas for each window
    persona_30d = personas_30d_sorted[0] if personas_30d_sorted else None
    persona_180d = personas_180d_sorted[0] if personas_180d_sorted else None
    
    # Check temporal consistency
    consistency = check_temporal_consistency(persona_30d, persona_180d)
    
    # Assign primary and secondary
    # Primary is usually 180-day (longer-term pattern)
    # Secondary is 30-day if different persona type from primary
    primary = persona_180d if persona_180d else persona_30d
    secondary = None
    
    # Find secondary from all matched personas (different type)
    if primary:
        # Combine all personas from both windows
        all_personas = personas_30d_sorted + personas_180d_sorted
        
        # Find next highest priority persona that's different
        for persona in all_personas:
            if persona.persona_type != primary.persona_type:
                secondary = persona
                break
    
    # If primary is 30-day and secondary is 180-day, swap them
    # (180-day should be primary as it's longer-term)
    if primary == persona_30d and secondary == persona_180d:
        primary, secondary = secondary, primary
    
    return PersonaAssignment(
        customer_id=customer_id,
        primary_persona=primary,
        secondary_persona=secondary,
        window_30d=persona_30d,
        window_180d=persona_180d,
        assigned_at=date.today()
    )


def get_persona_priority(persona_type: PersonaType) -> int:
    """
    Get priority number for a persona type.
    
    Args:
        persona_type: PersonaType enum value
        
    Returns:
        Priority number (lower = higher priority)
    """
    return PERSONA_PRIORITY.get(persona_type, 999)


def format_persona_assignment(assignment: PersonaAssignment) -> Dict:
    """
    Format persona assignment for display/API.
    
    Args:
        assignment: PersonaAssignment object
        
    Returns:
        Dictionary with formatted assignment data
    """
    result = {
        'customer_id': assignment.customer_id,
        'assigned_at': assignment.assigned_at.isoformat(),
        'primary_persona': None,
        'secondary_persona': None,
        'window_30d': None,
        'window_180d': None
    }
    
    if assignment.primary_persona:
        result['primary_persona'] = {
            'type': assignment.primary_persona.persona_type.value,
            'confidence': assignment.primary_persona.confidence_score,
            'criteria_met': assignment.primary_persona.criteria_met,
            'focus_areas': assignment.primary_persona.focus_areas,
            'window_days': assignment.primary_persona.window_days
        }
    
    if assignment.secondary_persona:
        result['secondary_persona'] = {
            'type': assignment.secondary_persona.persona_type.value,
            'confidence': assignment.secondary_persona.confidence_score,
            'criteria_met': assignment.secondary_persona.criteria_met,
            'focus_areas': assignment.secondary_persona.focus_areas,
            'window_days': assignment.secondary_persona.window_days
        }
    
    if assignment.window_30d:
        result['window_30d'] = {
            'type': assignment.window_30d.persona_type.value,
            'confidence': assignment.window_30d.confidence_score,
            'criteria_met': assignment.window_30d.criteria_met
        }
    
    if assignment.window_180d:
        result['window_180d'] = {
            'type': assignment.window_180d.persona_type.value,
            'confidence': assignment.window_180d.confidence_score,
            'criteria_met': assignment.window_180d.criteria_met
        }
    
    return result

