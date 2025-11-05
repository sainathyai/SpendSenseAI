"""
Financial Fragility Persona (Custom 5th Persona) for SpendSenseAI.

This persona addresses immediate financial stress not captured by other personas:
- Overdrafts in past 30 days
- Checking balance < $500 consistently
- Late fees present
"""

from typing import Optional, List
from datetime import date, timedelta
from dataclasses import dataclass

from personas.persona_definition import PersonaMatch, PersonaType
from ingest.queries import (
    get_accounts_by_customer,
    get_transactions_by_account
)
from ingest.schemas import AccountType, AccountSubtype


def check_overdrafts(
    transactions: List,
    window_days: int
) -> bool:
    """
    Check for overdrafts in the past window.
    
    Overdrafts are typically:
    - Negative balance transactions
    - Overdraft fees
    - NSF (Non-Sufficient Funds) fees
    
    Args:
        transactions: List of transactions
        window_days: Analysis window in days
        
    Returns:
        True if overdrafts detected
    """
    window_start = date.today() - timedelta(days=window_days)
    
    # Check for overdraft-related keywords
    overdraft_keywords = [
        'overdraft', 'od fee', 'nsf', 'insufficient funds',
        'returned item', 'overdrawn', 'negative balance'
    ]
    
    for transaction in transactions:
        if transaction.date < window_start:
            continue
        
        merchant_name = (transaction.merchant_name or "").lower()
        # Overdraft fees are typically negative charges
        if transaction.amount < 0:
            if any(keyword in merchant_name for keyword in overdraft_keywords):
                return True
            
            # Check for small negative amounts that might be fees
            if abs(transaction.amount) < 50 and abs(transaction.amount) > 10:
                # Could be an overdraft fee
                pass
    
    return False


def check_low_balance_consistently(
    accounts: List,
    transactions: List,
    window_days: int,
    threshold: float = 500.0
) -> bool:
    """
    Check if checking balance is consistently < threshold.
    
    Args:
        accounts: List of account objects
        transactions: List of transactions
        window_days: Analysis window in days
        threshold: Balance threshold (default: $500)
        
    Returns:
        True if balance consistently below threshold
    """
    checking_accounts = [
        acc for acc in accounts
        if acc.type == AccountType.DEPOSITORY and acc.subtype == AccountSubtype.CHECKING
    ]
    
    if not checking_accounts:
        return False
    
    # Check current balances
    low_balance_count = sum(1 for acc in checking_accounts if acc.balances.current < threshold)
    
    # If most checking accounts are below threshold, consider it consistent
    if low_balance_count >= len(checking_accounts) * 0.7:  # 70% of accounts
        return True
    
    # Check historical balances by looking at transactions
    # If we see many small balances or frequent low balances, it's consistent
    window_start = date.today() - timedelta(days=window_days)
    window_transactions = [t for t in transactions if t.date >= window_start]
    
    # Estimate balance changes
    # For simplicity, check if there are many transactions that would result in low balances
    # This is a heuristic - in production, would track actual balance history
    
    return False  # Default to not consistent if we can't determine


def check_late_fees(
    transactions: List,
    window_days: int
) -> bool:
    """
    Check for late fees in transactions.
    
    Args:
        transactions: List of transactions
        window_days: Analysis window in days
        
    Returns:
        True if late fees detected
    """
    window_start = date.today() - timedelta(days=window_days)
    
    late_fee_keywords = [
        'late fee', 'late payment', 'past due', 'delinquent',
        'late charge', 'overdue fee'
    ]
    
    for transaction in transactions:
        if transaction.date < window_start:
            continue
        
        merchant_name = (transaction.merchant_name or "").lower()
        # Late fees are typically negative charges
        if transaction.amount < 0:
            if any(keyword in merchant_name for keyword in late_fee_keywords):
                return True
    
    return False


def check_financial_fragility_persona(
    customer_id: str,
    db_path: str,
    window_days: int = 30
) -> Optional[PersonaMatch]:
    """
    Check if customer matches Financial Fragility persona.
    
    Criteria:
    - Overdrafts in past 30d OR
    - Checking balance < $500 consistently OR
    - Late fees present
    
    Args:
        customer_id: Customer ID
        db_path: Path to SQLite database
        window_days: Analysis window (default: 30 days)
        
    Returns:
        PersonaMatch if criteria met, None otherwise
    """
    # Get accounts
    accounts = get_accounts_by_customer(customer_id, db_path)
    checking_accounts = [
        acc for acc in accounts
        if acc.type == AccountType.DEPOSITORY and acc.subtype == AccountSubtype.CHECKING
    ]
    
    if not checking_accounts:
        return None
    
    # Get all transactions from checking accounts
    all_transactions = []
    window_start = date.today() - timedelta(days=window_days)
    window_end = date.today()
    
    for account in checking_accounts:
        transactions = get_transactions_by_account(
            account.account_id, db_path,
            start_date=window_start,
            end_date=window_end
        )
        all_transactions.extend(transactions)
    
    criteria_met = []
    confidence = 0.0
    
    # Check overdrafts
    has_overdrafts = check_overdrafts(all_transactions, window_days)
    if has_overdrafts:
        criteria_met.append("Overdrafts in past 30 days")
        confidence = 0.9
    
    # Check low balance consistently
    has_low_balance = check_low_balance_consistently(
        checking_accounts, all_transactions, window_days, threshold=500.0
    )
    if has_low_balance:
        # Check current balances
        total_balance = sum(acc.balances.current for acc in checking_accounts)
        if total_balance < 500:
            criteria_met.append(f"Checking balance < $500 (${total_balance:.2f})")
            confidence = max(confidence, 0.8)
            if total_balance < 200:
                confidence = 0.9
    
    # Check late fees
    has_late_fees = check_late_fees(all_transactions, window_days)
    if has_late_fees:
        criteria_met.append("Late fees present")
        confidence = max(confidence, 0.85)
    
    # Need at least one criterion
    if not criteria_met:
        return None
    
    # Supporting data
    total_checking_balance = sum(acc.balances.current for acc in checking_accounts)
    
    supporting_data = {
        'has_overdrafts': has_overdrafts,
        'has_low_balance': has_low_balance,
        'has_late_fees': has_late_fees,
        'total_checking_balance': total_checking_balance,
        'checking_account_count': len(checking_accounts)
    }
    
    return PersonaMatch(
        persona_type=PersonaType.FINANCIAL_FRAGILITY,
        confidence_score=confidence,
        criteria_met=criteria_met,
        window_days=window_days,
        focus_areas=[
            "Immediate cash-flow management",
            "Fee avoidance",
            "Buffer building",
            "Overdraft protection"
        ],
        supporting_data=supporting_data
    )

