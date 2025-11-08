"""
Test recommendation engine end-to-end.

Tests the complete recommendation flow:
Persona → Content → Offers → Rationale
"""

from personas.persona_prioritization import assign_personas_with_prioritization
from recommend.recommendation_builder import build_recommendations, format_recommendations_for_api
import json

db_path = 'data/spendsense.db'
sample_customer = 'CUST000001'

print("="*60)
print("Testing Recommendation Engine")
print("="*60)
print()

# Step 1: Assign persona
print("[STEP 1] Assigning persona...")
persona_assignment = assign_personas_with_prioritization(sample_customer, db_path)

if persona_assignment.primary_persona:
    print(f"   Primary Persona: {persona_assignment.primary_persona.persona_type.value}")
    print(f"   Confidence: {persona_assignment.primary_persona.confidence_score:.2%}")
else:
    print("   No persona assigned")
    exit(1)

print()

# Step 2: Build recommendations
print("[STEP 2] Building recommendations...")
recommendations = build_recommendations(
    sample_customer,
    db_path,
    persona_assignment,
    estimated_income=50000.0,
    estimated_credit_score=700
)

print(f"   Education Items: {len(recommendations.education_items)}")
print(f"   Partner Offers: {len(recommendations.partner_offers)}")

print()

# Step 3: Display recommendations
print("[STEP 3] Education Recommendations")
print("-" * 60)
for i, item in enumerate(recommendations.education_items, 1):
    print(f"\n{i}. {item.title}")
    print(f"   Description: {item.description}")
    print(f"   Rationale: {item.rationale}")
    print(f"   Content ID: {item.content_id}")

print()

print("[STEP 4] Partner Offers")
print("-" * 60)
for i, item in enumerate(recommendations.partner_offers, 1):
    print(f"\n{i}. {item.title}")
    print(f"   Description: {item.description}")
    print(f"   Rationale: {item.rationale}")
    print(f"   Offer ID: {item.offer_id}")

print()

# Step 5: Format for API
print("[STEP 5] API Response Format")
print("-" * 60)
api_response = format_recommendations_for_api(recommendations)
print(json.dumps(api_response, indent=2))

print("\n" + "="*60)
print("[SUCCESS] Recommendation engine tested successfully!")
print("="*60)

