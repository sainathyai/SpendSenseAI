# Plaid-Compatible Schema Documentation

## Overview

This document describes the data schemas used in SpendSenseAI, which are designed to be compatible with Plaid's API format. This ensures our system can work with real Plaid data in the future.

---

## Account Schema

### Structure

```python
Account(
    account_id: str,              # Unique identifier (e.g., "ACC-CUST000135-CHECKING-1")
    customer_id: str,             # Customer identifier (e.g., "CUST000135")
    type: AccountType,            # "depository", "credit", "loan", "investment", "other"
    subtype: AccountSubtype,      # "checking", "savings", "credit_card", etc.
    balances: AccountBalances,    # Balance information
    iso_currency_code: str,       # ISO 4217 code (e.g., "USD")
    holder_category: HolderCategory  # "consumer" or "business"
)
```

### AccountBalances

```python
AccountBalances(
    available: Optional[float],   # Available balance (for depository accounts)
    current: float,               # Current balance (required)
    limit: Optional[float]        # Credit limit (for credit cards)
)
```

### Account Types

| Type | Description | Subtypes |
|------|-------------|----------|
| `depository` | Bank accounts | `checking`, `savings`, `money market`, `cash management`, `hsa` |
| `credit` | Credit cards | `credit_card` |
| `loan` | Loans | `mortgage`, `student`, `auto` |
| `investment` | Investment accounts | (future) |
| `other` | Other accounts | `other` |

### Validation Rules

1. **Credit accounts** must have a `limit`
2. **Credit limit** must be >= current balance
3. **Depository accounts** should not have limits (except overdraft)
4. **Currency code** must be 3 characters (e.g., "USD")

### Example

```python
Account(
    account_id="ACC-CUST000135-CHECKING-1",
    customer_id="CUST000135",
    type=AccountType.DEPOSITORY,
    subtype=AccountSubtype.CHECKING,
    balances=AccountBalances(
        available=6846.96,
        current=6846.96,
        limit=None
    ),
    iso_currency_code="USD",
    holder_category=HolderCategory.CONSUMER
)
```

---

## Transaction Schema

### Structure

```python
Transaction(
    transaction_id: str,                    # Unique identifier
    account_id: str,                       # Account identifier
    date: date,                            # Transaction date (YYYY-MM-DD)
    amount: float,                         # Amount (positive for debits, negative for credits)
    merchant_name: Optional[str],         # Merchant name
    merchant_entity_id: Optional[str],     # Merchant entity ID (if merchant_name not available)
    payment_channel: PaymentChannel,       # "online", "in store", "atm", "other"
    personal_finance_category: Optional[PersonalFinanceCategory],  # Category info
    pending: bool,                         # Whether transaction is pending
    iso_currency_code: str                 # ISO 4217 code (e.g., "USD")
)
```

### PersonalFinanceCategory

```python
PersonalFinanceCategory(
    primary: PersonalFinanceCategoryPrimary,    # Primary category
    detailed: PersonalFinanceCategoryDetailed   # Detailed category
)
```

### Payment Channels

| Channel | Description |
|---------|-------------|
| `online` | Online transactions (credit cards, debit cards, digital wallets) |
| `in store` | In-store transactions |
| `atm` | ATM transactions |
| `other` | Other payment methods |

### Personal Finance Categories

#### Primary Categories

| Category | Description |
|----------|-------------|
| `GENERAL_MERCHANDISE` | General merchandise purchases |
| `FOOD_AND_DRINK` | Food and drink purchases |
| `GAS_STATIONS` | Gas station purchases |
| `TRANSPORTATION` | Transportation expenses |
| `ENTERTAINMENT` | Entertainment expenses |
| `GENERAL_SERVICES` | General services (utilities, healthcare) |
| `TRAVEL` | Travel expenses |
| `TRANSFER_IN` | Money transfers in |
| `TRANSFER_OUT` | Money transfers out |
| `LOAN_PAYMENTS` | Loan payments |
| `BANK_FEES` | Bank fees |
| `INCOME` | Income deposits |
| `OTHER` | Other transactions |

