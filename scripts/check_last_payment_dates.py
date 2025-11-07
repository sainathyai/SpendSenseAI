"""Check last payment dates for credit card accounts."""

import sqlite3
from datetime import date

DB_PATH = "data/spendsense.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
today = date.today()

# Get last payment dates
cursor.execute("""
    SELECT 
        a.customer_id,
        (SELECT MAX(date) FROM transactions t 
         WHERE t.account_id = a.account_id AND t.amount > 0) as last_payment_date,
        l.next_payment_due_date,
        a.balances_current
    FROM accounts a
    JOIN credit_card_liabilities l ON a.account_id = l.account_id
    WHERE a.type = 'credit'
    ORDER BY last_payment_date DESC NULLS LAST
    LIMIT 15
""")

print("Last Payment Dates (most recent first):")
print("="*80)
for row in cursor.fetchall():
    customer_id, last_payment_str, due_date_str, balance = row
    last_payment = date.fromisoformat(last_payment_str) if last_payment_str else None
    due_date = date.fromisoformat(due_date_str) if due_date_str else None
    days_overdue = (today - due_date).days if due_date and today > due_date else 0
    
    print(f"Customer: {customer_id}")
    print(f"  Last Payment: {last_payment or 'None'}")
    print(f"  Due Date: {due_date}")
    print(f"  Days Overdue: {days_overdue}")
    print(f"  Balance: ${balance:.2f}")
    print()

# Get statistics
cursor.execute("""
    SELECT COUNT(*) 
    FROM accounts a
    WHERE a.type = 'credit' 
    AND NOT EXISTS (
        SELECT 1 FROM transactions t 
        WHERE t.account_id = a.account_id AND t.amount > 0
    )
""")
no_payment = cursor.fetchone()[0]

cursor.execute("""
    SELECT COUNT(*) 
    FROM accounts a
    WHERE a.type = 'credit'
""")
total = cursor.fetchone()[0]

cursor.execute("""
    SELECT 
        MIN(last_payment),
        MAX(last_payment)
    FROM (
        SELECT MAX(date) as last_payment
        FROM accounts a
        JOIN transactions t ON a.account_id = t.account_id
        WHERE a.type = 'credit' AND t.amount > 0
        GROUP BY a.account_id
    )
""")
dates = cursor.fetchone()

print("="*80)
print("Payment Statistics:")
print(f"  Total credit accounts: {total}")
print(f"  Accounts with no payment history: {no_payment}")
print(f"  Accounts with payment history: {total - no_payment}")
if dates[0]:
    print(f"  Earliest last payment: {dates[0]}")
    print(f"  Latest last payment: {dates[1]}")
print(f"  Today: {today}")

conn.close()


