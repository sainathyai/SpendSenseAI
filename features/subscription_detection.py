"""
Subscription Detection Engine for SpendSenseAI.

Detects recurring subscription patterns from transaction data:
- Groups transactions by merchant
- Detects cadence (monthly, weekly, biweekly)
- Calculates monthly recurring spend
- Identifies subscription share of total spend
"""

from typing import List, Dict, Optional, Tuple
from datetime import date, timedelta
from collections import defaultdict
from dataclasses import dataclass

from ingest.queries import get_transactions_by_customer
from ingest.schemas import Transaction


@dataclass
class SubscriptionPattern:
    """Represents a detected subscription pattern."""
    merchant_name: str
    merchant_entity_id: Optional[str]
    cadence: str  # 'monthly', 'weekly', 'biweekly', 'annual', 'irregular'
    transaction_count: int
    first_transaction_date: date
    last_transaction_date: date
    total_spend: float
    monthly_recurring_spend: float  # Normalized to monthly
    average_amount: float
    date_intervals: List[int]  # Days between transactions
    confidence_score: float  # 0.0 to 1.0
    is_active: bool  # True if last transaction within cadence window


def group_transactions_by_merchant(transactions: List[Transaction]) -> Dict[str, List[Transaction]]:
    """
    Group transactions by merchant.
    
    Args:
        transactions: List of Transaction objects
        
    Returns:
        Dictionary mapping merchant_name to list of transactions
    """
    merchant_groups = defaultdict(list)
    
    for transaction in transactions:
        # Use merchant_name as primary key, fallback to merchant_entity_id
        key = transaction.merchant_name or transaction.merchant_entity_id or "Unknown"
        merchant_groups[key].append(transaction)
    
    return dict(merchant_groups)


def calculate_date_intervals(transactions: List[Transaction]) -> List[int]:
    """
    Calculate days between consecutive transactions.
    
    Args:
        transactions: List of Transaction objects, sorted by date
        
    Returns:
        List of days between consecutive transactions
    """
    if len(transactions) < 2:
        return []
    
    # Sort by date
    sorted_transactions = sorted(transactions, key=lambda t: t.date)
    
    intervals = []
    for i in range(1, len(sorted_transactions)):
        days_between = (sorted_transactions[i].date - sorted_transactions[i-1].date).days
        intervals.append(days_between)
    
    return intervals


def detect_cadence(intervals: List[int], transaction_count: int) -> Tuple[str, float]:
    """
    Detect subscription cadence from date intervals.
    
    Args:
        intervals: List of days between consecutive transactions
        transaction_count: Total number of transactions
        
    Returns:
        Tuple of (cadence_type, confidence_score)
    """
    if transaction_count < 3:
        return ('irregular', 0.0)
    
    if not intervals:
        return ('irregular', 0.0)
    
    # Calculate average interval
    avg_interval = sum(intervals) / len(intervals)
    
    # Tolerance for cadence detection (days)
    tolerance = 5  # Allow ±5 days variance
    
    # Monthly (28-35 days)
    if 28 - tolerance <= avg_interval <= 35 + tolerance:
        # Check consistency
        consistent = sum(1 for i in intervals if 28 - tolerance <= i <= 35 + tolerance) / len(intervals)
        return ('monthly', consistent)
    
    # Biweekly (13-15 days)
    elif 13 - tolerance <= avg_interval <= 15 + tolerance:
        consistent = sum(1 for i in intervals if 13 - tolerance <= i <= 15 + tolerance) / len(intervals)
        return ('biweekly', consistent)
    
    # Weekly (6-8 days)
    elif 6 - tolerance <= avg_interval <= 8 + tolerance:
        consistent = sum(1 for i in intervals if 6 - tolerance <= i <= 8 + tolerance) / len(intervals)
        return ('weekly', consistent)
    
    # Annual (330-395 days)
    elif 330 - tolerance <= avg_interval <= 395 + tolerance:
        consistent = sum(1 for i in intervals if 330 - tolerance <= i <= 395 + tolerance) / len(intervals)
        return ('annual', consistent)
    
    # Irregular
    else:
        return ('irregular', 0.3)  # Low confidence for irregular


