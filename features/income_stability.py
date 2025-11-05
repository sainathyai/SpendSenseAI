"""
Income Stability Analysis for SpendSenseAI.

Detects and assesses income patterns:
- Payroll ACH identification
- Payment frequency calculation
- Income variability measurement
- Cash-flow buffer calculation
- Median pay gap calculation
- Gig/freelance income detection
"""

from typing import List, Dict, Optional, Tuple
from datetime import date, timedelta
from dataclasses import dataclass
from statistics import median, stdev, mean

from ingest.queries import (
    get_accounts_by_customer,
    get_transactions_by_account
)
from ingest.schemas import Account, AccountType, AccountSubtype


@dataclass
class IncomePattern:
    """Income pattern for a single income source."""
    source_name: str  # e.g., "Payroll", "Gig Income"
    transaction_count: int
    first_date: date
    last_date: date
    total_income: float
    average_amount: float
    payment_frequency: str  # 'biweekly', 'monthly', 'irregular'
    frequency_days: Optional[float]  # Average days between payments
    is_regular: bool
    is_active: bool


@dataclass
class IncomeStabilityMetrics:
    """Income stability metrics for a customer."""
    total_income: float
    income_source_count: int
    primary_income_pattern: Optional[IncomePattern]
    payment_frequency: str  # 'biweekly', 'monthly', 'irregular'
    income_variability: float  # Coefficient of variation
    average_monthly_income: float
    median_pay_gap_days: float  # Days between paychecks
    cash_flow_buffer_months: float  # Balance / monthly burn rate
    is_gig_worker: bool  # Multiple irregular income sources
    income_sources: List[IncomePattern]


def is_payroll_deposit(transaction) -> bool:
    """
    Identify if transaction is a payroll deposit.
    
    Args:
        transaction: Transaction object
        
    Returns:
        True if appears to be payroll deposit
    """
    # Payroll deposits are typically:
    # - Positive amounts (deposits)
    # - Regular amounts (consistent paycheck)
    # - From employer or payroll service
    # - Payment channel: ACH or direct deposit
    
    if transaction.amount <= 0:
        return False
    
    merchant_name = (transaction.merchant_name or "").lower()
    merchant_id = (transaction.merchant_entity_id or "").lower()
    
    # Check for payroll-related keywords
    payroll_keywords = [
        'payroll', 'salary', 'wages', 'paycheck', 'direct deposit',
        'employer', 'company', 'corp', 'inc', 'llc'
    ]
    
    # Check merchant name or entity ID
    if any(keyword in merchant_name or keyword in merchant_id for keyword in payroll_keywords):
        return True
    
    # Check payment channel (ACH deposits are often payroll)
    if transaction.payment_channel.value in ['other', 'ach']:
        # Large regular deposits are likely payroll
        if transaction.amount >= 500:  # Minimum reasonable paycheck
            return True
    
    return False


def detect_payment_frequency(
    transactions: List,
    window_days: int
) -> Tuple[str, Optional[float], bool]:
    """
    Detect payment frequency from transaction dates.
    
    Args:
        transactions: List of income transactions
        window_days: Analysis window in days
        
    Returns:
        Tuple of (frequency_type, average_days, is_regular)
    """
    if len(transactions) < 2:
        return ('irregular', None, False)
    
    # Sort by date
    sorted_transactions = sorted(transactions, key=lambda t: t.date)
    dates = [t.date for t in sorted_transactions]
    
    # Calculate intervals
    intervals = [(dates[i] - dates[i-1]).days for i in range(1, len(dates))]
    
    if not intervals:
        return ('irregular', None, False)
    
    avg_interval = mean(intervals)
    
    # Check consistency (standard deviation)
    if len(intervals) > 1:
        interval_std = stdev(intervals)
        consistency = interval_std / avg_interval if avg_interval > 0 else 1.0
        is_regular = consistency < 0.3  # Less than 30% variation
    else:
        is_regular = False
    
    # Determine frequency type
    tolerance = 3  # Days tolerance
    
    if 13 - tolerance <= avg_interval <= 15 + tolerance:
        return ('biweekly', avg_interval, is_regular)
    elif 28 - tolerance <= avg_interval <= 31 + tolerance:
        return ('monthly', avg_interval, is_regular)
    else:
        return ('irregular', avg_interval, is_regular)


