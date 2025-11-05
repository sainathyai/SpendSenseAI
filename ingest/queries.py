"""
Query utilities for SpendSenseAI database.

This module provides query functions for retrieving accounts, transactions,
and liabilities from the SQLite database.
"""

from typing import List, Optional, Dict
from datetime import date
from contextlib import contextmanager
import sqlite3

from .schemas import (
    Account, Transaction, CreditCardLiability, LoanLiability,
    AccountType, AccountSubtype, HolderCategory, PaymentChannel,
    PersonalFinanceCategory, PersonalFinanceCategoryPrimary,
    PersonalFinanceCategoryDetailed, AccountBalances, CreditCardAPR
)


@contextmanager
def get_connection(db_path: str):
    """Get a database connection with proper context management."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_accounts_by_customer(customer_id: str, db_path: str) -> List[Account]:
    """
    Get all accounts for a customer.
    
    Args:
        customer_id: Customer ID
        db_path: Path to SQLite database file
        
    Returns:
        List of Account objects
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM accounts
            WHERE customer_id = ?
            ORDER BY type, subtype
        """, (customer_id,))
        
        accounts = []
        for row in cursor.fetchall():
            balances = AccountBalances(
                available=row['balances_available'],
                current=row['balances_current'],
                limit=row['balances_limit']
            )
            account = Account(
                account_id=row['account_id'],
                customer_id=row['customer_id'],
                type=AccountType(row['type']),
                subtype=AccountSubtype(row['subtype']),
                balances=balances,
                iso_currency_code=row['iso_currency_code'],
                holder_category=HolderCategory(row['holder_category'])
            )
            accounts.append(account)
        
        return accounts


def get_transactions_by_account(
    account_id: str,
    db_path: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    exclude_pending: bool = False
) -> List[Transaction]:
    """
    Get transactions for an account with optional date range and pending filter.
    
    Args:
        account_id: Account ID
        db_path: Path to SQLite database file
        start_date: Start date for filtering (inclusive)
        end_date: End date for filtering (inclusive)
        exclude_pending: If True, exclude pending transactions
        
    Returns:
        List of Transaction objects
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        
        query = "SELECT * FROM transactions WHERE account_id = ?"
        params = [account_id]
        
        if start_date:
            query += " AND date >= ?"
            params.append(start_date.isoformat())
        
        if end_date:
            query += " AND date <= ?"
            params.append(end_date.isoformat())
        
        if exclude_pending:
            query += " AND pending = 0"
        
        query += " ORDER BY date DESC, transaction_id"
        
        cursor.execute(query, params)
        
        transactions = []
        for row in cursor.fetchall():
            category = None
            if row['personal_finance_category_primary']:
                category = PersonalFinanceCategory(
                    primary=PersonalFinanceCategoryPrimary(row['personal_finance_category_primary']),
                    detailed=PersonalFinanceCategoryDetailed(row['personal_finance_category_detailed'])
                )
            
            transaction = Transaction(
                transaction_id=row['transaction_id'],
                account_id=row['account_id'],
                date=date.fromisoformat(row['date']),
                amount=row['amount'],
                merchant_name=row['merchant_name'],
                merchant_entity_id=row['merchant_entity_id'],
                payment_channel=PaymentChannel(row['payment_channel']),
                personal_finance_category=category,
                pending=bool(row['pending']),
                iso_currency_code=row['iso_currency_code']
            )
            transactions.append(transaction)
        
        return transactions


