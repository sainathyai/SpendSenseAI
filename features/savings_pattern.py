"""
Savings Pattern Detection for SpendSenseAI.

Analyzes savings behaviors:
- Savings account identification
- Net inflow calculation (deposits - withdrawals)
- Growth rate computation
- Emergency fund coverage
- Automated transfer detection
"""

from typing import List, Dict, Optional, Tuple
from datetime import date, timedelta
from dataclasses import dataclass

from ingest.queries import (
    get_accounts_by_customer,
    get_transactions_by_account
)
from ingest.schemas import Account, AccountType, AccountSubtype


@dataclass
class SavingsAccountMetrics:
    """Savings metrics for a single account."""
    account_id: str
    account_subtype: str
    current_balance: float
    starting_balance: float  # Balance at start of window
    ending_balance: float  # Balance at end of window
    net_inflow: float  # Deposits - withdrawals
    deposit_count: int
    withdrawal_count: int
    total_deposits: float
    total_withdrawals: float
    growth_rate: float  # Percentage growth
    growth_amount: float  # Absolute growth
    automated_transfer_count: int


@dataclass
class AggregateSavingsMetrics:
    """Aggregate savings metrics across all savings accounts."""
    total_savings_balance: float
    total_net_inflow: float
    total_growth_amount: float
    overall_growth_rate: float
    savings_account_count: int
    emergency_fund_coverage_months: float  # Savings / avg monthly expenses
    average_monthly_inflow: float


def is_savings_account(account: Account) -> bool:
    """
    Identify if account is a savings account.
    
    Args:
        account: Account object
        
    Returns:
        True if account is a savings account type
    """
    savings_subtypes = [
        AccountSubtype.SAVINGS,
        AccountSubtype.MONEY_MARKET,
        AccountSubtype.HSA,
        AccountSubtype.CASH_MANAGEMENT
    ]
    
    return (
        account.type == AccountType.DEPOSITORY and
        account.subtype in savings_subtypes
    )


def calculate_net_inflow(
    transactions: List,
    start_date: date,
    end_date: date
) -> Tuple[float, int, int, float, float]:
    """
    Calculate net inflow (deposits - withdrawals).
    
    Args:
        transactions: List of transactions
        start_date: Start date of window
        end_date: End date of window
        
    Returns:
        Tuple of (net_inflow, deposit_count, withdrawal_count, total_deposits, total_withdrawals)
    """
    # Filter to window
    window_transactions = [
        t for t in transactions
        if start_date <= t.date <= end_date
    ]
    
    deposits = 0.0
    withdrawals = 0.0
    deposit_count = 0
    withdrawal_count = 0
    
    for transaction in window_transactions:
        amount = transaction.amount
        
        # Positive amounts = deposits (credits to account)
        # Negative amounts = withdrawals (debits from account)
        if amount > 0:
            deposits += amount
            deposit_count += 1
        elif amount < 0:
            withdrawals += abs(amount)
            withdrawal_count += 1
    
    net_inflow = deposits - withdrawals
    
    return net_inflow, deposit_count, withdrawal_count, deposits, withdrawals


def detect_automated_transfers(
    transactions: List,
    start_date: date,
    end_date: date
) -> int:
    """
    Detect automated transfers (regular, consistent amounts).
    
    Args:
        transactions: List of transactions
        start_date: Start date of window
        end_date: End date of window
        
    Returns:
        Number of automated transfers detected
    """
    # Filter to deposits in window
    window_transactions = [
        t for t in transactions
        if start_date <= t.date <= end_date and t.amount > 0
    ]
    
    if len(window_transactions) < 2:
        return 0
    
    # Group by amount
    amount_groups = {}
    for transaction in window_transactions:
        # Round to nearest dollar for grouping
        rounded_amount = round(transaction.amount)
        if rounded_amount not in amount_groups:
            amount_groups[rounded_amount] = []
        amount_groups[rounded_amount].append(transaction)
    
    # Find amounts that appear regularly (potential automated transfers)
    automated_count = 0
    for amount, transactions in amount_groups.items():
        if len(transactions) >= 2:
            # Check if transactions are regular (monthly, biweekly)
            dates = sorted([t.date for t in transactions])
            intervals = [(dates[i] - dates[i-1]).days for i in range(1, len(dates))]
            
            # Check if intervals are consistent (within 5 days of average)
            if intervals:
                avg_interval = sum(intervals) / len(intervals)
                consistent = all(
                    abs(interval - avg_interval) <= 5
                    for interval in intervals
                )
                
                # Monthly or biweekly cadence
                if consistent and (avg_interval >= 25 and avg_interval <= 35 or
                                   avg_interval >= 12 and avg_interval <= 16):
                    automated_count += len(transactions)
    
    return automated_count


def calculate_growth_rate(
    starting_balance: float,
    ending_balance: float,
    window_days: int
) -> Tuple[float, float]:
    """
    Calculate growth rate and amount.
    
    Args:
        starting_balance: Balance at start of window
        ending_balance: Balance at end of window
        window_days: Number of days in window
        
    Returns:
        Tuple of (growth_rate_percentage, growth_amount)
    """
    growth_amount = ending_balance - starting_balance
    
    if starting_balance <= 0:
        growth_rate = 0.0 if ending_balance <= 0 else 100.0
    else:
        growth_rate = (growth_amount / starting_balance) * 100.0
    
    return growth_rate, growth_amount


