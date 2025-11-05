"""
Data synthesis module for SpendSenseAI.

This module transforms Capital One CSV data into Plaid-compatible format
with precision and accuracy. It synthesizes accounts, enhances transactions,
and generates liability data.
"""

import pandas as pd
from datetime import date, timedelta
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
import hashlib

from .schemas import (
    Account, AccountType, AccountSubtype, AccountBalances, HolderCategory,
    Transaction, PaymentChannel, PersonalFinanceCategory,
    PersonalFinanceCategoryPrimary, PersonalFinanceCategoryDetailed,
    CreditCardLiability, CreditCardAPR
)


# ============================================================================
# Category Mapping (Capital One → Plaid)
# ============================================================================

CATEGORY_MAP = {
    "groceries": {
        "primary": PersonalFinanceCategoryPrimary.GENERAL_MERCHANDISE,
        "detailed": PersonalFinanceCategoryDetailed.GROCERIES
    },
    "gas_station": {
        "primary": PersonalFinanceCategoryPrimary.GAS_STATIONS,
        "detailed": PersonalFinanceCategoryDetailed.GAS_STATIONS
    },
    "restaurant": {
        "primary": PersonalFinanceCategoryPrimary.FOOD_AND_DRINK,
        "detailed": PersonalFinanceCategoryDetailed.RESTAURANTS
    },
    "retail": {
        "primary": PersonalFinanceCategoryPrimary.GENERAL_MERCHANDISE,
        "detailed": PersonalFinanceCategoryDetailed.GENERAL_MERCHANDISE
    },
    "utilities": {
        "primary": PersonalFinanceCategoryPrimary.GENERAL_SERVICES,
        "detailed": PersonalFinanceCategoryDetailed.UTILITIES
    },
    "healthcare": {
        "primary": PersonalFinanceCategoryPrimary.GENERAL_SERVICES,
        "detailed": PersonalFinanceCategoryDetailed.HEALTHCARE
    },
    "transportation": {
        "primary": PersonalFinanceCategoryPrimary.TRANSPORTATION,
        "detailed": PersonalFinanceCategoryDetailed.TRANSPORTATION
    },
    "entertainment": {
        "primary": PersonalFinanceCategoryPrimary.ENTERTAINMENT,
        "detailed": PersonalFinanceCategoryDetailed.ENTERTAINMENT
    },
    "online_shopping": {
        "primary": PersonalFinanceCategoryPrimary.GENERAL_MERCHANDISE,
        "detailed": PersonalFinanceCategoryDetailed.GENERAL_MERCHANDISE
    },
    "other": {
        "primary": PersonalFinanceCategoryPrimary.GENERAL_MERCHANDISE,
        "detailed": PersonalFinanceCategoryDetailed.GENERAL_MERCHANDISE
    }
}


# Payment Method → Payment Channel Mapping
PAYMENT_CHANNEL_MAP = {
    "debit_card": PaymentChannel.ONLINE,
    "credit_card": PaymentChannel.ONLINE,
    "bank_transfer": PaymentChannel.OTHER,
    "digital_wallet": PaymentChannel.ONLINE,
    "cash": PaymentChannel.OTHER
}


# Payment Method → Account Type Mapping
PAYMENT_METHOD_TO_ACCOUNT_TYPE = {
    "credit_card": (AccountType.CREDIT, AccountSubtype.CREDIT_CARD),
    "debit_card": (AccountType.DEPOSITORY, AccountSubtype.CHECKING),
    "bank_transfer": (AccountType.DEPOSITORY, AccountSubtype.CHECKING),
    "digital_wallet": (AccountType.DEPOSITORY, AccountSubtype.CHECKING),
    "cash": None  # Cash transactions don't have accounts
}


