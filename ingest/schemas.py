"""
Plaid-compatible data schemas for SpendSenseAI.

This module defines the data structures that match Plaid's API format
for Accounts, Transactions, and Liabilities.
"""

from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional, Literal
from enum import Enum


# ============================================================================
# Account Types & Subtypes
# ============================================================================

class AccountType(str, Enum):
    """Account types as defined by Plaid."""
    DEPOSITORY = "depository"
    CREDIT = "credit"
    LOAN = "loan"
    INVESTMENT = "investment"
    OTHER = "other"


class AccountSubtype(str, Enum):
    """Account subtypes as defined by Plaid."""
    # Depository subtypes
    CHECKING = "checking"
    SAVINGS = "savings"
    MONEY_MARKET = "money market"
    CASH_MANAGEMENT = "cash management"
    HSA = "hsa"
    
    # Credit subtypes
    CREDIT_CARD = "credit card"
    
    # Loan subtypes
    MORTGAGE = "mortgage"
    STUDENT = "student"
    AUTO = "auto"
    
    # Other
    OTHER = "other"


class HolderCategory(str, Enum):
    """Account holder category."""
    CONSUMER = "consumer"
    BUSINESS = "business"


# ============================================================================
# Transaction Categories (Plaid Personal Finance Categories)
# ============================================================================

class PersonalFinanceCategoryPrimary(str, Enum):
    """Primary personal finance categories as defined by Plaid."""
    GENERAL_MERCHANDISE = "GENERAL_MERCHANDISE"
    FOOD_AND_DRINK = "FOOD_AND_DRINK"
    GAS_STATIONS = "GAS_STATIONS"
    TRANSPORTATION = "TRANSPORTATION"
    ENTERTAINMENT = "ENTERTAINMENT"
    GENERAL_SERVICES = "GENERAL_SERVICES"
    TRAVEL = "TRAVEL"
    TRANSFER_IN = "TRANSFER_IN"
    TRANSFER_OUT = "TRANSFER_OUT"
    LOAN_PAYMENTS = "LOAN_PAYMENTS"
    BANK_FEES = "BANK_FEES"
    INCOME = "INCOME"
    OTHER = "OTHER"


class PersonalFinanceCategoryDetailed(str, Enum):
    """Detailed personal finance categories as defined by Plaid."""
    # General Merchandise
    GROCERIES = "GROCERIES"
    GENERAL_MERCHANDISE = "GENERAL_MERCHANDISE"
    
    # Food and Drink
    RESTAURANTS = "RESTAURANTS"
    FOOD_AND_DRINK = "FOOD_AND_DRINK"
    
    # Gas Stations
    GAS_STATIONS = "GAS_STATIONS"
    
    # Transportation
    TRANSPORTATION = "TRANSPORTATION"
    
    # Entertainment
    ENTERTAINMENT = "ENTERTAINMENT"
    
    # General Services
    UTILITIES = "UTILITIES"
    HEALTHCARE = "HEALTHCARE"
    GENERAL_SERVICES = "GENERAL_SERVICES"
    
    # Other
    TRAVEL = "TRAVEL"
    TRANSFER_IN = "TRANSFER_IN"
    TRANSFER_OUT = "TRANSFER_OUT"
    LOAN_PAYMENTS = "LOAN_PAYMENTS"
    BANK_FEES = "BANK_FEES"
    INCOME = "INCOME"
    OTHER = "OTHER"


class PaymentChannel(str, Enum):
    """Payment channels as defined by Plaid."""
    ONLINE = "online"
    IN_STORE = "in store"
    ATM = "atm"
    OTHER = "other"


# ============================================================================
# Account Schema
# ============================================================================

@dataclass
class AccountBalances:
    """Account balance information."""
    available: Optional[float] = None  # Available balance
    current: float = 0.0  # Current balance
    limit: Optional[float] = None  # Credit limit (for credit cards)


