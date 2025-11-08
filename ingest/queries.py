"""
Query utilities for SpendSenseAI database.

This module provides query functions for retrieving accounts, transactions,
and liabilities from the SQLite database.
"""

from typing import List, Optional, Dict, Any
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


def get_all_customers(db_path: str, limit: Optional[int] = None) -> List[str]:
    """
    Get all unique customer IDs from the database.
    
    Args:
        db_path: Path to SQLite database file
        limit: Optional limit on number of customers
        
    Returns:
        List of customer IDs
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        query = "SELECT DISTINCT customer_id FROM accounts ORDER BY customer_id"
        if limit:
            query += f" LIMIT {limit}"
        cursor.execute(query)
        return [row['customer_id'] for row in cursor.fetchall()]


def search_customers(db_path: str, query: str, limit: int = 10) -> List[str]:
    """
    Search for customers by ID (autocomplete/suggestions).
    
    Args:
        db_path: Path to SQLite database file
        query: Search query (partial customer ID)
        limit: Maximum number of results
        
    Returns:
        List of matching customer IDs
    """
    if not query:
        return []
    
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        search_pattern = f"%{query}%"
        cursor.execute("""
            SELECT DISTINCT customer_id 
            FROM accounts 
            WHERE customer_id LIKE ? 
            ORDER BY customer_id
            LIMIT ?
        """, (search_pattern, limit))
        return [row['customer_id'] for row in cursor.fetchall()]


def get_customer_summary(db_path: str, customer_id: str) -> Optional[Dict]:
    """
    Get summary information for a customer.
    
    Args:
        db_path: Path to SQLite database file
        customer_id: Customer ID
        
    Returns:
        Dictionary with customer summary (account count, transaction count, etc.)
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        
        # Get account count
        cursor.execute("SELECT COUNT(*) as count FROM accounts WHERE customer_id = ?", (customer_id,))
        account_count = cursor.fetchone()['count']
        
        # Get transaction count
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM transactions t
            JOIN accounts a ON t.account_id = a.account_id
            WHERE a.customer_id = ?
        """, (customer_id,))
        transaction_count = cursor.fetchone()['count']
        
        # Get total balance (assets - debts)
        # Depository accounts are assets (positive), credit accounts are debts (subtract)
        cursor.execute("""
            SELECT 
                COALESCE(SUM(CASE WHEN type = 'depository' THEN balances_current ELSE 0 END), 0) -
                COALESCE(SUM(CASE WHEN type = 'credit' THEN balances_current ELSE 0 END), 0) as total
            FROM accounts 
            WHERE customer_id = ?
        """, (customer_id,))
        total_balance = cursor.fetchone()['total'] or 0.0
        
        # Get account types
        cursor.execute("""
            SELECT type, COUNT(*) as count 
            FROM accounts 
            WHERE customer_id = ?
            GROUP BY type
        """, (customer_id,))
        account_types = {row['type']: row['count'] for row in cursor.fetchall()}
        
        return {
            'customer_id': customer_id,
            'account_count': account_count,
            'transaction_count': transaction_count,
            'total_balance': total_balance,
            'account_types': account_types
        }


def get_transactions_summary_by_category(
    customer_id: str,
    db_path: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> Dict[str, Any]:
    """
    Get transaction summary grouped by category for a customer.
    
    Args:
        customer_id: Customer ID
        db_path: Path to SQLite database file
        start_date: Optional start date
        end_date: Optional end date
        
    Returns:
        Dictionary with category summaries
    """
    transactions = get_transactions_by_customer(
        customer_id, db_path,
        start_date=start_date,
        end_date=end_date,
        exclude_pending=True
    )
    
    if not transactions:
        return {
            "total_transactions": 0,
            "total_amount": 0.0,
            "by_category": {},
            "by_primary_category": {}
        }
    
    # Group by category
    by_category = {}
    by_primary_category = {}
    
    total_amount = 0.0
    
    for transaction in transactions:
        category_primary = transaction.category.primary.value if transaction.category and transaction.category.primary else "OTHER"
        category_detailed = transaction.category.detailed.value if transaction.category and transaction.category.detailed else "OTHER"
        
        amount = abs(transaction.amount)
        total_amount += amount
        
        # Group by detailed category
        if category_detailed not in by_category:
            by_category[category_detailed] = {
                "count": 0,
                "total_amount": 0.0,
                "average_amount": 0.0,
                "transactions": []
            }
        by_category[category_detailed]["count"] += 1
        by_category[category_detailed]["total_amount"] += amount
        by_category[category_detailed]["transactions"].append({
            "date": transaction.date.isoformat(),
            "amount": amount,
            "merchant": transaction.merchant_name or "Unknown"
        })
        
        # Group by primary category
        if category_primary not in by_primary_category:
            by_primary_category[category_primary] = {
                "count": 0,
                "total_amount": 0.0
            }
        by_primary_category[category_primary]["count"] += 1
        by_primary_category[category_primary]["total_amount"] += amount
    
    # Calculate averages
    for cat in by_category.values():
        if cat["count"] > 0:
            cat["average_amount"] = cat["total_amount"] / cat["count"]
    
    return {
        "total_transactions": len(transactions),
        "total_amount": total_amount,
        "by_category": by_category,
        "by_primary_category": by_primary_category
    }


def get_all_customers_with_summary(db_path: str, limit: Optional[int] = None) -> List[Dict]:
    """
    Get all customers with summary information.
    
    Args:
        db_path: Path to SQLite database file
        limit: Optional limit on number of customers
        
    Returns:
        List of customer summary dictionaries
    """
    customers = get_all_customers(db_path, limit)
    summaries = []
    for customer_id in customers:
        summary = get_customer_summary(db_path, customer_id)
        if summary:
            summaries.append(summary)
    return summaries


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