#### Detailed Categories

| Category | Description |
|----------|-------------|
| `GROCERIES` | Grocery purchases |
| `RESTAURANTS` | Restaurant purchases |
| `GAS_STATIONS` | Gas station purchases |
| `UTILITIES` | Utility bills |
| `HEALTHCARE` | Healthcare expenses |
| `TRANSPORTATION` | Transportation expenses |
| `ENTERTAINMENT` | Entertainment expenses |
| `TRAVEL` | Travel expenses |
| `TRANSFER_IN` | Money transfers in |
| `TRANSFER_OUT` | Money transfers out |
| `LOAN_PAYMENTS` | Loan payments |
| `BANK_FEES` | Bank fees |
| `INCOME` | Income deposits |
| `OTHER` | Other transactions |

### Validation Rules

1. Must have either `merchant_name` or `merchant_entity_id`
2. `amount` cannot be zero
3. `date` cannot be in the future
4. `currency_code` must be 3 characters

### Example

```python
Transaction(
    transaction_id="TXN00000001",
    account_id="ACC-CUST000135-CHECKING-1",
    date=date(2024, 1, 1),
    amount=100.46,
    merchant_name="Groceries Store #159",
    merchant_entity_id="MERCH000159",
    payment_channel=PaymentChannel.ONLINE,
    personal_finance_category=PersonalFinanceCategory(
        primary=PersonalFinanceCategoryPrimary.GENERAL_MERCHANDISE,
        detailed=PersonalFinanceCategoryDetailed.GROCERIES
    ),
    pending=False,
    iso_currency_code="USD"
)
```

---

## Liability Schema

### CreditCardLiability

#### Structure

```python
CreditCardLiability(
    account_id: str,                    # Account identifier
    aprs: list[CreditCardAPR],          # List of APRs
    minimum_payment_amount: float,      # Minimum payment amount
    last_payment_amount: Optional[float],  # Last payment amount
    is_overdue: bool,                   # Whether account is overdue
    next_payment_due_date: Optional[date],  # Next payment due date
    last_statement_balance: Optional[float]  # Last statement balance
)
```

#### CreditCardAPR

```python
CreditCardAPR(
    type: str,              # "purchase", "balance_transfer", "cash_advance"
    percentage: float       # APR percentage (e.g., 18.99 for 18.99%)
)
```

#### Validation Rules

1. `minimum_payment_amount` must be > 0
2. APR percentage must be between 0 and 100
3. `last_payment_amount` must be > 0 if provided
4. `next_payment_due_date` should be in the future (if not overdue)

#### Example

```python
CreditCardLiability(
    account_id="ACC-CUST000036-CREDIT-1",
    aprs=[
        CreditCardAPR(type="purchase", percentage=18.99)
    ],
    minimum_payment_amount=111.00,
    last_payment_amount=500.00,
    is_overdue=False,
    next_payment_due_date=date(2024, 2, 15),
    last_statement_balance=5550.00
)
```

### LoanLiability

#### Structure

```python
LoanLiability(
    account_id: str,                    # Account identifier
    interest_rate: float,               # Interest rate percentage
    next_payment_due_date: Optional[date]  # Next payment due date
)
```

#### Validation Rules

1. `interest_rate` must be between 0 and 100

#### Example

```python
LoanLiability(
    account_id="ACC-CUST000036-MORTGAGE-1",
    interest_rate=3.5,
    next_payment_due_date=date(2024, 2, 1)
)
```

---

## Category Mapping

### Capital One Categories → Plaid Categories