@dataclass
class Account:
    """
    Account schema matching Plaid's Account object.
    
    Attributes:
        account_id: Unique identifier for the account
        customer_id: Customer/user identifier
        type: Account type (depository, credit, loan, etc.)
        subtype: Account subtype (checking, savings, credit_card, etc.)
        balances: Account balances (available, current, limit)
        iso_currency_code: ISO 4217 currency code (e.g., "USD")
        holder_category: Account holder category (consumer or business)
    """
    account_id: str
    customer_id: str
    type: AccountType
    subtype: AccountSubtype
    balances: AccountBalances
    iso_currency_code: str = "USD"
    holder_category: HolderCategory = HolderCategory.CONSUMER
    
    def __post_init__(self):
        """Validate account data after initialization."""
        # Credit accounts must have a limit
        if self.type == AccountType.CREDIT and self.balances.limit is None:
            raise ValueError("Credit accounts must have a limit")
        
        # Credit limit must be >= current balance
        if self.balances.limit is not None:
            if self.balances.limit < self.balances.current:
                raise ValueError(
                    f"Credit limit ({self.balances.limit}) must be >= "
                    f"current balance ({self.balances.current})"
                )
        
        # Depository accounts should not have limits
        if self.type == AccountType.DEPOSITORY and self.balances.limit is not None:
            # This is a warning, not an error (some accounts might have overdraft limits)
            pass
        
        # Validate currency code
        if len(self.iso_currency_code) != 3:
            raise ValueError(
                f"Invalid ISO currency code: {self.iso_currency_code}. "
                "Must be 3 characters (e.g., 'USD')"
            )


# ============================================================================
# Transaction Schema
# ============================================================================

@dataclass
class PersonalFinanceCategory:
    """Personal finance category information."""
    primary: PersonalFinanceCategoryPrimary
    detailed: PersonalFinanceCategoryDetailed


@dataclass
class Transaction:
    """
    Transaction schema matching Plaid's Transaction object.
    
    Attributes:
        transaction_id: Unique identifier for the transaction
        account_id: Account identifier this transaction belongs to
        date: Transaction date (YYYY-MM-DD)
        amount: Transaction amount (positive for debits, negative for credits)
        merchant_name: Merchant name (if available)
        merchant_entity_id: Merchant entity identifier (if merchant_name not available)
        payment_channel: Payment channel (online, in store, atm, other)
        personal_finance_category: Personal finance category (primary/detailed)
        pending: Whether transaction is pending
        iso_currency_code: ISO 4217 currency code (e.g., "USD")
    """
    transaction_id: str
    account_id: str
    date: date
    amount: float
    merchant_name: Optional[str] = None
    merchant_entity_id: Optional[str] = None
    payment_channel: PaymentChannel = PaymentChannel.ONLINE
    personal_finance_category: Optional[PersonalFinanceCategory] = None
    pending: bool = False
    iso_currency_code: str = "USD"
    
    def __post_init__(self):
        """Validate transaction data after initialization."""
        # Must have either merchant_name or merchant_entity_id
        if not self.merchant_name and not self.merchant_entity_id:
            raise ValueError(
                "Transaction must have either merchant_name or merchant_entity_id"
            )
        
        # Validate currency code
        if len(self.iso_currency_code) != 3:
            raise ValueError(
                f"Invalid ISO currency code: {self.iso_currency_code}. "
                "Must be 3 characters (e.g., 'USD')"
            )
        
        # Validate amount is not zero
        if self.amount == 0.0:
            raise ValueError("Transaction amount cannot be zero")
        
        # Validate date is not in the future
        if self.date > date.today():
            raise ValueError(f"Transaction date ({self.date}) cannot be in the future")


# ============================================================================
# Liability Schema
# ============================================================================

@dataclass
class CreditCardAPR:
    """Credit card APR information."""
    type: str  # e.g., "purchase", "balance_transfer", "cash_advance"
    percentage: float  # APR percentage (e.g., 18.99 for 18.99%)


@dataclass
class CreditCardLiability:
    """
    Credit card liability schema matching Plaid's CreditCardLiability object.
    
    Attributes:
        account_id: Account identifier for the credit card
        aprs: List of APRs (purchase, balance transfer, cash advance)
        minimum_payment_amount: Minimum payment amount
        last_payment_amount: Last payment amount made
        is_overdue: Whether the account is overdue
        next_payment_due_date: Next payment due date
        last_statement_balance: Last statement balance
    """
    account_id: str
    aprs: list[CreditCardAPR]
    minimum_payment_amount: float
    last_payment_amount: Optional[float] = None
    is_overdue: bool = False
    next_payment_due_date: Optional[date] = None
    last_statement_balance: Optional[float] = None
    
    def __post_init__(self):
        """Validate liability data after initialization."""
        # Minimum payment must be positive
        if self.minimum_payment_amount <= 0:
            raise ValueError(
                f"Minimum payment amount ({self.minimum_payment_amount}) must be > 0"
            )
        
        # APR must be between 0 and 100 (as percentage)
        for apr in self.aprs:
            if apr.percentage < 0 or apr.percentage > 100:
                raise ValueError(
                    f"APR percentage ({apr.percentage}) must be between 0 and 100"
                )
        
        # Due date must be in future if provided
        if self.next_payment_due_date and self.next_payment_due_date < date.today():
            # This is a warning, not an error (account might be overdue)
            pass
        
        # Last payment amount must be positive if provided
        if self.last_payment_amount is not None and self.last_payment_amount <= 0:
            raise ValueError(
                f"Last payment amount ({self.last_payment_amount}) must be > 0"
            )