def get_transactions_by_customer(
    customer_id: str,
    db_path: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    exclude_pending: bool = False
) -> List[Transaction]:
    """
    Get all transactions for a customer across all accounts.
    
    Args:
        customer_id: Customer ID
        db_path: Path to SQLite database file
        start_date: Start date for filtering (inclusive)
        end_date: End date for filtering (inclusive)
        exclude_pending: If True, exclude pending transactions
        
    Returns:
        List of Transaction objects
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        
        query = """
            SELECT t.* FROM transactions t
            JOIN accounts a ON t.account_id = a.account_id
            WHERE a.customer_id = ?
        """
        params = [customer_id]
        
        if start_date:
            query += " AND t.date >= ?"
            params.append(start_date.isoformat())
        
        if end_date:
            query += " AND t.date <= ?"
            params.append(end_date.isoformat())
        
        if exclude_pending:
            query += " AND t.pending = 0"
        
        query += " ORDER BY t.date DESC, t.transaction_id"
        
        cursor.execute(query, params)
        
        transactions = []
        for row in cursor.fetchall():
            category = None
            if row['personal_finance_category_primary']:
                category = PersonalFinanceCategory(
                    primary=PersonalFinanceCategoryPrimary(row['personal_finance_category_primary']),
                    detailed=PersonalFinanceCategoryDetailed(row['personal_finance_category_detailed'])
                )
            
            transaction = Transaction(
                transaction_id=row['transaction_id'],
                account_id=row['account_id'],
                date=date.fromisoformat(row['date']),
                amount=row['amount'],
                merchant_name=row['merchant_name'],
                merchant_entity_id=row['merchant_entity_id'],
                payment_channel=PaymentChannel(row['payment_channel']),
                personal_finance_category=category,
                pending=bool(row['pending']),
                iso_currency_code=row['iso_currency_code']
            )
            transactions.append(transaction)
        
        return transactions


def get_credit_card_liabilities_by_customer(
    customer_id: str,
    db_path: str
) -> List[CreditCardLiability]:
    """
    Get all credit card liabilities for a customer.
    
    Args:
        customer_id: Customer ID
        db_path: Path to SQLite database file
        
    Returns:
        List of CreditCardLiability objects
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT l.* FROM credit_card_liabilities l
            JOIN accounts a ON l.account_id = a.account_id
            WHERE a.customer_id = ?
        """, (customer_id,))
        
        liabilities = []
        for row in cursor.fetchall():
            apr = CreditCardAPR(
                type=row['apr_type'],
                percentage=row['apr_percentage']
            )
            
            liability = CreditCardLiability(
                account_id=row['account_id'],
                aprs=[apr],
                minimum_payment_amount=row['minimum_payment_amount'],
                last_payment_amount=row['last_payment_amount'],
                is_overdue=bool(row['is_overdue']),
                next_payment_due_date=date.fromisoformat(row['next_payment_due_date']) if row['next_payment_due_date'] else None,
                last_statement_balance=row['last_statement_balance']
            )
            liabilities.append(liability)
        
        return liabilities


def get_loan_liabilities_by_customer(
    customer_id: str,
    db_path: str
) -> List[LoanLiability]:
    """
    Get all loan liabilities for a customer.
    
    Args:
        customer_id: Customer ID
        db_path: Path to SQLite database file
        
    Returns:
        List of LoanLiability objects
    """
    from .schemas import LoanLiability
    
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT l.* FROM loan_liabilities l
            JOIN accounts a ON l.account_id = a.account_id
            WHERE a.customer_id = ?
        """, (customer_id,))
        
        liabilities = []
        for row in cursor.fetchall():
            liability = LoanLiability(
                account_id=row['account_id'],
                interest_rate=row['interest_rate'],
                next_payment_due_date=date.fromisoformat(row['next_payment_due_date']) if row['next_payment_due_date'] else None
            )
            liabilities.append(liability)
        
        return liabilities


def check_data_integrity(db_path: str) -> Dict[str, any]:
    """
    Check data integrity and return report.
    
    Args:
        db_path: Path to SQLite database file
        
    Returns:
        Dictionary with integrity check results
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        
        results = {
            'orphaned_transactions': 0,
            'orphaned_liabilities': 0,
            'accounts_without_transactions': 0,
            'credit_cards_without_liabilities': 0,
            'total_accounts': 0,
            'total_transactions': 0,
            'total_liabilities': 0
        }
        
        # Count total records
        cursor.execute("SELECT COUNT(*) FROM accounts")
        results['total_accounts'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM transactions")
        results['total_transactions'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM credit_card_liabilities")
        results['total_liabilities'] = cursor.fetchone()[0]
        
        # Check for orphaned transactions
        cursor.execute("""
            SELECT COUNT(*) FROM transactions t
            LEFT JOIN accounts a ON t.account_id = a.account_id
            WHERE a.account_id IS NULL
        """)
        results['orphaned_transactions'] = cursor.fetchone()[0]
        
        # Check for orphaned liabilities
        cursor.execute("""
            SELECT COUNT(*) FROM credit_card_liabilities l
            LEFT JOIN accounts a ON l.account_id = a.account_id
            WHERE a.account_id IS NULL
        """)
        results['orphaned_liabilities'] = cursor.fetchone()[0]
        
        # Check for accounts without transactions
        cursor.execute("""
            SELECT COUNT(*) FROM accounts a
            LEFT JOIN transactions t ON a.account_id = t.account_id
            WHERE t.transaction_id IS NULL
        """)
        results['accounts_without_transactions'] = cursor.fetchone()[0]
        
        # Check for credit cards without liabilities
        cursor.execute("""
            SELECT COUNT(*) FROM accounts a
            LEFT JOIN credit_card_liabilities l ON a.account_id = l.account_id
            WHERE a.type = 'credit' AND l.account_id IS NULL
        """)
        results['credit_cards_without_liabilities'] = cursor.fetchone()[0]
        
        # Calculate integrity score
        # Critical checks: orphaned records and credit cards without liabilities
        # Accounts without transactions are acceptable (new accounts, inactive accounts)
        critical_checks = 3
        passed_critical = sum([
            results['orphaned_transactions'] == 0,
            results['orphaned_liabilities'] == 0,
            results['credit_cards_without_liabilities'] == 0
        ])
        results['integrity_score'] = passed_critical / critical_checks if critical_checks > 0 else 1.0
        results['integrity_passed'] = passed_critical == critical_checks
        
        return results

