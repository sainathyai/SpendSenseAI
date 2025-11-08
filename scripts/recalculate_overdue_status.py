"""
Recalculate overdue status for existing credit card accounts.

This script updates the is_overdue flag in credit_card_liabilities
based on the corrected logic that uses payment due dates.
"""

import sqlite3
from datetime import date
from typing import Optional

DB_PATH = "data/spendsense.db"


def determine_overdue_status(
    payment_history: list,
    current_balance: float,
    next_payment_due_date: Optional[date] = None,
    last_payment_date: Optional[date] = None
) -> bool:
    """
    Determine if credit card account is overdue using corrected logic.
    
    Account is overdue if:
    - Balance > 0
    - Payment due date has passed
    - No payment made after the due date
    """
    if current_balance <= 0:
        return False  # No balance, not overdue
    
    # If we have a due date, use it (most accurate)
    if next_payment_due_date:
        today = date.today()
        if today > next_payment_due_date:
            # Due date has passed - check if payment was made after due date
            if last_payment_date and last_payment_date > next_payment_due_date:
                return False  # Payment made after due date, not overdue
            # Due date passed and no payment (or payment before due date) = overdue
            return True
        else:
            # Due date hasn't passed yet, not overdue
            return False
    
    # Fallback: If no due date, use payment history heuristic
    if not last_payment_date:
        # No payment history and no due date - can't determine, assume not overdue
        return False
    
    # Get days since last payment
    days_since_payment = (date.today() - last_payment_date).days
    
    # Only mark overdue if no payment in 60+ days (more conservative)
    return days_since_payment > 60


def recalculate_overdue_status(db_path: str):
    """Recalculate overdue status for all credit card accounts."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all credit card liabilities with account info
    cursor.execute("""
        SELECT 
            l.account_id,
            a.balances_current,
            l.next_payment_due_date,
            l.last_payment_amount,
            l.is_overdue as current_overdue
        FROM credit_card_liabilities l
        JOIN accounts a ON l.account_id = a.account_id
        WHERE a.type = 'credit'
    """)
    
    accounts = cursor.fetchall()
    
    updated_count = 0
    overdue_count = 0
    
    for account_id, balance, due_date_str, last_payment_amount, current_overdue in accounts:
        # Parse due date
        next_payment_due_date = None
        if due_date_str:
            try:
                next_payment_due_date = date.fromisoformat(due_date_str)
            except:
                pass
        
        # Get last payment date from transactions (if available)
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
        
        # Determine overdue status
        is_overdue = determine_overdue_status(
            payment_history=[],  # Not used in new logic
            current_balance=balance or 0.0,
            next_payment_due_date=next_payment_due_date,
            last_payment_date=last_payment_date
        )
        
        # Update if changed
        if is_overdue != bool(current_overdue):
            cursor.execute("""
                UPDATE credit_card_liabilities
                SET is_overdue = ?
                WHERE account_id = ?
            """, (1 if is_overdue else 0, account_id))
            updated_count += 1
        
        if is_overdue:
            overdue_count += 1
    
    conn.commit()
    conn.close()
    
    print(f"Recalculation complete!")
    print(f"Updated {updated_count} accounts")
    print(f"Total overdue accounts: {overdue_count}")
    print(f"Total accounts checked: {len(accounts)}")


if __name__ == "__main__":
    recalculate_overdue_status(DB_PATH)


