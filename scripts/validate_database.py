"""
Comprehensive database validation script.

Validates SQLite database completeness, integrity, and readiness
for behavioral signal detection.
"""

import sys
from pathlib import Path
from datetime import date, timedelta
from ingest.queries import (
    check_data_integrity,
    get_accounts_by_customer,
    get_transactions_by_customer,
    get_credit_card_liabilities_by_customer,
    get_connection
)


def validate_database(db_path: str) -> dict:
    """
    Comprehensive database validation.
    
    Returns:
        Dictionary with validation results
    """
    results = {
        'database_exists': False,
        'tables_exist': False,
        'data_counts': {},
        'integrity': {},
        'data_completeness': {},
        'date_ranges': {},
        'sample_queries': {},
        'validation_passed': False
    }
    
    db_path_obj = Path(db_path)
    
    # Check if database exists
    if not db_path_obj.exists():
        print(f"[ERROR] Database file not found: {db_path}")
        return results
    
    results['database_exists'] = True
    print(f"[INFO] Database found: {db_path}")
    
    # Check tables exist
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' 
            AND name IN ('accounts', 'transactions', 'credit_card_liabilities', 'loan_liabilities')
        """)
        tables = [row[0] for row in cursor.fetchall()]
        
        required_tables = ['accounts', 'transactions', 'credit_card_liabilities']
        missing_tables = [t for t in required_tables if t not in tables]
        
        if missing_tables:
            print(f"[ERROR] Missing tables: {missing_tables}")
            return results
        
        results['tables_exist'] = True
        print(f"[SUCCESS] All required tables exist: {tables}")
    
    # Count records
    print(f"\n[INFO] Counting records...")
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM accounts")
        account_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM transactions")
        transaction_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM credit_card_liabilities")
        liability_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM loan_liabilities")
        loan_count = cursor.fetchone()[0]
        
        results['data_counts'] = {
            'accounts': account_count,
            'transactions': transaction_count,
            'credit_card_liabilities': liability_count,
            'loan_liabilities': loan_count
        }
        
        print(f"   Accounts: {account_count}")
        print(f"   Transactions: {transaction_count}")
        print(f"   Credit Card Liabilities: {liability_count}")
        print(f"   Loan Liabilities: {loan_count}")
    
    # Check integrity
    print(f"\n[INFO] Running integrity checks...")
    integrity = check_data_integrity(db_path)
    results['integrity'] = integrity
    
    print(f"   Orphaned Transactions: {integrity['orphaned_transactions']}")
    print(f"   Orphaned Liabilities: {integrity['orphaned_liabilities']}")
    print(f"   Credit Cards Without Liabilities: {integrity['credit_cards_without_liabilities']}")
    print(f"   Accounts Without Transactions: {integrity['accounts_without_transactions']}")
    print(f"   Integrity Score: {integrity['integrity_score']:.2%}")
    print(f"   Integrity Passed: {'Yes' if integrity['integrity_passed'] else 'No'}")
    
    # Check data completeness
    print(f"\n[INFO] Checking data completeness...")
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        
        # Check for null required fields
        cursor.execute("""
            SELECT COUNT(*) FROM accounts 
            WHERE account_id IS NULL OR customer_id IS NULL OR type IS NULL
        """)
        null_accounts = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(*) FROM transactions 
            WHERE transaction_id IS NULL OR account_id IS NULL OR date IS NULL OR amount IS NULL
        """)
        null_transactions = cursor.fetchone()[0]
        
        # Check for unique customer IDs
        cursor.execute("SELECT COUNT(DISTINCT customer_id) FROM accounts")
        unique_customers = cursor.fetchone()[0]
        
        # Check transaction date coverage
        cursor.execute("SELECT MIN(date), MAX(date) FROM transactions")
        date_range = cursor.fetchone()
        min_date = date.fromisoformat(date_range[0]) if date_range[0] else None
        max_date = date.fromisoformat(date_range[1]) if date_range[1] else None
        
        results['data_completeness'] = {
            'null_accounts': null_accounts,
            'null_transactions': null_transactions,
            'unique_customers': unique_customers,
            'min_date': min_date.isoformat() if min_date else None,
            'max_date': max_date.isoformat() if max_date else None,
            'date_range_days': (max_date - min_date).days if (min_date and max_date) else None
        }
        
        print(f"   Null Account Fields: {null_accounts}")
        print(f"   Null Transaction Fields: {null_transactions}")
        print(f"   Unique Customers: {unique_customers}")
        print(f"   Transaction Date Range: {min_date} to {max_date}")
        if min_date and max_date:
            print(f"   Date Range: {(max_date - min_date).days} days")
    
    # Check date ranges for 30-day and 180-day windows
    print(f"\n[INFO] Checking date ranges for detection windows...")
    if min_date and max_date:
        today = date.today()
        
        # 30-day window
        start_30d = today - timedelta(days=30)
        with get_connection(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM transactions 
                WHERE date >= ? AND date <= ?
            """, (start_30d.isoformat(), today.isoformat()))
            transactions_30d = cursor.fetchone()[0]
        
        # 180-day window
        start_180d = today - timedelta(days=180)
        with get_connection(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM transactions 
                WHERE date >= ? AND date <= ?
            """, (start_180d.isoformat(), today.isoformat()))
            transactions_180d = cursor.fetchone()[0]
        
        results['date_ranges'] = {
            '30_day_transactions': transactions_30d,
            '180_day_transactions': transactions_180d,
            '30_day_start': start_30d.isoformat(),
            '180_day_start': start_180d.isoformat()
        }
        
        print(f"   30-day window ({start_30d} to {today}): {transactions_30d} transactions")
        print(f"   180-day window ({start_180d} to {today}): {transactions_180d} transactions")
    
    # Test sample queries
    print(f"\n[INFO] Testing sample queries...")
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        
        # Get a sample customer
        cursor.execute("SELECT DISTINCT customer_id FROM accounts LIMIT 1")
        sample_customer = cursor.fetchone()
        
        if sample_customer:
            customer_id = sample_customer[0]
            
            # Test account query
            accounts = get_accounts_by_customer(customer_id, db_path)
            
            # Test transaction query
            transactions = get_transactions_by_customer(customer_id, db_path)
            
            # Test date-filtered query
            start_date = date.today() - timedelta(days=30)
            end_date = date.today()
            filtered_transactions = get_transactions_by_customer(
                customer_id, db_path,
                start_date=start_date,
                end_date=end_date
            )
            
            # Test liability query
            liabilities = get_credit_card_liabilities_by_customer(customer_id, db_path)
            
            results['sample_queries'] = {
                'sample_customer': customer_id,
                'accounts_found': len(accounts),
                'transactions_found': len(transactions),
                'filtered_transactions_found': len(filtered_transactions),
                'liabilities_found': len(liabilities),
                'query_success': True
            }
            
            print(f"   Sample Customer: {customer_id}")
            print(f"   Accounts Found: {len(accounts)}")
            print(f"   Transactions Found: {len(transactions)}")
            print(f"   Filtered Transactions (30d): {len(filtered_transactions)}")
            print(f"   Liabilities Found: {len(liabilities)}")
        else:
            results['sample_queries'] = {'query_success': False}
            print(f"   [WARNING] No customers found for sample query")
    
    # Overall validation
    validation_passed = (
        results['database_exists'] and
        results['tables_exist'] and
        integrity['integrity_passed'] and
        null_accounts == 0 and
        null_transactions == 0 and
        results['data_counts']['accounts'] > 0 and
        results['data_counts']['transactions'] > 0
    )
    
    results['validation_passed'] = validation_passed
    
    return results


