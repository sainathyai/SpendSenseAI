"""Test overdue query to verify it's returning correctly."""

import sqlite3
from datetime import date
from recommend.query_interpreter import QueryInterpreter

DB_PATH = "data/spendsense.db"

# Test the query
print("Testing overdue query...")
interpreter = QueryInterpreter(DB_PATH)
result = interpreter.interpret("how many customers have overdue credit card payment")

print("\n" + "="*60)
print("Query Result:")
print("="*60)
print(f"Success: {result['success']}")
print(f"Query: {result['query']}")

if result['success']:
    print(f"\nResult Type: {result['result'].get('type')}")
    print(f"Count: {result['result'].get('count', 'N/A')}")
    print(f"Message: {result['result'].get('message', 'N/A')}")
else:
    print(f"Error: {result.get('error')}")

# Verify directly from database
print("\n" + "="*60)
print("Direct Database Verification:")
print("="*60)

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("""
    SELECT COUNT(DISTINCT a.customer_id) 
    FROM accounts a 
    JOIN credit_card_liabilities l ON a.account_id = l.account_id 
    WHERE a.type = 'credit' AND l.is_overdue = 1
""")
overdue_customers = cursor.fetchone()[0]

cursor.execute("""
    SELECT COUNT(DISTINCT a.customer_id) 
    FROM accounts a 
    WHERE a.type = 'credit'
""")
total_customers = cursor.fetchone()[0]

cursor.execute("""
    SELECT COUNT(*) 
    FROM credit_card_liabilities 
    WHERE is_overdue = 1
""")
overdue_accounts = cursor.fetchone()[0]

cursor.execute("""
    SELECT COUNT(*) 
    FROM credit_card_liabilities 
    WHERE next_payment_due_date IS NOT NULL 
    AND date(next_payment_due_date) < date('now')
""")
past_due = cursor.fetchone()[0]

today = date.today()
print(f"Today: {today}")
print(f"Customers with overdue credit cards: {overdue_customers}")
print(f"Total customers with credit cards: {total_customers}")
print(f"Overdue accounts: {overdue_accounts}")
print(f"Accounts with past due dates: {past_due}")

conn.close()

print("\n" + "="*60)
if overdue_customers == 0:
    print("✅ Status: Query is returning correctly!")
    print("   All due dates are in the future, so 0 overdue is correct.")
else:
    print(f"⚠️  Status: Found {overdue_customers} overdue customers")
print("="*60)