@dataclass
class LoanLiability:
    """
    Loan liability schema matching Plaid's LoanLiability object.
    
    Attributes:
        account_id: Account identifier for the loan
        interest_rate: Interest rate percentage
        next_payment_due_date: Next payment due date
    """
    account_id: str
    interest_rate: float
    next_payment_due_date: Optional[date] = None
    
    def __post_init__(self):
        """Validate loan liability data after initialization."""
        # Interest rate must be between 0 and 100 (as percentage)
        if self.interest_rate < 0 or self.interest_rate > 100:
            raise ValueError(
                f"Interest rate ({self.interest_rate}) must be between 0 and 100"
            )


# ============================================================================
# Schema Validation Functions
# ============================================================================

def validate_account(account: Account) -> list[str]:
    """
    Validate an Account object.
    
    Args:
        account: Account object to validate
        
    Returns:
        List of validation errors (empty if valid)
    """
    errors = []
    
    # Validate account_id format
    if not account.account_id or len(account.account_id) < 3:
        errors.append("account_id must be at least 3 characters")
    
    # Validate customer_id format
    if not account.customer_id or len(account.customer_id) < 3:
        errors.append("customer_id must be at least 3 characters")
    
    # Validate balances
    if account.balances.current < 0 and account.type == AccountType.DEPOSITORY:
        errors.append("Depository account balance cannot be negative")
    
    # Validate credit limit
    if account.type == AccountType.CREDIT:
        if account.balances.limit is None:
            errors.append("Credit account must have a limit")
        elif account.balances.limit <= 0:
            errors.append("Credit limit must be > 0")
        elif account.balances.current > account.balances.limit:
            errors.append("Current balance exceeds credit limit")
    
    return errors


def validate_transaction(transaction: Transaction) -> list[str]:
    """
    Validate a Transaction object.
    
    Args:
        transaction: Transaction object to validate
        
    Returns:
        List of validation errors (empty if valid)
    """
    errors = []
    
    # Validate transaction_id format
    if not transaction.transaction_id or len(transaction.transaction_id) < 3:
        errors.append("transaction_id must be at least 3 characters")
    
    # Validate account_id format
    if not transaction.account_id or len(transaction.account_id) < 3:
        errors.append("account_id must be at least 3 characters")
    
    # Validate amount
    if transaction.amount == 0.0:
        errors.append("Transaction amount cannot be zero")
    
    # Validate merchant information
    if not transaction.merchant_name and not transaction.merchant_entity_id:
        errors.append("Transaction must have merchant_name or merchant_entity_id")
    
    return errors


def validate_credit_card_liability(liability: CreditCardLiability) -> list[str]:
    """
    Validate a CreditCardLiability object.
    
    Args:
        liability: CreditCardLiability object to validate
        
    Returns:
        List of validation errors (empty if valid)
    """
    errors = []
    
    # Validate account_id format
    if not liability.account_id or len(liability.account_id) < 3:
        errors.append("account_id must be at least 3 characters")
    
    # Validate minimum payment
    if liability.minimum_payment_amount <= 0:
        errors.append("Minimum payment amount must be > 0")
    
    # Validate APRs
    if not liability.aprs:
        errors.append("Credit card must have at least one APR")
    
    for apr in liability.aprs:
        if apr.percentage < 0 or apr.percentage > 100:
            errors.append(f"APR percentage ({apr.percentage}) must be between 0 and 100")
    
    # Validate last payment amount if provided
    if liability.last_payment_amount is not None:
        if liability.last_payment_amount <= 0:
            errors.append("Last payment amount must be > 0")
    
    return errors

