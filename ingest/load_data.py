"""
CLI script to load synthesized data into SQLite database.

Usage:
    python -m ingest.load_data <data_dir> <db_path>
"""

import sys
import argparse
from pathlib import Path

from .database import create_database, load_from_csv, load_from_json
from .queries import check_data_integrity


def main():
    """Main function to load data into database."""
    parser = argparse.ArgumentParser(
        description='Load synthesized data into SQLite database'
    )
    parser.add_argument(
        'data_dir',
        type=str,
        help='Directory containing synthesized data (CSV files or JSON)'
    )
    parser.add_argument(
        'db_path',
        type=str,
        help='Path to SQLite database file (will be created if not exists)'
    )
    parser.add_argument(
        '--format',
        choices=['csv', 'json'],
        default='csv',
        help='Data format to load (default: csv)'
    )
    parser.add_argument(
        '--check-integrity',
        action='store_true',
        help='Run data integrity checks after loading'
    )
    
    args = parser.parse_args()
    
    data_path = Path(args.data_dir)
    db_path = Path(args.db_path)
    
    # Validate data directory exists
    if not data_path.exists():
        print(f"[ERROR] Data directory not found: {data_path}")
        sys.exit(1)
    
    # Create database directory if needed
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"[INFO] Creating database at {db_path}...")
    create_database(str(db_path))
    
    # Load data based on format
    if args.format == 'csv':
        accounts_csv = data_path / 'accounts.csv'
        transactions_csv = data_path / 'transactions.csv'
        liabilities_csv = data_path / 'liabilities.csv'
        
        # Validate CSV files exist
        missing_files = []
        if not accounts_csv.exists():
            missing_files.append('accounts.csv')
        if not transactions_csv.exists():
            missing_files.append('transactions.csv')
        if not liabilities_csv.exists():
            missing_files.append('liabilities.csv')
        
        if missing_files:
            print(f"[ERROR] Missing CSV files: {', '.join(missing_files)}")
            sys.exit(1)
        
        print(f"[INFO] Loading data from CSV files...")
        print(f"   Accounts: {accounts_csv}")
        print(f"   Transactions: {transactions_csv}")
        print(f"   Liabilities: {liabilities_csv}")
        
        try:
            counts = load_from_csv(
                str(accounts_csv),
                str(transactions_csv),
                str(liabilities_csv),
                str(db_path)
            )
            
            print(f"\n[SUCCESS] Data loaded successfully!")
            print(f"   Accounts: {counts['accounts']}")
            print(f"   Transactions: {counts['transactions']}")
            print(f"   Liabilities: {counts['liabilities']}")
            
        except Exception as e:
            print(f"\n[ERROR] Error loading data: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    
    elif args.format == 'json':
        json_path = data_path / 'plaid_data.json'
        
        if not json_path.exists():
            print(f"[ERROR] JSON file not found: {json_path}")
            sys.exit(1)
        
        print(f"[INFO] Loading data from JSON file: {json_path}")
        
        try:
            counts = load_from_json(str(json_path), str(db_path))
            
            print(f"\n[SUCCESS] Data loaded successfully!")
            print(f"   Accounts: {counts['accounts']}")
            print(f"   Transactions: {counts['transactions']}")
            print(f"   Liabilities: {counts['liabilities']}")
            
        except Exception as e:
            print(f"\n[ERROR] Error loading data: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    
    # Run integrity checks if requested
    if args.check_integrity:
        print(f"\n[INFO] Running data integrity checks...")
        try:
            integrity = check_data_integrity(str(db_path))
            
            print(f"\n[INFO] Integrity Check Results:")
            print(f"   Total Accounts: {integrity['total_accounts']}")
            print(f"   Total Transactions: {integrity['total_transactions']}")
            print(f"   Total Liabilities: {integrity['total_liabilities']}")
            print(f"   Orphaned Transactions: {integrity['orphaned_transactions']}")
            print(f"   Orphaned Liabilities: {integrity['orphaned_liabilities']}")
            print(f"   Accounts Without Transactions: {integrity['accounts_without_transactions']}")
            print(f"   Credit Cards Without Liabilities: {integrity['credit_cards_without_liabilities']}")
            print(f"   Integrity Score: {integrity['integrity_score']:.2%}")
            print(f"   Integrity Passed: {'Yes' if integrity['integrity_passed'] else 'No'}")
            
            if not integrity['integrity_passed']:
                print(f"\n[WARNING] Some integrity checks failed. Review the results above.")
                sys.exit(1)
            
        except Exception as e:
            print(f"\n[ERROR] Error running integrity checks: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    
    print(f"\n[SUCCESS] Database setup complete!")
    print(f"   Database: {db_path}")


if __name__ == '__main__':
    main()

