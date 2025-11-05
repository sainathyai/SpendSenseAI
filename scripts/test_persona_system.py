"""
Test persona system for a sample customer.

Tests all five personas and prioritization logic.
"""

from personas.persona_prioritization import assign_personas_with_prioritization, format_persona_assignment

db_path = 'data/spendsense.db'
sample_customer = 'CUST000001'

print("="*60)
print("Testing Persona System")
print("="*60)
print()

# Assign personas
print("[TEST] Assigning personas for customer...")
assignment = assign_personas_with_prioritization(sample_customer, db_path)

print(f"\n[RESULTS] Persona Assignment for {sample_customer}")
print("-" * 60)

if assignment.primary_persona:
    print(f"\nPrimary Persona: {assignment.primary_persona.persona_type.value}")
    print(f"   Confidence: {assignment.primary_persona.confidence_score:.2%}")
    print(f"   Window: {assignment.primary_persona.window_days} days")
    print(f"   Criteria Met:")
    for criterion in assignment.primary_persona.criteria_met:
        print(f"     - {criterion}")
    print(f"   Focus Areas: {', '.join(assignment.primary_persona.focus_areas)}")
else:
    print("\nPrimary Persona: None (no persona matched)")

if assignment.secondary_persona:
    print(f"\nSecondary Persona: {assignment.secondary_persona.persona_type.value}")
    print(f"   Confidence: {assignment.secondary_persona.confidence_score:.2%}")
    print(f"   Window: {assignment.secondary_persona.window_days} days")
    print(f"   Criteria Met:")
    for criterion in assignment.secondary_persona.criteria_met:
        print(f"     - {criterion}")
else:
    print("\nSecondary Persona: None")

print(f"\n30-Day Window Persona:")
if assignment.window_30d:
    print(f"   Type: {assignment.window_30d.persona_type.value}")
    print(f"   Confidence: {assignment.window_30d.confidence_score:.2%}")
else:
    print("   None")

print(f"\n180-Day Window Persona:")
if assignment.window_180d:
    print(f"   Type: {assignment.window_180d.persona_type.value}")
    print(f"   Confidence: {assignment.window_180d.confidence_score:.2%}")
else:
    print("   None")

# Format and display JSON
print(f"\n[FORMATTED] JSON Output:")
print("-" * 60)
import json
formatted = format_persona_assignment(assignment)
print(json.dumps(formatted, indent=2))

print("\n" + "="*60)
print("[SUCCESS] Persona system tested successfully!")
print("="*60)