# Merchant Name Generation (deterministic)
MERCHANT_NAME_TEMPLATES = {
    "groceries": ["Whole Foods", "Safeway", "Kroger", "Walmart", "Target", "Costco"],
    "gas_station": ["Shell", "Exxon", "BP", "Chevron", "Mobil", "76"],
    "restaurant": ["McDonald's", "Starbucks", "Chipotle", "Subway", "Pizza Hut", "Taco Bell"],
    "retail": ["Amazon", "Walmart", "Target", "Best Buy", "Home Depot", "Lowe's"],
    "utilities": ["Electric Company", "Water Utility", "Gas Company", "Internet Provider"],
    "healthcare": ["CVS Pharmacy", "Walgreens", "Medical Center", "Hospital", "Clinic"],
    "transportation": ["Uber", "Lyft", "Metro Transit", "Taxi", "Bus Line"],
    "entertainment": ["Netflix", "Spotify", "Movie Theater", "Concert Hall", "Theme Park"],
    "online_shopping": ["Amazon", "eBay", "Etsy", "Shopify", "Online Store"],
    "other": ["General Store", "Merchant", "Vendor", "Service", "Business"]
}


# ============================================================================
# Phase 1: Account Discovery & Synthesis
# ============================================================================

def discover_accounts(df: pd.DataFrame) -> Dict[str, List[Account]]:
    """
    Discover and synthesize accounts from transaction data.
    
    Groups transactions by customer_id and payment_method to identify
    distinct accounts per customer.
    
    Args:
        df: DataFrame with transactions (must have customer_id, payment_method, account_balance)
        
    Returns:
        Dictionary mapping customer_id to list of Account objects
    """
    accounts_by_customer = defaultdict(list)
    
    # Group by customer_id and payment_method
    for (customer_id, payment_method), group in df.groupby(['customer_id', 'payment_method']):
        # Skip cash transactions (no account)
        if payment_method == "cash":
            continue
        
        # Get account type/subtype from payment method
        account_type_info = PAYMENT_METHOD_TO_ACCOUNT_TYPE.get(payment_method)
        if account_type_info is None:
            continue
        
        account_type, account_subtype = account_type_info
        
        # Generate account_id (deterministic)
        account_index = len(accounts_by_customer[customer_id]) + 1
        account_id = f"ACC-{customer_id}-{account_subtype.value.replace(' ', '_').upper()}-{account_index}"
        
        # Calculate balances
        balances = calculate_account_balances(group, account_type)
        
        # Create account
        account = Account(
            account_id=account_id,
            customer_id=customer_id,
            type=account_type,
            subtype=account_subtype,
            balances=balances,
            iso_currency_code="USD",
            holder_category=HolderCategory.CONSUMER
        )
        
        accounts_by_customer[customer_id].append(account)
    
    return dict(accounts_by_customer)


def calculate_account_balances(group: pd.DataFrame, account_type: AccountType) -> AccountBalances:
    """
    Calculate account balances from transaction history.
    
    Args:
        group: DataFrame with transactions for a single account
        account_type: Type of account (depository or credit)
        
    Returns:
        AccountBalances object with available, current, and limit
    """
    # Sort by date to process chronologically
    group = group.sort_values('date')
    
    # Get the latest balance (post-transaction balance from CSV)
    latest_balance = group['account_balance'].iloc[-1]
    
    # For credit cards, estimate limit from max balance
    limit = None
    if account_type == AccountType.CREDIT:
        max_balance = group['account_balance'].max()
        # Estimate limit as max_balance * 1.3 (30% buffer) or max_balance * 2.0
        # Use the more conservative estimate
        estimated_limit_1 = max_balance * 1.3
        estimated_limit_2 = max_balance * 2.0
        limit = max(estimated_limit_1, estimated_limit_2)
        # Round to nearest $500 (industry standard)
        limit = round(limit / 500) * 500
        # Ensure limit is at least max_balance
        limit = max(limit, max_balance)
    
    # For depository accounts, available balance = current balance
    available = latest_balance if account_type == AccountType.DEPOSITORY else None
    
    return AccountBalances(
        available=available,
        current=latest_balance,
        limit=limit
    )


# ============================================================================
# Phase 2: Transaction Enhancement
# ============================================================================