def calculate_income_variability(amounts: List[float]) -> float:
    """
    Calculate income variability (coefficient of variation).
    
    Args:
        amounts: List of income amounts
        
    Returns:
        Coefficient of variation (0-1, lower = more stable)
    """
    if len(amounts) < 2:
        return 0.0
    
    if mean(amounts) == 0:
        return 1.0
    
    return stdev(amounts) / mean(amounts)


def calculate_median_pay_gap(transactions: List) -> float:
    """
    Calculate median days between paychecks.
    
    Args:
        transactions: List of income transactions
        
    Returns:
        Median pay gap in days
    """
    if len(transactions) < 2:
        return 0.0
    
    # Sort by date
    sorted_transactions = sorted(transactions, key=lambda t: t.date)
    dates = [t.date for t in sorted_transactions]
    
    # Calculate intervals
    intervals = [(dates[i] - dates[i-1]).days for i in range(1, len(dates))]
    
    if not intervals:
        return 0.0
    
    return median(intervals)


def calculate_cash_flow_buffer(
    checking_balance: float,
    monthly_burn_rate: float
) -> float:
    """
    Calculate cash-flow buffer in months.
    
    Args:
        checking_balance: Current checking account balance
        monthly_burn_rate: Average monthly expenses
        
    Returns:
        Cash-flow buffer in months
    """
    if monthly_burn_rate <= 0:
        return 0.0
    
    return checking_balance / monthly_burn_rate


def detect_income_patterns(
    transactions: List,
    window_days: int,
    window_end_date: date
) -> List[IncomePattern]:
    """
    Detect income patterns from transactions.
    
    Args:
        transactions: List of all transactions
        window_days: Analysis window in days
        window_end_date: End date of window
        
    Returns:
        List of IncomePattern objects
    """
    # Filter to deposits (positive amounts)
    deposits = [t for t in transactions if t.amount > 0]
    
    if not deposits:
        return []
    
    # Separate payroll from other income
    payroll_deposits = [t for t in deposits if is_payroll_deposit(t)]
    other_deposits = [t for t in deposits if not is_payroll_deposit(t)]
    
    patterns = []
    
    # Analyze payroll income
    if payroll_deposits:
        amounts = [t.amount for t in payroll_deposits]
        dates = [t.date for t in payroll_deposits]
        
        frequency_type, avg_days, is_regular = detect_payment_frequency(
            payroll_deposits, window_days
        )
        
        # Check if active (recent deposit)
        window_start = window_end_date - timedelta(days=window_days)
        recent_deposits = [t for t in payroll_deposits if t.date >= window_start]
        is_active = len(recent_deposits) > 0
        
        pattern = IncomePattern(
            source_name="Payroll",
            transaction_count=len(payroll_deposits),
            first_date=min(dates),
            last_date=max(dates),
            total_income=sum(amounts),
            average_amount=mean(amounts),
            payment_frequency=frequency_type,
            frequency_days=avg_days,
            is_regular=is_regular,
            is_active=is_active
        )
        patterns.append(pattern)
    
    # Analyze other income (gig/freelance)
    if other_deposits:
        # Group by merchant to identify income sources
        merchant_groups = {}
        for transaction in other_deposits:
            merchant = transaction.merchant_name or transaction.merchant_entity_id or "Unknown"
            if merchant not in merchant_groups:
                merchant_groups[merchant] = []
            merchant_groups[merchant].append(transaction)
        
        # Create patterns for each merchant group
        for merchant, merchant_transactions in merchant_groups.items():
            if len(merchant_transactions) >= 2:  # At least 2 transactions to be a pattern
                amounts = [t.amount for t in merchant_transactions]
                dates = [t.date for t in merchant_transactions]
                
                frequency_type, avg_days, is_regular = detect_payment_frequency(
                    merchant_transactions, window_days
                )
                
                window_start = window_end_date - timedelta(days=window_days)
                recent_deposits = [t for t in merchant_transactions if t.date >= window_start]
                is_active = len(recent_deposits) > 0
                
                pattern = IncomePattern(
                    source_name=f"Gig Income: {merchant}",
                    transaction_count=len(merchant_transactions),
                    first_date=min(dates),
                    last_date=max(dates),
                    total_income=sum(amounts),
                    average_amount=mean(amounts),
                    payment_frequency=frequency_type,
                    frequency_days=avg_days,
                    is_regular=is_regular,
                    is_active=is_active
                )
                patterns.append(pattern)
    
    return patterns


