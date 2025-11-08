"""
Shift transaction dates to be more recent (last 6 months) and recalculate
payment due dates so we have a realistic mix of overdue and current accounts.
"""

import sqlite3
from datetime import date, timedelta
from typing import Dict, List, Optional
import sys
import os

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.recalculate_overdue_status import recalculate_overdue_status

DB_PATH = "data/spendsense.db"


def shift_dates_to_recent(db_path: str, months_back: int = 6):
    """
    Shift all transaction dates to be within the last N months.
    This makes the data look more recent and creates a realistic mix of overdue/current accounts.
    
    Args:
        db_path: Path to database
        months_back: How many months back to shift dates (default: 6 months)
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    today = date.today()
    
    # Get date range of current transactions
    cursor.execute("SELECT MIN(date), MAX(date) FROM transactions")
    result = cursor.fetchone()
    min_date = date.fromisoformat(result[0]) if result[0] else date.today()
    max_date = date.fromisoformat(result[1]) if result[1] else date.today()
    
    print(f"Current transaction date range: {min_date} to {max_date}")
    
    # Calculate new date range (last N months)
    new_max_date = today
    new_min_date = today - timedelta(days=months_back * 30)
    
    print(f"New transaction date range: {new_min_date} to {new_max_date}")
    
    # Calculate shift amount
    old_range = (max_date - min_date).days
    new_range = (new_max_date - new_min_date).days
    
    if old_range == 0:
        print("⚠️  No date range in transactions, cannot shift")
        conn.close()
        return
    
    # Shift all transaction dates proportionally
    print("\nShifting transaction dates...")
    cursor.execute("SELECT transaction_id, date FROM transactions")
    transactions = cursor.fetchall()
    
    updated_count = 0
    for txn_id, old_date_str in transactions:
        old_date = date.fromisoformat(old_date_str)
        
        # Calculate position in old range (0.0 to 1.0)
        position = (old_date - min_date).days / old_range if old_range > 0 else 0.5
        
        # Map to new range
        days_from_min = int(position * new_range)
        new_date = new_min_date + timedelta(days=days_from_min)
        
        # Update transaction date
        cursor.execute("UPDATE transactions SET date = ? WHERE transaction_id = ?", 
                      (new_date.isoformat(), txn_id))
        updated_count += 1
    
    conn.commit()
    print(f"[OK] Updated {updated_count} transaction dates")
    
    # Now recalculate payment due dates based on new payment dates
    print("\nRecalculating payment due dates...")
    recalculate_payment_due_dates(db_path)
    
    # Recalculate overdue status
    print("\nRecalculating overdue status...")
    recalculate_overdue_status(db_path)
    
    # Show summary
    cursor.execute("""
        SELECT 
            COUNT(DISTINCT a.customer_id) as total_customers,
            SUM(CASE WHEN l.is_overdue = 1 THEN 1 ELSE 0 END) as overdue_customers
        FROM accounts a
        JOIN credit_card_liabilities l ON a.account_id = l.account_id
        WHERE a.type = 'credit'
    """)
    result = cursor.fetchone()
    total = result[0]
    overdue = result[1]
    
    print(f"\n{'='*70}")
    print(f"Summary after date shift:")
    print(f"  Total credit card customers: {total}")
    print(f"  Overdue customers: {overdue} ({overdue/total*100:.1f}%)")
    print(f"  Current customers: {total - overdue} ({(total-overdue)/total*100:.1f}%)")
    print(f"{'='*70}")
    
    conn.close()


def recalculate_payment_due_dates(db_path: str):
    """Recalculate payment due dates based on actual payment dates in transactions."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all credit card accounts with their payment history
    cursor.execute("""
        SELECT DISTINCT a.account_id, a.customer_id
        FROM accounts a
        WHERE a.type = 'credit'
    """)
    
    accounts = cursor.fetchall()
    updated_count = 0
    
    for account_id, customer_id in accounts:
        # Get last payment date (negative amounts = payments for credit cards)
        cursor.execute("""
            SELECT MAX(date) as last_payment_date
            FROM transactions
            WHERE account_id = ? AND amount < 0
        """, (account_id,))
        
        result = cursor.fetchone()
        last_payment_date_str = result[0] if result else None
        
        if last_payment_date_str:
            last_payment_date = date.fromisoformat(last_payment_date_str)
            # Next payment due date is 30 days after last payment
            # This may be in the past (overdue) or future (current) - both are valid
            next_due_date = last_payment_date + timedelta(days=30)
            
            # Update due date (don't force it to be in the future - overdue is valid)
            cursor.execute("""
                UPDATE credit_card_liabilities
                SET next_payment_due_date = ?
                WHERE account_id = ?
            """, (next_due_date.isoformat(), account_id))
            updated_count += 1
        else:
            # No payment history - use last transaction date + 30 days
            cursor.execute("""
                SELECT MAX(date) as last_txn_date
                FROM transactions
                WHERE account_id = ?
            """, (account_id,))
            
            result = cursor.fetchone()
            if result and result[0]:
                last_txn_date = date.fromisoformat(result[0])
                # Next payment due date is 30 days after last transaction
                # This may be in the past (overdue) or future (current) - both are valid
                next_due_date = last_txn_date + timedelta(days=30)
                
                cursor.execute("""
                    UPDATE credit_card_liabilities
                    SET next_payment_due_date = ?
                    WHERE account_id = ?
                """, (next_due_date.isoformat(), account_id))
                updated_count += 1
    
    conn.commit()
    print(f"[OK] Updated {updated_count} payment due dates")
    conn.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Shift transaction dates to be more recent")
    parser.add_argument(
        "--months",
        type=int,
        default=6,
        help="Number of months back to shift dates (default: 6)"
    )
    
    args = parser.parse_args()
    
    print("="*70)
    print("Shifting Transaction Dates to Recent")
    print("="*70)
    print(f"This will shift all transaction dates to the last {args.months} months")
    print("and recalculate payment due dates accordingly.")
    print()
    
    shift_dates_to_recent(DB_PATH, months_back=args.months)

