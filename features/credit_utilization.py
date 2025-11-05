"""
Credit Utilization Analysis for SpendSenseAI.

Calculates credit usage metrics:
- Per-card utilization (balance / limit)
- Threshold flagging (30%, 50%, 80%)
- Minimum-payment-only detection
- Interest charge identification
- Overdue status tracking
- Multi-card aggregation
"""

from typing import List, Dict, Optional, Tuple
from datetime import date, timedelta
from dataclasses import dataclass

from ingest.queries import (
    get_accounts_by_customer,
    get_credit_card_liabilities_by_customer,
    get_transactions_by_account
)
from ingest.schemas import Account, AccountType, CreditCardLiability


@dataclass
class CreditUtilizationMetrics:
    """Credit utilization metrics for a single card."""
    account_id: str
    customer_id: str
    balance: float
    limit: float
    utilization_percentage: float
    utilization_tier: str  # 'low', 'moderate', 'high', 'critical'
    is_minimum_payment_only: bool
    has_interest_charges: bool
    is_overdue: bool
    minimum_payment_amount: float
    apr_percentage: float
    estimated_monthly_interest: float


@dataclass
class AggregateCreditMetrics:
    """Aggregate credit metrics across all cards."""
    total_balance: float
    total_limit: float
    aggregate_utilization: float
    card_count: int
    high_utilization_card_count: int
    critical_utilization_card_count: int
    overdue_card_count: int
    total_monthly_interest: float
    total_minimum_payments: float


def calculate_utilization_percentage(balance: float, limit: float) -> float:
    """
    Calculate credit utilization percentage.
    
    Args:
        balance: Current balance
        limit: Credit limit
        
    Returns:
        Utilization percentage (0-100)
    """
    if limit <= 0:
        return 0.0
    
    return (balance / limit) * 100.0


def get_utilization_tier(utilization: float) -> str:
    """
    Get utilization tier based on percentage.
    
    Args:
        utilization: Utilization percentage (0-100)
        
    Returns:
        Tier: 'low', 'moderate', 'high', 'critical'
    """
    if utilization < 30:
        return 'low'
    elif utilization < 50:
        return 'moderate'
    elif utilization < 80:
        return 'high'
    else:
        return 'critical'


def detect_minimum_payment_only(
    transactions: List,
    minimum_payment: float,
    window_days: int = 30
) -> bool:
    """
    Detect if user is only making minimum payments.
    
    Args:
        transactions: List of transactions (payments are negative amounts)
        minimum_payment: Minimum payment amount
        window_days: Analysis window in days
        
    Returns:
        True if appears to be minimum-payment-only
    """
    if not transactions:
        return False
    
    # Get recent transactions (payments)
    recent_date = date.today() - timedelta(days=window_days)
    recent_transactions = [
        t for t in transactions
        if t.date >= recent_date and t.amount > 0  # Positive = payments to credit card
    ]
    
    if len(recent_transactions) < 2:
        return False
    
    # Check if payments are close to minimum
    tolerance = 5.0  # $5 tolerance
    for transaction in recent_transactions:
        payment_amount = transaction.amount
        if payment_amount < minimum_payment - tolerance:
            return False
        if payment_amount > minimum_payment + tolerance:
            return False
    
    return True


def detect_interest_charges(
    transactions: List,
    window_days: int = 30
) -> bool:
    """
    Detect interest charges on credit card.
    
    Args:
        transactions: List of transactions
        window_days: Analysis window in days
        
    Returns:
        True if interest charges detected
    """
    if not transactions:
        return False
    
    # Look for transactions that might be interest charges
    # Interest charges are typically:
    # - Small amounts (often < $100)
    # - Regular (monthly)
    # - From the credit card issuer
    # - Negative amounts (charges)
    
    recent_date = date.today() - timedelta(days=window_days)
    recent_transactions = [
        t for t in transactions
        if t.date >= recent_date and t.amount < 0
    ]
    
    # Check for merchant names that suggest interest
    interest_keywords = ['interest', 'finance charge', 'apr', 'fee']
    
    for transaction in recent_transactions:
        merchant_name = (transaction.merchant_name or "").lower()
        if any(keyword in merchant_name for keyword in interest_keywords):
            return True
        
        # Check for small regular charges (potential interest)
        if abs(transaction.amount) < 100 and transaction.amount < 0:
            # Could be interest, but not definitive
            pass
    
    return False


def calculate_monthly_interest(balance: float, apr: float) -> float:
    """
    Calculate estimated monthly interest.
    
    Args:
        balance: Current balance
        apr: APR percentage (e.g., 18.99)
        
    Returns:
        Estimated monthly interest in dollars
    """
    if balance <= 0:
        return 0.0
    
    # Monthly interest = balance * (APR / 100) / 12
    monthly_rate = (apr / 100.0) / 12.0
    return balance * monthly_rate