def print_summary(results: dict):
    """Print validation summary."""
    print(f"\n{'='*60}")
    print(f"Database Validation Summary")
    print(f"{'='*60}")
    
    print(f"\n[Database Status]")
    print(f"   Database Exists: {'Yes' if results['database_exists'] else 'No'}")
    print(f"   Tables Exist: {'Yes' if results['tables_exist'] else 'No'}")
    
    print(f"\n[Data Counts]")
    counts = results['data_counts']
    print(f"   Accounts: {counts.get('accounts', 0)}")
    print(f"   Transactions: {counts.get('transactions', 0)}")
    print(f"   Credit Card Liabilities: {counts.get('credit_card_liabilities', 0)}")
    print(f"   Loan Liabilities: {counts.get('loan_liabilities', 0)}")
    
    print(f"\n[Integrity]")
    integrity = results['integrity']
    print(f"   Score: {integrity.get('integrity_score', 0):.2%}")
    print(f"   Passed: {'Yes' if integrity.get('integrity_passed', False) else 'No'}")
    
    print(f"\n[Data Completeness]")
    completeness = results['data_completeness']
    print(f"   Unique Customers: {completeness.get('unique_customers', 0)}")
    print(f"   Date Range: {completeness.get('min_date', 'N/A')} to {completeness.get('max_date', 'N/A')}")
    if completeness.get('date_range_days'):
        print(f"   Range: {completeness['date_range_days']} days")
    
    print(f"\n[Detection Windows]")
    date_ranges = results['date_ranges']
    if date_ranges:
        print(f"   30-day window: {date_ranges.get('30_day_transactions', 0)} transactions")
        print(f"   180-day window: {date_ranges.get('180_day_transactions', 0)} transactions")
    
    print(f"\n[Overall Validation]")
    print(f"   Validation Passed: {'YES' if results['validation_passed'] else 'NO'}")
    
    if results['validation_passed']:
        print(f"\n[SUCCESS] Database is ready for behavioral signal detection!")
    else:
        print(f"\n[WARNING] Database validation failed. Review issues above.")
    
    print(f"{'='*60}")


def main():
    """Main function."""
    db_path = "data/spendsense.db"
    
    if not Path(db_path).exists():
        print(f"[ERROR] Database not found: {db_path}")
        print(f"Please run: python -m ingest.load_data data/processed data/spendsense.db")
        sys.exit(1)
    
    print("="*60)
    print("Database Validation")
    print("="*60)
    print()
    
    results = validate_database(db_path)
    print_summary(results)
    
    if not results['validation_passed']:
        sys.exit(1)


if __name__ == '__main__':
    main()