def calculate_monthly_recurring_spend(
    cadence: str,
    average_amount: float,
    transaction_count: int
) -> float:
    """
    Calculate monthly recurring spend based on cadence.
    
    Args:
        cadence: Subscription cadence ('monthly', 'weekly', 'biweekly', 'annual', 'irregular')
        average_amount: Average transaction amount
        transaction_count: Number of transactions
        
    Returns:
        Monthly recurring spend (normalized to per month)
    """
    if cadence == 'monthly':
        return average_amount
    elif cadence == 'biweekly':
        # Biweekly = 2 per month
        return average_amount * 2
    elif cadence == 'weekly':
        # Weekly = ~4.33 per month
        return average_amount * 4.33
    elif cadence == 'annual':
        # Annual = 1/12 per month
        return average_amount / 12
    else:
        # Irregular: estimate based on transaction frequency
        # If we have enough transactions, estimate monthly
        if transaction_count >= 3:
            # Rough estimate: assume monthly if we have 3+ transactions
            return average_amount
        return 0.0


def is_active_subscription(
    last_transaction_date: date,
    cadence: str,
    window_end_date: date
) -> bool:
    """
    Check if subscription is still active based on last transaction.
    
    Args:
        last_transaction_date: Date of last transaction
        cadence: Subscription cadence
        window_end_date: End date of analysis window
        
    Returns:
        True if subscription appears active
    """
    days_since_last = (window_end_date - last_transaction_date).days
    
    # Active if last transaction within 2 cadence periods
    if cadence == 'monthly':
        return days_since_last <= 60  # 2 months
    elif cadence == 'biweekly':
        return days_since_last <= 30  # 2 biweeks
    elif cadence == 'weekly':
        return days_since_last <= 14  # 2 weeks
    elif cadence == 'annual':
        return days_since_last <= 365  # 1 year
    else:
        # Irregular: consider active if within 90 days
        return days_since_last <= 90


def detect_subscriptions(
    transactions: List[Transaction],
    min_occurrences: int = 3,
    window_days: int = 90
) -> List[SubscriptionPattern]:
    """
    Detect subscription patterns from transactions.
    
    Args:
        transactions: List of Transaction objects
        min_occurrences: Minimum number of transactions to consider (default: 3)
        window_days: Analysis window in days (default: 90)
        
    Returns:
        List of SubscriptionPattern objects
    """
    if not transactions:
        return []
    
    # Filter to positive amounts (subscriptions are typically charges, not credits)
    charge_transactions = [t for t in transactions if t.amount < 0]
    
    if not charge_transactions:
        return []
    
    # Group by merchant
    merchant_groups = group_transactions_by_merchant(charge_transactions)
    
    subscriptions = []
    
    # Determine window end date (use latest transaction date)
    window_end_date = max(t.date for t in charge_transactions)
    window_start_date = window_end_date - timedelta(days=window_days)
    
    for merchant_name, merchant_transactions in merchant_groups.items():
        # Filter to window
        window_transactions = [
            t for t in merchant_transactions
            if window_start_date <= t.date <= window_end_date
        ]
        
        if len(window_transactions) < min_occurrences:
            continue
        
        # Calculate intervals
        intervals = calculate_date_intervals(window_transactions)
        
        if not intervals:
            continue
        
        # Detect cadence
        cadence, confidence = detect_cadence(intervals, len(window_transactions))
        
        # Skip if confidence too low
        if confidence < 0.3:
            continue
        
        # Calculate amounts
        amounts = [abs(t.amount) for t in window_transactions]
        total_spend = sum(amounts)
        average_amount = total_spend / len(window_transactions)
        
        # Calculate monthly recurring spend
        monthly_recurring_spend = calculate_monthly_recurring_spend(
            cadence, average_amount, len(window_transactions)
        )
        
        # Get dates
        sorted_transactions = sorted(window_transactions, key=lambda t: t.date)
        first_transaction_date = sorted_transactions[0].date
        last_transaction_date = sorted_transactions[-1].date
        
        # Check if active
        is_active = is_active_subscription(last_transaction_date, cadence, window_end_date)
        
        # Get merchant entity ID
        merchant_entity_id = window_transactions[0].merchant_entity_id
        
        pattern = SubscriptionPattern(
            merchant_name=merchant_name,
            merchant_entity_id=merchant_entity_id,
            cadence=cadence,
            transaction_count=len(window_transactions),
            first_transaction_date=first_transaction_date,
            last_transaction_date=last_transaction_date,
            total_spend=total_spend,
            monthly_recurring_spend=monthly_recurring_spend,
            average_amount=average_amount,
            date_intervals=intervals,
            confidence_score=confidence,
            is_active=is_active
        )
        
        subscriptions.append(pattern)
    
    # Sort by monthly recurring spend (descending)
    subscriptions.sort(key=lambda s: s.monthly_recurring_spend, reverse=True)
    
    return subscriptions


