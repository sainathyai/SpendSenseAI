#!/usr/bin/env python3
"""
Test Counterfactual Scenario Generation
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from recommend.counterfactuals import generate_counterfactual_scenarios, format_counterfactual_for_display
from ingest.queries import get_all_customers

DB_PATH = "data/spendsense.db"

def test_counterfactuals():
    """Test counterfactual generation for multiple customers."""
    print("=" * 70)
    print("Testing Counterfactual Scenario Generation")
    print("=" * 70)
    
    # Get first 10 customers
    all_customers = get_all_customers(DB_PATH)
    customers = [c.customer_id if hasattr(c, 'customer_id') else c for c in all_customers[:10]]
    
    total_scenarios = 0
    customers_with_scenarios = 0
    
    print(f"\nTesting {len(customers)} customers...\n")
    
    for customer_id in customers:
        scenarios = generate_counterfactual_scenarios(customer_id, DB_PATH)
        
        if scenarios:
            customers_with_scenarios += 1
            total_scenarios += len(scenarios)
            
            print(f"\n{'='*70}")
            print(f"Customer: {customer_id}")
            print(f"   Scenarios Generated: {len(scenarios)}")
            print(f"{'='*70}")
            
            for i, scenario in enumerate(scenarios, 1):
                print(f"\n{i}. {scenario.title}")
                print(f"   ID: {scenario.scenario_id}")
                print(f"   Confidence: {scenario.confidence:.0%}")
                print(f"   {scenario.description}")
                
                # Show key impact metrics
                if scenario.impact:
                    print(f"\n   Key Impacts:")
                    for key, value in list(scenario.impact.items())[:3]:  # Show first 3
                        if isinstance(value, float):
                            if 'savings' in key.lower():
                                print(f"      • {key.replace('_', ' ').title()}: ${value:,.2f}")
                            else:
                                print(f"      • {key.replace('_', ' ').title()}: {value:,.0f}")
                        elif isinstance(value, list):
                            print(f"      • {key.replace('_', ' ').title()}: {', '.join(str(v) for v in value[:3])}")
                        else:
                            print(f"      • {key.replace('_', ' ').title()}: {value}")
                
                if scenario.time_to_achieve:
                    print(f"   Time to Achieve: {scenario.time_to_achieve}")
        else:
            print(f"   {customer_id}: No scenarios generated")
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Customers tested: {len(customers)}")
    print(f"Customers with scenarios: {customers_with_scenarios} ({customers_with_scenarios/len(customers):.1%})")
    print(f"Total scenarios generated: {total_scenarios}")
    print(f"Average scenarios per customer: {total_scenarios/len(customers):.1f}")
    
    if customers_with_scenarios > 0:
        print("\nSUCCESS: Counterfactual generation working!")
    else:
        print("\nFAIL: No counterfactuals generated - check data")
    
    return customers_with_scenarios > 0


if __name__ == "__main__":
    success = test_counterfactuals()
    sys.exit(0 if success else 1)