| Capital One Category | Plaid Primary | Plaid Detailed |
|----------------------|---------------|----------------|
| `groceries` | `GENERAL_MERCHANDISE` | `GROCERIES` |
| `gas_station` | `GAS_STATIONS` | `GAS_STATIONS` |
| `restaurant` | `FOOD_AND_DRINK` | `RESTAURANTS` |
| `retail` | `GENERAL_MERCHANDISE` | `GENERAL_MERCHANDISE` |
| `utilities` | `GENERAL_SERVICES` | `UTILITIES` |
| `healthcare` | `GENERAL_SERVICES` | `HEALTHCARE` |
| `transportation` | `TRANSPORTATION` | `TRANSPORTATION` |
| `entertainment` | `ENTERTAINMENT` | `ENTERTAINMENT` |
| `online_shopping` | `GENERAL_MERCHANDISE` | `GENERAL_MERCHANDISE` |
| `other` | `GENERAL_MERCHANDISE` | `GENERAL_MERCHANDISE` |

---

## Payment Method Mapping

### Capital One Payment Methods → Plaid Payment Channels

| Capital One Payment Method | Plaid Payment Channel |
|----------------------------|----------------------|
| `debit_card` | `online` |
| `credit_card` | `online` |
| `bank_transfer` | `other` |
| `digital_wallet` | `online` |
| `cash` | `other` |

---

## Data Validation

### Schema Validation Functions

1. **`validate_account(account: Account) -> list[str]`**
   - Validates account structure and constraints
   - Returns list of validation errors (empty if valid)

2. **`validate_transaction(transaction: Transaction) -> list[str]`**
   - Validates transaction structure and constraints
   - Returns list of validation errors (empty if valid)

3. **`validate_credit_card_liability(liability: CreditCardLiability) -> list[str]`**
   - Validates credit card liability structure and constraints
   - Returns list of validation errors (empty if valid)

### Automatic Validation

All schema classes use `__post_init__` to automatically validate data:
- Invalid data raises `ValueError` with descriptive error messages
- Validation happens on object creation

---

## Usage Examples

### Creating an Account

```python
from ingest.schemas import Account, AccountType, AccountSubtype, AccountBalances, HolderCategory

account = Account(
    account_id="ACC-CUST000135-CHECKING-1",
    customer_id="CUST000135",
    type=AccountType.DEPOSITORY,
    subtype=AccountSubtype.CHECKING,
    balances=AccountBalances(
        available=6846.96,
        current=6846.96,
        limit=None
    ),
    iso_currency_code="USD",
    holder_category=HolderCategory.CONSUMER
)
```

### Creating a Transaction

```python
from ingest.schemas import (
    Transaction, PaymentChannel, PersonalFinanceCategory,
    PersonalFinanceCategoryPrimary, PersonalFinanceCategoryDetailed
)
from datetime import date

transaction = Transaction(
    transaction_id="TXN00000001",
    account_id="ACC-CUST000135-CHECKING-1",
    date=date(2024, 1, 1),
    amount=100.46,
    merchant_name="Groceries Store #159",
    merchant_entity_id="MERCH000159",
    payment_channel=PaymentChannel.ONLINE,
    personal_finance_category=PersonalFinanceCategory(
        primary=PersonalFinanceCategoryPrimary.GENERAL_MERCHANDISE,
        detailed=PersonalFinanceCategoryDetailed.GROCERIES
    ),
    pending=False,
    iso_currency_code="USD"
)
```

### Validating Data

```python
from ingest.schemas import validate_account, validate_transaction

# Validate account
errors = validate_account(account)
if errors:
    print(f"Account validation errors: {errors}")
else:
    print("Account is valid!")

# Validate transaction
errors = validate_transaction(transaction)
if errors:
    print(f"Transaction validation errors: {errors}")
else:
    print("Transaction is valid!")
```

---

## Next Steps

After schema definition (PR #2), we'll:
1. **PR #3:** Use these schemas to synthesize data from Capital One CSV
2. **PR #4:** Load synthesized data into SQLite database
3. **Feature Detection:** Use these schemas for behavioral signal detection

