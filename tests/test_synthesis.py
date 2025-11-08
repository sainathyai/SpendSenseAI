"""
Unit tests for data synthesis module.

These tests validate the synthesis algorithms work correctly.
"""

import pytest
import pandas as pd
from datetime import date, timedelta
from pathlib import Path

from ingest.synthesis import (
    discover_accounts,
    calculate_account_balances,
    enhance_transactions,
    generate_merchant_name,
    synthesize_liabilities,
    synthesize_apr,
    calculate_minimum_payment,
    determine_overdue_status,
    estimate_next_payment_due_date,
    synthesize_data
)
from ingest.schemas import AccountType, AccountSubtype, PaymentChannel
from ingest.exporter import export_all_to_csv, export_to_json


def test_generate_merchant_name():
    """Test merchant name generation is deterministic."""
    name1 = generate_merchant_name("MERCH000159", "groceries")
    name2 = generate_merchant_name("MERCH000159", "groceries")
    
    # Same merchant_id should produce same name
    assert name1 == name2
    
    # Different merchant_id should produce different name
    name3 = generate_merchant_name("MERCH000160", "groceries")
    assert name1 != name3
    
    # Name should contain merchant number
    assert "#159" in name1 or "159" in name1


def test_calculate_minimum_payment():
    """Test minimum payment calculation."""
    # Test 2% calculation
    assert calculate_minimum_payment(1000.0) == 25.0  # $25 minimum
    
    # Test 2% of larger balance
    assert calculate_minimum_payment(5000.0) == 100.0  # 2% of $5000
    
    # Test zero balance
    assert calculate_minimum_payment(0.0) == 0.0
    
    # Test negative balance
    assert calculate_minimum_payment(-100.0) == 0.0


def test_synthesize_apr():
    """Test APR synthesis based on utilization."""
    from ingest.schemas import Account, AccountBalances, HolderCategory
    
    # Low utilization (good credit)
    account_low = Account(
        account_id="ACC-TEST-CREDIT-1",
        customer_id="TEST",
        type=AccountType.CREDIT,
        subtype=AccountSubtype.CREDIT_CARD,
        balances=AccountBalances(current=1000.0, limit=5000.0),
        holder_category=HolderCategory.CONSUMER
    )
    aprs_low = synthesize_apr(account_low)
    assert len(aprs_low) > 0
    assert aprs_low[0].percentage <= 22.99  # Should be 18.99% for low utilization
    
    # High utilization (high risk)
    account_high = Account(
        account_id="ACC-TEST-CREDIT-2",
        customer_id="TEST",
        type=AccountType.CREDIT,
        subtype=AccountSubtype.CREDIT_CARD,
        balances=AccountBalances(current=4500.0, limit=5000.0),
        holder_category=HolderCategory.CONSUMER
    )
    aprs_high = synthesize_apr(account_high)
    assert aprs_high[0].percentage >= 25.99  # Should be higher for high utilization


def test_determine_overdue_status():
    """Test overdue status determination."""
    from datetime import date
    
    # No balance, not overdue
    assert determine_overdue_status([], 0.0) == False
    
    # Balance with recent payment, not overdue
    recent_payment = [{'date': date.today() - timedelta(days=10), 'amount': 100.0}]
    assert determine_overdue_status(recent_payment, 1000.0) == False
    
    # Balance with old payment, overdue
    old_payment = [{'date': date.today() - timedelta(days=35), 'amount': 100.0}]
    assert determine_overdue_status(old_payment, 1000.0) == True
    
    # No payment history, overdue
    assert determine_overdue_status([], 1000.0) == True


def test_estimate_next_payment_due_date():
    """Test next payment due date estimation."""
    from datetime import date
    
    # Not enough history, default to 30 days
    history_short = [{'date': date.today() - timedelta(days=10), 'amount': 100.0}]
    due_date = estimate_next_payment_due_date(history_short)
    assert due_date > date.today()
    assert (due_date - date.today()).days <= 30
    
    # With history, estimate from average interval
    history = [
        {'date': date.today() - timedelta(days=10), 'amount': 100.0},
        {'date': date.today() - timedelta(days=40), 'amount': 100.0},
    ]
    due_date = estimate_next_payment_due_date(history)
    assert due_date > date.today()


def test_synthesize_data_integration():
    """Integration test for full data synthesis."""
    # Create sample CSV data
    sample_data = {
        'transaction_id': ['TXN001', 'TXN002', 'TXN003'],
        'customer_id': ['CUST001', 'CUST001', 'CUST002'],
        'merchant_id': ['MERCH001', 'MERCH002', 'MERCH003'],
        'merchant_category': ['groceries', 'gas_station', 'restaurant'],
        'transaction_type': ['purchase', 'purchase', 'purchase'],
        'payment_method': ['debit_card', 'debit_card', 'credit_card'],
        'amount': [100.0, 50.0, 75.0],
        'account_balance': [900.0, 850.0, 5000.0],
        'status': ['approved', 'approved', 'approved'],
        'date': ['2024-01-01', '2024-01-02', '2024-01-03']
    }
    
    # Create temporary CSV
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        df = pd.DataFrame(sample_data)
        df.to_csv(f.name, index=False)
        
        try:
            # Run synthesis
            accounts, transactions, liabilities = synthesize_data(f.name)
            
            # Validate output
            assert len(accounts) > 0, "Should have at least one account"
            assert len(transactions) > 0, "Should have at least one transaction"
            
            # Check accounts have required fields
            for account in accounts:
                assert account.account_id is not None
                assert account.customer_id is not None
                assert account.type in [AccountType.DEPOSITORY, AccountType.CREDIT]
                assert account.balances.current is not None
            
            # Check transactions have required fields
            for transaction in transactions:
                assert transaction.transaction_id is not None
                assert transaction.account_id is not None
                assert transaction.merchant_name is not None or transaction.merchant_entity_id is not None
                assert transaction.payment_channel in PaymentChannel
            
            # Check liabilities for credit cards
            credit_accounts = [acc for acc in accounts if acc.type == AccountType.CREDIT]
            if credit_accounts:
                assert len(liabilities) > 0, "Should have liabilities for credit cards"
                for liability in liabilities:
                    assert liability.account_id is not None
                    assert len(liability.aprs) > 0
                    assert liability.minimum_payment_amount > 0
        
        finally:
            # Clean up
            import os
            os.unlink(f.name)


if __name__ == '__main__':
    # Run tests
    pytest.main([__file__, '-v'])

