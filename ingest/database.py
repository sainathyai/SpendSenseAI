"""
Database module for SpendSenseAI.

This module handles SQLite database setup, data loading, and query utilities
for accounts, transactions, and liabilities.
"""

import sqlite3
import json
from pathlib import Path
from typing import List, Optional, Dict, Tuple
from datetime import date, datetime
from contextlib import contextmanager

from .schemas import (
    Account, Transaction, CreditCardLiability, LoanLiability,
    AccountBalances, PersonalFinanceCategory
)


# ============================================================================
# Database Setup
# ============================================================================

def create_database(db_path: str) -> None:
    """
    Create SQLite database with all required tables.
    
    Args:
        db_path: Path to SQLite database file
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        
        # Create accounts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                account_id TEXT PRIMARY KEY,
                customer_id TEXT NOT NULL,
                type TEXT NOT NULL,
                subtype TEXT NOT NULL,
                balances_available REAL,
                balances_current REAL NOT NULL,
                balances_limit REAL,
                iso_currency_code TEXT NOT NULL DEFAULT 'USD',
                holder_category TEXT NOT NULL DEFAULT 'consumer',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create transactions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                transaction_id TEXT PRIMARY KEY,
                account_id TEXT NOT NULL,
                date DATE NOT NULL,
                amount REAL NOT NULL,
                merchant_name TEXT,
                merchant_entity_id TEXT,
                payment_channel TEXT NOT NULL DEFAULT 'online',
                personal_finance_category_primary TEXT,
                personal_finance_category_detailed TEXT,
                pending INTEGER NOT NULL DEFAULT 0,
                iso_currency_code TEXT NOT NULL DEFAULT 'USD',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (account_id) REFERENCES accounts(account_id)
            )
        """)
        
        # Create credit card liabilities table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS credit_card_liabilities (
                account_id TEXT PRIMARY KEY,
                apr_type TEXT NOT NULL,
                apr_percentage REAL NOT NULL,
                minimum_payment_amount REAL NOT NULL,
                last_payment_amount REAL,
                is_overdue INTEGER NOT NULL DEFAULT 0,
                next_payment_due_date DATE,
                last_statement_balance REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (account_id) REFERENCES accounts(account_id)
            )
        """)
        
        # Create loan liabilities table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS loan_liabilities (
                account_id TEXT PRIMARY KEY,
                interest_rate REAL NOT NULL,
                next_payment_due_date DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (account_id) REFERENCES accounts(account_id)
            )
        """)
        
        # Create indexes for performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_accounts_customer_id ON accounts(customer_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_account_id ON transactions(account_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_customer_id ON transactions(account_id, date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_pending ON transactions(pending)")
        
        conn.commit()