def analyze_income_stability_for_customer(
    customer_id: str,
    db_path: str,
    window_days: int = 180,
    monthly_burn_rate: float = 0.0
) -> IncomeStabilityMetrics:
    """
    Analyze income stability for a customer.
    
    Args:
        customer_id: Customer ID
        db_path: Path to SQLite database
        window_days: Analysis window in days (default: 180)
        monthly_burn_rate: Average monthly expenses (for cash-flow buffer)
        
    Returns:
        IncomeStabilityMetrics object
    """
    # Get all accounts
    accounts = get_accounts_by_customer(customer_id, db_path)
    
    # Get checking accounts (where income is typically deposited)
    checking_accounts = [
        acc for acc in accounts
        if acc.type == AccountType.DEPOSITORY and acc.subtype == AccountSubtype.CHECKING
    ]
    
    if not checking_accounts:
        return IncomeStabilityMetrics(
            total_income=0.0,
            income_source_count=0,
            primary_income_pattern=None,
            payment_frequency='irregular',
            income_variability=1.0,
            average_monthly_income=0.0,
            median_pay_gap_days=0.0,
            cash_flow_buffer_months=0.0,
            is_gig_worker=False,
            income_sources=[]
        )
    
    # Get all transactions from checking accounts
    all_transactions = []
    window_end_date = date.today()
    window_start_date = window_end_date - timedelta(days=window_days)
    
    for account in checking_accounts:
        transactions = get_transactions_by_account(
            account.account_id, db_path,
            start_date=window_start_date,
            end_date=window_end_date
        )
        all_transactions.extend(transactions)
    
    # Detect income patterns
    income_patterns = detect_income_patterns(
        all_transactions, window_days, window_end_date
    )
    
    if not income_patterns:
        # Get checking balance for cash-flow buffer
        total_checking_balance = sum(acc.balances.current for acc in checking_accounts)
        
        return IncomeStabilityMetrics(
            total_income=0.0,
            income_source_count=0,
            primary_income_pattern=None,
            payment_frequency='irregular',
            income_variability=1.0,
            average_monthly_income=0.0,
            median_pay_gap_days=0.0,
            cash_flow_buffer_months=calculate_cash_flow_buffer(total_checking_balance, monthly_burn_rate),
            is_gig_worker=False,
            income_sources=[]
        )
    
    # Find primary income pattern (highest total income)
    primary_pattern = max(income_patterns, key=lambda p: p.total_income)
    
    # Calculate aggregate metrics
    total_income = sum(p.total_income for p in income_patterns)
    
    # Calculate income variability from primary pattern
    payroll_patterns = [p for p in income_patterns if p.source_name == "Payroll"]
    if payroll_patterns:
        # Get all payroll amounts to calculate variability
        all_transactions = []
        for account in checking_accounts:
            transactions = get_transactions_by_account(
                account.account_id, db_path,
                start_date=window_start_date,
                end_date=window_end_date
            )
            all_transactions.extend(transactions)
        
        payroll_deposits = [t for t in all_transactions if is_payroll_deposit(t)]
        payroll_amounts = [t.amount for t in payroll_deposits]
        income_variability = calculate_income_variability(payroll_amounts)
        median_pay_gap = calculate_median_pay_gap(payroll_deposits)
    else:
        income_variability = 1.0  # High variability if no regular payroll
        median_pay_gap = 0.0
    
    # Calculate average monthly income
    months = window_days / 30.0
    average_monthly_income = total_income / months if months > 0 else 0.0
    
    # Check if gig worker (multiple irregular income sources)
    gig_patterns = [p for p in income_patterns if "Gig Income" in p.source_name]
    is_gig_worker = len(gig_patterns) >= 2 or (
        len(income_patterns) > 1 and not any(p.source_name == "Payroll" for p in income_patterns)
    )
    
    # Calculate cash-flow buffer
    total_checking_balance = sum(acc.balances.current for acc in checking_accounts)
    cash_flow_buffer = calculate_cash_flow_buffer(total_checking_balance, monthly_burn_rate)
    
    return IncomeStabilityMetrics(
        total_income=total_income,
        income_source_count=len(income_patterns),
        primary_income_pattern=primary_pattern,
        payment_frequency=primary_pattern.payment_frequency,
        income_variability=income_variability,
        average_monthly_income=average_monthly_income,
        median_pay_gap_days=median_pay_gap,
        cash_flow_buffer_months=cash_flow_buffer,
        is_gig_worker=is_gig_worker,
        income_sources=income_patterns
    )