def enhance_transactions(
    df: pd.DataFrame,
    accounts_by_customer: Dict[str, List[Account]]
) -> List[Transaction]:
    """
    Enhance transactions with account_id, merchant_name, and Plaid categories.
    
    Args:
        df: DataFrame with raw transactions
        accounts_by_customer: Dictionary mapping customer_id to list of accounts
        
    Returns:
        List of enhanced Transaction objects
    """
    transactions = []
    
    # Create account lookup map
    account_lookup = create_account_lookup(accounts_by_customer)
    
    for _, row in df.iterrows():
        # Get account_id from lookup
        # For cash transactions, try to map to checking account
        if row['payment_method'] == 'cash':
            # Cash transactions typically come from checking accounts
            # Try to find a checking account for this customer
            account_id = account_lookup.get((row['customer_id'], 'debit_card'))
            if account_id is None:
                # Fallback: try any depository account
                account_id = account_lookup.get((row['customer_id'], 'bank_transfer'))
            if account_id is None:
                # No checking account found, skip cash transaction
                continue
        else:
            account_id = account_lookup.get((row['customer_id'], row['payment_method']))
            if account_id is None:
                continue  # Skip if no account found
        
        # Generate merchant_name
        merchant_name = generate_merchant_name(row['merchant_id'], row['merchant_category'])
        
        # Transform merchant_category to Plaid format
        category_info = CATEGORY_MAP.get(row['merchant_category'], CATEGORY_MAP['other'])
        personal_finance_category = PersonalFinanceCategory(
            primary=category_info['primary'],
            detailed=category_info['detailed']
        )
        
        # Map payment_method to payment_channel
        payment_channel = PAYMENT_CHANNEL_MAP.get(row['payment_method'], PaymentChannel.OTHER)
        
        # Map status to pending boolean
        pending = row['status'] == 'pending'
        
        # Create transaction
        transaction = Transaction(
            transaction_id=row['transaction_id'],
            account_id=account_id,
            date=pd.to_datetime(row['date']).date(),
            amount=float(row['amount']),
            merchant_name=merchant_name,
            merchant_entity_id=row['merchant_id'],
            payment_channel=payment_channel,
            personal_finance_category=personal_finance_category,
            pending=pending,
            iso_currency_code="USD"
        )
        
        transactions.append(transaction)
    
    return transactions


def create_account_lookup(accounts_by_customer: Dict[str, List[Account]]) -> Dict[Tuple[str, str], str]:
    """
    Create lookup map from (customer_id, payment_method) to account_id.
    
    Args:
        accounts_by_customer: Dictionary mapping customer_id to list of accounts
        
    Returns:
        Dictionary mapping (customer_id, payment_method) to account_id
    """
    lookup = {}
    
    for customer_id, accounts in accounts_by_customer.items():
        for account in accounts:
            # Map payment methods to accounts based on account type/subtype
            if account.type == AccountType.CREDIT:
                # Credit card accounts only accept credit_card transactions
                payment_methods = ["credit_card"]
            elif account.subtype == AccountSubtype.CHECKING:
                # Checking accounts accept multiple payment methods
                payment_methods = ["debit_card", "digital_wallet", "bank_transfer"]
            elif account.subtype == AccountSubtype.SAVINGS:
                # Savings accounts typically via bank transfer
                payment_methods = ["bank_transfer"]
            else:
                # Default: accept debit_card and digital_wallet
                payment_methods = ["debit_card", "digital_wallet"]
            
            # Create lookup entries for all applicable payment methods
            for payment_method in payment_methods:
                key = (customer_id, payment_method)
                # Use first account found for each payment_method (may have multiple accounts)
                if key not in lookup:
                    lookup[key] = account.account_id
    
    return lookup