@contextmanager
def get_connection(db_path: str):
    """
    Get a database connection with proper context management.
    
    Args:
        db_path: Path to SQLite database file
        
    Yields:
        sqlite3.Connection: Database connection
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Enable column access by name
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ============================================================================
# Data Loading
# ============================================================================

def load_accounts(accounts: List[Account], db_path: str) -> int:
    """
    Load accounts into database.
    
    Args:
        accounts: List of Account objects
        db_path: Path to SQLite database file
        
    Returns:
        Number of accounts loaded
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        
        loaded = 0
        for account in accounts:
            try:
                cursor.execute("""
                    INSERT OR REPLACE INTO accounts (
                        account_id, customer_id, type, subtype,
                        balances_available, balances_current, balances_limit,
                        iso_currency_code, holder_category
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    account.account_id,
                    account.customer_id,
                    account.type.value,
                    account.subtype.value,
                    account.balances.available,
                    account.balances.current,
                    account.balances.limit,
                    account.iso_currency_code,
                    account.holder_category.value
                ))
                loaded += 1
            except sqlite3.Error as e:
                print(f"Error loading account {account.account_id}: {e}")
                raise
        
        conn.commit()
        return loaded


def load_transactions(transactions: List[Transaction], db_path: str) -> int:
    """
    Load transactions into database.
    
    Args:
        transactions: List of Transaction objects
        db_path: Path to SQLite database file
        
    Returns:
        Number of transactions loaded
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        
        loaded = 0
        for transaction in transactions:
            try:
                # Get category info
                category_primary = None
                category_detailed = None
                if transaction.personal_finance_category:
                    category_primary = transaction.personal_finance_category.primary.value
                    category_detailed = transaction.personal_finance_category.detailed.value
                
                cursor.execute("""
                    INSERT OR REPLACE INTO transactions (
                        transaction_id, account_id, date, amount,
                        merchant_name, merchant_entity_id, payment_channel,
                        personal_finance_category_primary,
                        personal_finance_category_detailed,
                        pending, iso_currency_code
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    transaction.transaction_id,
                    transaction.account_id,
                    transaction.date.isoformat(),
                    transaction.amount,
                    transaction.merchant_name,
                    transaction.merchant_entity_id,
                    transaction.payment_channel.value,
                    category_primary,
                    category_detailed,
                    1 if transaction.pending else 0,
                    transaction.iso_currency_code
                ))
                loaded += 1
            except sqlite3.Error as e:
                print(f"Error loading transaction {transaction.transaction_id}: {e}")
                raise
        
        conn.commit()
        return loaded


def load_credit_card_liabilities(liabilities: List[CreditCardLiability], db_path: str) -> int:
    """
    Load credit card liabilities into database.
    
    Args:
        liabilities: List of CreditCardLiability objects
        db_path: Path to SQLite database file
        
    Returns:
        Number of liabilities loaded
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        
        loaded = 0
        for liability in liabilities:
            try:
                # Get first APR (most credit cards have one primary APR)
                apr = liability.aprs[0] if liability.aprs else None
                if apr is None:
                    continue
                
                cursor.execute("""
                    INSERT OR REPLACE INTO credit_card_liabilities (
                        account_id, apr_type, apr_percentage,
                        minimum_payment_amount, last_payment_amount,
                        is_overdue, next_payment_due_date,
                        last_statement_balance
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    liability.account_id,
                    apr.type,
                    apr.percentage,
                    liability.minimum_payment_amount,
                    liability.last_payment_amount,
                    1 if liability.is_overdue else 0,
                    liability.next_payment_due_date.isoformat() if liability.next_payment_due_date else None,
                    liability.last_statement_balance
                ))
                loaded += 1
            except sqlite3.Error as e:
                print(f"Error loading liability {liability.account_id}: {e}")
                raise
        
        conn.commit()
        return loaded


def load_loan_liabilities(liabilities: List[LoanLiability], db_path: str) -> int:
    """
    Load loan liabilities into database.
    
    Args:
        liabilities: List of LoanLiability objects
        db_path: Path to SQLite database file
        
    Returns:
        Number of liabilities loaded
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        
        loaded = 0
        for liability in liabilities:
            try:
                cursor.execute("""
                    INSERT OR REPLACE INTO loan_liabilities (
                        account_id, interest_rate, next_payment_due_date
                    ) VALUES (?, ?, ?)
                """, (
                    liability.account_id,
                    liability.interest_rate,
                    liability.next_payment_due_date.isoformat() if liability.next_payment_due_date else None
                ))
                loaded += 1
            except sqlite3.Error as e:
                print(f"Error loading loan liability {liability.account_id}: {e}")
                raise
        
        conn.commit()
        return loaded


def load_from_csv(
    accounts_csv: str,
    transactions_csv: str,
    liabilities_csv: str,
    db_path: str
) -> Dict[str, int]:
    """
    Load data from CSV files into database.
    
    Args:
        accounts_csv: Path to accounts CSV file
        transactions_csv: Path to transactions CSV file
        liabilities_csv: Path to liabilities CSV file
        db_path: Path to SQLite database file
        
    Returns:
        Dictionary with counts of loaded records
    """
    import pandas as pd
    from .schemas import (
        Account, Transaction, CreditCardLiability,
        AccountType, AccountSubtype, HolderCategory,
        PaymentChannel, PersonalFinanceCategoryPrimary,
        PersonalFinanceCategoryDetailed
    )
    
    # Load accounts
    accounts_df = pd.read_csv(accounts_csv)
    accounts = []
    for _, row in accounts_df.iterrows():
        balances = AccountBalances(
            available=row.get('balances_available'),
            current=row['balances_current'],
            limit=row.get('balances_limit')
        )
        account = Account(
            account_id=row['account_id'],
            customer_id=row['customer_id'],
            type=AccountType(row['type']),
            subtype=AccountSubtype(row['subtype']),
            balances=balances,
            iso_currency_code=row.get('iso_currency_code', 'USD'),
            holder_category=HolderCategory(row.get('holder_category', 'consumer'))
        )
        accounts.append(account)
    
    # Load transactions
    transactions_df = pd.read_csv(transactions_csv)
    transactions = []
    for _, row in transactions_df.iterrows():
        category = None
        if pd.notna(row.get('personal_finance_category_primary')):
            category = PersonalFinanceCategory(
                primary=PersonalFinanceCategoryPrimary(row['personal_finance_category_primary']),
                detailed=PersonalFinanceCategoryDetailed(row['personal_finance_category_detailed'])
            )
        
        transaction = Transaction(
            transaction_id=row['transaction_id'],
            account_id=row['account_id'],
            date=pd.to_datetime(row['date']).date(),
            amount=float(row['amount']),
            merchant_name=row.get('merchant_name'),
            merchant_entity_id=row.get('merchant_entity_id'),
            payment_channel=PaymentChannel(row.get('payment_channel', 'online')),
            personal_finance_category=category,
            pending=bool(row.get('pending', False)),
            iso_currency_code=row.get('iso_currency_code', 'USD')
        )
        transactions.append(transaction)
    
    # Load liabilities
    liabilities_df = pd.read_csv(liabilities_csv)
    liabilities = []
    for _, row in liabilities_df.iterrows():
        from .schemas import CreditCardAPR
        
        apr = CreditCardAPR(
            type=row['apr_type'],
            percentage=float(row['apr_percentage'])
        )
        
        liability = CreditCardLiability(
            account_id=row['account_id'],
            aprs=[apr],
            minimum_payment_amount=float(row['minimum_payment_amount']),
            last_payment_amount=row.get('last_payment_amount'),
            is_overdue=bool(row.get('is_overdue', False)),
            next_payment_due_date=pd.to_datetime(row['next_payment_due_date']).date() if pd.notna(row.get('next_payment_due_date')) else None,
            last_statement_balance=row.get('last_statement_balance')
        )
        liabilities.append(liability)
    
    # Load into database
    accounts_count = load_accounts(accounts, db_path)
    transactions_count = load_transactions(transactions, db_path)
    liabilities_count = load_credit_card_liabilities(liabilities, db_path)
    
    return {
        'accounts': accounts_count,
        'transactions': transactions_count,
        'liabilities': liabilities_count
    }


def load_from_json(json_path: str, db_path: str) -> Dict[str, int]:
    """
    Load data from JSON file into database.
    
    Args:
        json_path: Path to JSON file
        db_path: Path to SQLite database file
        
    Returns:
        Dictionary with counts of loaded records
    """
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    from .schemas import (
        Account, Transaction, CreditCardLiability,
        AccountType, AccountSubtype, HolderCategory,
        PaymentChannel, PersonalFinanceCategoryPrimary,
        PersonalFinanceCategoryDetailed, AccountBalances,
        PersonalFinanceCategory, CreditCardAPR
    )
    
    # Load accounts
    accounts = []
    for acc_data in data['accounts']:
        balances = AccountBalances(
            available=acc_data['balances'].get('available'),
            current=acc_data['balances']['current'],
            limit=acc_data['balances'].get('limit')
        )
        account = Account(
            account_id=acc_data['account_id'],
            customer_id=acc_data['customer_id'],
            type=AccountType(acc_data['type']),
            subtype=AccountSubtype(acc_data['subtype']),
            balances=balances,
            iso_currency_code=acc_data.get('iso_currency_code', 'USD'),
            holder_category=HolderCategory(acc_data.get('holder_category', 'consumer'))
        )
        accounts.append(account)
    
    # Load transactions
    transactions = []
    for txn_data in data['transactions']:
        category = None
        if txn_data.get('personal_finance_category', {}).get('primary'):
            category = PersonalFinanceCategory(
                primary=PersonalFinanceCategoryPrimary(txn_data['personal_finance_category']['primary']),
                detailed=PersonalFinanceCategoryDetailed(txn_data['personal_finance_category']['detailed'])
            )
        
        transaction = Transaction(
            transaction_id=txn_data['transaction_id'],
            account_id=txn_data['account_id'],
            date=datetime.fromisoformat(txn_data['date']).date(),
            amount=float(txn_data['amount']),
            merchant_name=txn_data.get('merchant_name'),
            merchant_entity_id=txn_data.get('merchant_entity_id'),
            payment_channel=PaymentChannel(txn_data.get('payment_channel', 'online')),
            personal_finance_category=category,
            pending=bool(txn_data.get('pending', False)),
            iso_currency_code=txn_data.get('iso_currency_code', 'USD')
        )
        transactions.append(transaction)
    
    # Load liabilities
    liabilities = []
    for liab_data in data['liabilities']:
        aprs = [
            CreditCardAPR(type=apr['type'], percentage=apr['percentage'])
            for apr in liab_data['aprs']
        ]
        
        liability = CreditCardLiability(
            account_id=liab_data['account_id'],
            aprs=aprs,
            minimum_payment_amount=float(liab_data['minimum_payment_amount']),
            last_payment_amount=liab_data.get('last_payment_amount'),
            is_overdue=bool(liab_data.get('is_overdue', False)),
            next_payment_due_date=datetime.fromisoformat(liab_data['next_payment_due_date']).date() if liab_data.get('next_payment_due_date') else None,
            last_statement_balance=liab_data.get('last_statement_balance')
        )
        liabilities.append(liability)
    
    # Load into database
    accounts_count = load_accounts(accounts, db_path)
    transactions_count = load_transactions(transactions, db_path)
    liabilities_count = load_credit_card_liabilities(liabilities, db_path)
    
    return {
        'accounts': accounts_count,
        'transactions': transactions_count,
        'liabilities': liabilities_count
    }