def calculate_subscription_metrics(
    subscriptions: List[SubscriptionPattern],
    total_spend: float
) -> Dict[str, float]:
    """
    Calculate subscription-related metrics.
    
    Args:
        subscriptions: List of detected subscriptions
        total_spend: Total spending in the period
        
    Returns:
        Dictionary with subscription metrics
    """
    total_monthly_recurring = sum(s.monthly_recurring_spend for s in subscriptions)
    active_subscriptions = [s for s in subscriptions if s.is_active]
    active_monthly_recurring = sum(s.monthly_recurring_spend for s in active_subscriptions)
    
    subscription_count = len(subscriptions)
    active_count = len(active_subscriptions)
    
    subscription_share = (total_monthly_recurring / total_spend * 100) if total_spend > 0 else 0.0
    
    return {
        'subscription_count': subscription_count,
        'active_subscription_count': active_count,
        'total_monthly_recurring_spend': total_monthly_recurring,
        'active_monthly_recurring_spend': active_monthly_recurring,
        'subscription_share_of_total': subscription_share,
        'average_subscription_amount': total_monthly_recurring / subscription_count if subscription_count > 0 else 0.0
    }


def detect_subscriptions_for_customer(
    customer_id: str,
    db_path: str,
    window_days: int = 90,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> Tuple[List[SubscriptionPattern], Dict[str, float]]:
    """
    Detect subscriptions for a customer with date range filtering.
    
    Args:
        customer_id: Customer ID
        db_path: Path to SQLite database
        window_days: Analysis window in days (default: 90)
        start_date: Optional start date for filtering
        end_date: Optional end date for filtering
        
    Returns:
        Tuple of (subscriptions list, metrics dictionary)
    """
    # Get transactions
    transactions = get_transactions_by_customer(
        customer_id,
        db_path,
        start_date=start_date,
        end_date=end_date,
        exclude_pending=True
    )
    
    if not transactions:
        return [], {
            'subscription_count': 0,
            'active_subscription_count': 0,
            'total_monthly_recurring_spend': 0.0,
            'active_monthly_recurring_spend': 0.0,
            'subscription_share_of_total': 0.0,
            'average_subscription_amount': 0.0
        }
    
    # Detect subscriptions
    subscriptions = detect_subscriptions(transactions, min_occurrences=3, window_days=window_days)
    
    # Calculate total spend
    total_spend = sum(abs(t.amount) for t in transactions if t.amount < 0)
    
    # Calculate metrics
    metrics = calculate_subscription_metrics(subscriptions, total_spend)
    
    return subscriptions, metrics