def generate_merchant_name(merchant_id: str, merchant_category: str) -> str:
    """
    Generate deterministic merchant name from merchant_id and category.
    
    Same merchant_id always produces the same name.
    
    Args:
        merchant_id: Merchant identifier (e.g., "MERCH000159")
        merchant_category: Merchant category (e.g., "groceries")
        
    Returns:
        Merchant name (e.g., "Whole Foods #159")
    """
    # Get merchant name templates for category
    templates = MERCHANT_NAME_TEMPLATES.get(merchant_category, MERCHANT_NAME_TEMPLATES['other'])
    
    # Use hash of merchant_id to deterministically select template
    merchant_hash = int(hashlib.md5(merchant_id.encode()).hexdigest(), 16)
    template_index = merchant_hash % len(templates)
    template_name = templates[template_index]
    
    # Extract last 3 digits from merchant_id for uniqueness
    merchant_number = merchant_id[-3:] if len(merchant_id) >= 3 else merchant_id
    
    return f"{template_name} #{merchant_number}"


# ============================================================================
# Phase 3: Liability Synthesis
# ============================================================================

def synthesize_liabilities(
    accounts: List[Account],
    transactions: List[Transaction],
    df: pd.DataFrame
) -> List[CreditCardLiability]:
    """
    Synthesize credit card liability data from transactions.
    
    Args:
        accounts: List of Account objects
        transactions: List of Transaction objects
        df: Original DataFrame with transactions
        
    Returns:
        List of CreditCardLiability objects for credit card accounts
    """
    liabilities = []
    
    # Filter to credit card accounts only
    credit_card_accounts = [acc for acc in accounts if acc.type == AccountType.CREDIT]
    
    for account in credit_card_accounts:
        # Get all transactions for this account
        account_transactions = [t for t in transactions if t.account_id == account.account_id]
        
        if not account_transactions:
            continue
        
        # Extract payment history
        payment_history = extract_payment_history(account, df)
        
        # Synthesize APR based on utilization
        aprs = synthesize_apr(account)
        
        # Calculate minimum payment
        minimum_payment = calculate_minimum_payment(account.balances.current)
        
        # Determine overdue status
        is_overdue = determine_overdue_status(payment_history, account.balances.current)
        
        # Estimate next payment due date
        next_payment_due_date = estimate_next_payment_due_date(payment_history)
        
        # Get last payment amount
        last_payment_amount = payment_history[-1]['amount'] if payment_history else None
        
        # Create liability
        liability = CreditCardLiability(
            account_id=account.account_id,
            aprs=aprs,
            minimum_payment_amount=minimum_payment,
            last_payment_amount=last_payment_amount,
            is_overdue=is_overdue,
            next_payment_due_date=next_payment_due_date,
            last_statement_balance=account.balances.current
        )
        
        liabilities.append(liability)
    
    return liabilities


def extract_payment_history(account: Account, df: pd.DataFrame) -> List[Dict]:
    """
    Extract credit card payment history from transactions.
    
    Payments are identified as:
    - Transactions with negative amounts (payments to credit card)
    - Transfers to credit card account
    - Deposits to credit card account
    
    Args:
        account: Credit card Account object
        df: Original DataFrame with transactions
        
    Returns:
        List of payment records with date and amount
    """
    payments = []
    
    # Get customer_id from account
    customer_id = account.customer_id
    
    # Filter transactions for this customer with credit card payment method
    customer_transactions = df[df['customer_id'] == customer_id]
    credit_transactions = customer_transactions[customer_transactions['payment_method'] == 'credit_card']
    
    # Find payment transactions (negative amounts or transfers)
    for _, row in credit_transactions.iterrows():
        # Negative amounts are payments
        if row['amount'] < 0:
            payments.append({
                'date': pd.to_datetime(row['date']).date(),
                'amount': abs(row['amount'])  # Store as positive
            })
        # Transfers or deposits might be payments
        elif row['transaction_type'] in ['transfer', 'deposit'] and row['amount'] > 0:
            payments.append({
                'date': pd.to_datetime(row['date']).date(),
                'amount': row['amount']
            })
    
    # Sort by date (most recent first)
    payments.sort(key=lambda x: x['date'], reverse=True)
    
    return payments


