"""
Fix payment due dates in credit_card_liabilities table.

The original synthesis used date.today() which was incorrect.
This script recalculates due dates based on last transaction dates.
"""

import sqlite3
from datetime import date, timedelta
from typing import Optional

DB_PATH = "data/spendsense.db"


def estimate_next_payment_due_date(
    last_payment_date: Optional[date],
    last_transaction_date: date
) -> date:
    """
    Estimate next payment due date based on payment history.
    
    Credit card payments are typically due monthly. If we have a payment date,
    the next payment is due approximately 30 days after that payment.
    
    Args:
        last_payment_date: Last payment date (if available)
        last_transaction_date: Last transaction date for the account
        
    Returns:
        Estimated next payment due date
    """
    # If we have a payment date, use it (most accurate)
    if last_payment_date:
        # Next payment is due 30 days after last payment
        next_due_date = last_payment_date + timedelta(days=30)
        return next_due_date
    
    # No payment history - estimate 30 days from last transaction
    # This is less accurate but better than nothing
    return last_transaction_date + timedelta(days=30)


def fix_due_dates(db_path: str):
    """Fix payment due dates for all credit card accounts."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all credit card accounts with their last transaction dates
    cursor.execute("""
        SELECT 
            a.account_id,
            MAX(t.date) as last_transaction_date
        FROM accounts a
        LEFT JOIN transactions t ON a.account_id = t.account_id
        WHERE a.type = 'credit'
        GROUP BY a.account_id
    """)
    
    accounts = cursor.fetchall()
    
    updated_count = 0
    
    for account_id, last_txn_str in accounts:
        if not last_txn_str:
            continue
        
        try:
            last_transaction_date = date.fromisoformat(last_txn_str)
        except:
            continue
        
        # Get last payment date from transactions (positive amounts = payments)
        cursor.execute("""
            SELECT MAX(date) as last_payment_date
            FROM transactions
            WHERE account_id = ? AND amount > 0
        """, (account_id,))
        
        result = cursor.fetchone()
        last_payment_date = None
        if result and result[0]:
            try:
                last_payment_date = date.fromisoformat(result[0])
            except:
                pass
        
        # Calculate new due date (use payment date if available, otherwise transaction date)
        new_due_date = estimate_next_payment_due_date(last_payment_date, last_transaction_date)
        
        # Update due date
        cursor.execute("""
            UPDATE credit_card_liabilities
            SET next_payment_due_date = ?
            WHERE account_id = ?
        """, (new_due_date.isoformat(), account_id))
        
        updated_count += 1
    
    conn.commit()
    
    # Recalculate overdue status
    print("Recalculating overdue status...")
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from scripts.recalculate_overdue_status import recalculate_overdue_status
    recalculate_overdue_status(db_path)
    
    conn.close()
    
    print(f"\nDue date fix complete!")
    print(f"Updated {updated_count} accounts")


if __name__ == "__main__":
    fix_due_dates(DB_PATH)