def analyze_savings_account(
    account: Account,
    transactions: List,
    start_date: date,
    end_date: date
) -> SavingsAccountMetrics:
    """
    Analyze savings account metrics.
    
    Args:
        account: Account object
        transactions: List of transactions for this account
        start_date: Start date of analysis window
        end_date: End date of analysis window
        
    Returns:
        SavingsAccountMetrics object
    """
    current_balance = account.balances.current
    
    # Get starting balance (approximate from current balance and transactions)
    # For simplicity, we'll use current balance as ending balance
    # and calculate starting balance by reversing transactions
    ending_balance = current_balance
    
    # Calculate net inflow
    net_inflow, deposit_count, withdrawal_count, total_deposits, total_withdrawals = calculate_net_inflow(
        transactions, start_date, end_date
    )
    
    # Estimate starting balance
    starting_balance = ending_balance - net_inflow
    
    # Calculate growth
    window_days = (end_date - start_date).days
    growth_rate, growth_amount = calculate_growth_rate(
        starting_balance, ending_balance, window_days
    )
    
    # Detect automated transfers
    automated_transfer_count = detect_automated_transfers(
        transactions, start_date, end_date
    )
    
    return SavingsAccountMetrics(
        account_id=account.account_id,
        account_subtype=account.subtype.value,
        current_balance=current_balance,
        starting_balance=starting_balance,
        ending_balance=ending_balance,
        net_inflow=net_inflow,
        deposit_count=deposit_count,
        withdrawal_count=withdrawal_count,
        total_deposits=total_deposits,
        total_withdrawals=total_withdrawals,
        growth_rate=growth_rate,
        growth_amount=growth_amount,
        automated_transfer_count=automated_transfer_count
    )


def calculate_emergency_fund_coverage(
    total_savings: float,
    avg_monthly_expenses: float
) -> float:
    """
    Calculate emergency fund coverage in months.
    
    Args:
        total_savings: Total savings balance
        avg_monthly_expenses: Average monthly expenses
        
    Returns:
        Emergency fund coverage in months
    """
    if avg_monthly_expenses <= 0:
        return 0.0
    
    return total_savings / avg_monthly_expenses


def aggregate_savings_metrics(
    account_metrics: List[SavingsAccountMetrics],
    window_days: int,
    avg_monthly_expenses: float = 0.0
) -> AggregateSavingsMetrics:
    """
    Aggregate savings metrics across all accounts.
    
    Args:
        account_metrics: List of SavingsAccountMetrics
        window_days: Analysis window in days
        avg_monthly_expenses: Average monthly expenses (for emergency fund calculation)
        
    Returns:
        AggregateSavingsMetrics object
    """
    if not account_metrics:
        return AggregateSavingsMetrics(
            total_savings_balance=0.0,
            total_net_inflow=0.0,
            total_growth_amount=0.0,
            overall_growth_rate=0.0,
            savings_account_count=0,
            emergency_fund_coverage_months=0.0,
            average_monthly_inflow=0.0
        )
    
    total_balance = sum(m.current_balance for m in account_metrics)
    total_net_inflow = sum(m.net_inflow for m in account_metrics)
    total_growth = sum(m.growth_amount for m in account_metrics)
    
    # Calculate overall growth rate
    total_starting = sum(m.starting_balance for m in account_metrics)
    if total_starting > 0:
        overall_growth_rate = (total_growth / total_starting) * 100.0
    else:
        overall_growth_rate = 0.0
    
    # Calculate average monthly inflow
    months = window_days / 30.0
    average_monthly_inflow = total_net_inflow / months if months > 0 else 0.0
    
    # Calculate emergency fund coverage
    emergency_fund_coverage = calculate_emergency_fund_coverage(
        total_balance, avg_monthly_expenses
    )
    
    return AggregateSavingsMetrics(
        total_savings_balance=total_balance,
        total_net_inflow=total_net_inflow,
        total_growth_amount=total_growth,
        overall_growth_rate=overall_growth_rate,
        savings_account_count=len(account_metrics),
        emergency_fund_coverage_months=emergency_fund_coverage,
        average_monthly_inflow=average_monthly_inflow
    )


def analyze_savings_patterns_for_customer(
    customer_id: str,
    db_path: str,
    window_days: int = 180,
    avg_monthly_expenses: float = 0.0
) -> Tuple[List[SavingsAccountMetrics], AggregateSavingsMetrics]:
    """
    Analyze savings patterns for a customer.
    
    Args:
        customer_id: Customer ID
        db_path: Path to SQLite database
        window_days: Analysis window in days (default: 180)
        avg_monthly_expenses: Average monthly expenses (for emergency fund calculation)
        
    Returns:
        Tuple of (account_metrics list, aggregate_metrics)
    """
    # Get all accounts
    accounts = get_accounts_by_customer(customer_id, db_path)
    
    # Filter to savings accounts
    savings_accounts = [acc for acc in accounts if is_savings_account(acc)]
    
    if not savings_accounts:
        return [], AggregateSavingsMetrics(
            total_savings_balance=0.0,
            total_net_inflow=0.0,
            total_growth_amount=0.0,
            overall_growth_rate=0.0,
            savings_account_count=0,
            emergency_fund_coverage_months=0.0,
            average_monthly_inflow=0.0
        )
    
    # Determine window dates
    end_date = date.today()
    start_date = end_date - timedelta(days=window_days)
    
    # Analyze each savings account
    account_metrics = []
    
    for account in savings_accounts:
        # Get transactions
        transactions = get_transactions_by_account(
            account.account_id, db_path,
            start_date=start_date,
            end_date=end_date
        )
        
        # Analyze
        metrics = analyze_savings_account(
            account, transactions, start_date, end_date
        )
        
        account_metrics.append(metrics)
    
    # Aggregate
    aggregate_metrics = aggregate_savings_metrics(
        account_metrics, window_days, avg_monthly_expenses
    )
    
    return account_metrics, aggregate_metrics