def synthesize_apr(account: Account) -> List[CreditCardAPR]:
    """
    Synthesize APR based on credit card utilization.
    
    Higher utilization = higher APR (more risk).
    
    Args:
        account: Credit card Account object
        
    Returns:
        List of CreditCardAPR objects
    """
    if account.balances.limit is None or account.balances.limit == 0:
        # Default APR if no limit
        base_apr = 18.99
    else:
        # Calculate utilization
        utilization = account.balances.current / account.balances.limit
        
        # Base APR based on utilization tier
        if utilization < 0.30:
            base_apr = 18.99  # Good credit
        elif utilization < 0.50:
            base_apr = 22.99  # Moderate risk
        elif utilization < 0.80:
            base_apr = 25.99  # High risk
        else:
            base_apr = 28.99  # Very high risk
    
    # Create APR object
    apr = CreditCardAPR(
        type="purchase",
        percentage=round(base_apr, 2)
    )
    
    return [apr]


def calculate_minimum_payment(balance: float) -> float:
    """
    Calculate minimum payment amount (industry standard: 2% of balance or $25).
    
    Args:
        balance: Current credit card balance
        
    Returns:
        Minimum payment amount (rounded to nearest dollar)
    """
    if balance <= 0:
        return 0.0
    
    # Industry standard: 2% of balance or $25, whichever is higher
    minimum = max(balance * 0.02, 25.0)
    
    # Round to nearest dollar
    return round(minimum)


def determine_overdue_status(payment_history: List[Dict], current_balance: float) -> bool:
    """
    Determine if credit card account is overdue.
    
    Account is overdue if:
    - Balance > 0
    - No payment in last 30 days
    
    Args:
        payment_history: List of payment records (sorted by date, most recent first)
        current_balance: Current credit card balance
        
    Returns:
        True if overdue, False otherwise
    """
    if current_balance <= 0:
        return False  # No balance, not overdue
    
    if not payment_history:
        # No payment history, check if balance exists for more than 30 days
        # This is a simplified check - in real system, would check statement date
        return True  # Assume overdue if no payments
    
    # Get most recent payment date
    last_payment_date = payment_history[0]['date']
    days_since_payment = (date.today() - last_payment_date).days
    
    # Overdue if no payment in 30+ days
    return days_since_payment > 30


def estimate_next_payment_due_date(payment_history: List[Dict]) -> Optional[date]:
    """
    Estimate next payment due date from payment history.
    
    Args:
        payment_history: List of payment records (sorted by date, most recent first)
        
    Returns:
        Estimated next payment due date, or None if no history
    """
    if not payment_history or len(payment_history) < 2:
        # Not enough history, estimate 30 days from today
        return date.today() + timedelta(days=30)
    
    # Calculate average payment interval
    intervals = []
    for i in range(len(payment_history) - 1):
        interval = (payment_history[i]['date'] - payment_history[i + 1]['date']).days
        intervals.append(interval)
    
    if intervals:
        avg_interval = sum(intervals) / len(intervals)
    else:
        avg_interval = 30  # Default to monthly
    
    # Estimate next due date from most recent payment
    last_payment_date = payment_history[0]['date']
    next_due_date = last_payment_date + timedelta(days=int(avg_interval))
    
    # Ensure due date is in future
    if next_due_date < date.today():
        next_due_date = date.today() + timedelta(days=30)
    
    return next_due_date


# ============================================================================
# Main Synthesis Function
# ============================================================================

def synthesize_data(csv_path: str) -> Tuple[List[Account], List[Transaction], List[CreditCardLiability]]:
    """
    Main function to synthesize Plaid-compatible data from Capital One CSV.
    
    Args:
        csv_path: Path to input CSV file
        
    Returns:
        Tuple of (accounts, transactions, liabilities)
    """
    # Load CSV
    df = pd.read_csv(csv_path)
    
    # Ensure date column is datetime
    df['date'] = pd.to_datetime(df['date'])
    
    # Phase 1: Discover and synthesize accounts
    accounts_by_customer = discover_accounts(df)
    all_accounts = [acc for accounts in accounts_by_customer.values() for acc in accounts]
    
    # Phase 2: Enhance transactions
    transactions = enhance_transactions(df, accounts_by_customer)
    
    # Phase 3: Synthesize liabilities
    liabilities = synthesize_liabilities(all_accounts, transactions, df)
    
    return all_accounts, transactions, liabilities