def analyze_credit_card_utilization(
    account: Account,
    liability: Optional[CreditCardLiability],
    transactions: List,
    window_days: int = 30
) -> CreditUtilizationMetrics:
    """
    Analyze credit utilization for a single card.
    
    Args:
        account: Account object
        liability: CreditCardLiability object (optional)
        transactions: List of transactions for this account
        window_days: Analysis window in days
        
    Returns:
        CreditUtilizationMetrics object
    """
    balance = account.balances.current
    limit = account.balances.limit or 0.0
    
    utilization = calculate_utilization_percentage(balance, limit)
    tier = get_utilization_tier(utilization)
    
    # Get liability info
    minimum_payment = 0.0
    apr = 0.0
    is_overdue = False
    
    if liability:
        minimum_payment = liability.minimum_payment_amount
        is_overdue = liability.is_overdue
        if liability.aprs:
            apr = liability.aprs[0].percentage
    
    # Detect minimum payment only
    is_minimum_payment_only = detect_minimum_payment_only(
        transactions, minimum_payment, window_days
    ) if minimum_payment > 0 else False
    
    # Detect interest charges
    has_interest_charges = detect_interest_charges(transactions, window_days)
    
    # Calculate estimated monthly interest
    estimated_interest = calculate_monthly_interest(balance, apr)
    
    return CreditUtilizationMetrics(
        account_id=account.account_id,
        customer_id=account.customer_id,
        balance=balance,
        limit=limit,
        utilization_percentage=utilization,
        utilization_tier=tier,
        is_minimum_payment_only=is_minimum_payment_only,
        has_interest_charges=has_interest_charges,
        is_overdue=is_overdue,
        minimum_payment_amount=minimum_payment,
        apr_percentage=apr,
        estimated_monthly_interest=estimated_interest
    )


def aggregate_credit_metrics(
    card_metrics: List[CreditUtilizationMetrics]
) -> AggregateCreditMetrics:
    """
    Aggregate credit metrics across all cards.
    
    Args:
        card_metrics: List of CreditUtilizationMetrics objects
        
    Returns:
        AggregateCreditMetrics object
    """
    if not card_metrics:
        return AggregateCreditMetrics(
            total_balance=0.0,
            total_limit=0.0,
            aggregate_utilization=0.0,
            card_count=0,
            high_utilization_card_count=0,
            critical_utilization_card_count=0,
            overdue_card_count=0,
            total_monthly_interest=0.0,
            total_minimum_payments=0.0
        )
    
    total_balance = sum(m.balance for m in card_metrics)
    total_limit = sum(m.limit for m in card_metrics)
    aggregate_utilization = calculate_utilization_percentage(total_balance, total_limit)
    
    high_utilization_count = sum(1 for m in card_metrics if m.utilization_tier in ['high', 'critical'])
    critical_utilization_count = sum(1 for m in card_metrics if m.utilization_tier == 'critical')
    overdue_count = sum(1 for m in card_metrics if m.is_overdue)
    
    total_monthly_interest = sum(m.estimated_monthly_interest for m in card_metrics)
    total_minimum_payments = sum(m.minimum_payment_amount for m in card_metrics)
    
    return AggregateCreditMetrics(
        total_balance=total_balance,
        total_limit=total_limit,
        aggregate_utilization=aggregate_utilization,
        card_count=len(card_metrics),
        high_utilization_card_count=high_utilization_count,
        critical_utilization_card_count=critical_utilization_count,
        overdue_card_count=overdue_count,
        total_monthly_interest=total_monthly_interest,
        total_minimum_payments=total_minimum_payments
    )


def analyze_credit_utilization_for_customer(
    customer_id: str,
    db_path: str,
    window_days: int = 30
) -> Tuple[List[CreditUtilizationMetrics], AggregateCreditMetrics]:
    """
    Analyze credit utilization for a customer.
    
    Args:
        customer_id: Customer ID
        db_path: Path to SQLite database
        window_days: Analysis window in days
        
    Returns:
        Tuple of (card_metrics list, aggregate_metrics)
    """
    # Get all accounts
    accounts = get_accounts_by_customer(customer_id, db_path)
    
    # Filter to credit cards only
    credit_accounts = [acc for acc in accounts if acc.type == AccountType.CREDIT]
    
    if not credit_accounts:
        return [], AggregateCreditMetrics(
            total_balance=0.0,
            total_limit=0.0,
            aggregate_utilization=0.0,
            card_count=0,
            high_utilization_card_count=0,
            critical_utilization_card_count=0,
            overdue_card_count=0,
            total_monthly_interest=0.0,
            total_minimum_payments=0.0
        )
    
    # Get liabilities
    liabilities = get_credit_card_liabilities_by_customer(customer_id, db_path)
    liability_map = {liab.account_id: liab for liab in liabilities}
    
    # Analyze each card
    card_metrics = []
    
    for account in credit_accounts:
        # Get transactions
        transactions = get_transactions_by_account(account.account_id, db_path)
        
        # Get liability
        liability = liability_map.get(account.account_id)
        
        # Analyze
        metrics = analyze_credit_card_utilization(
            account, liability, transactions, window_days
        )
        
        card_metrics.append(metrics)
    
    # Aggregate
    aggregate_metrics = aggregate_credit_metrics(card_metrics)
    
    return card_metrics, aggregate_metrics

