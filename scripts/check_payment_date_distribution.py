"""Check distribution of last payment dates across customers."""

import sqlite3
from collections import Counter

DB_PATH = "data/spendsense.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Get last payment date for each customer
cursor.execute("""
    SELECT 
        a.customer_id,
        (SELECT MAX(date) 
         FROM transactions t 
         WHERE t.account_id = a.account_id AND t.amount < 0) as last_payment_date
    FROM accounts a
    WHERE a.type = 'credit'
    GROUP BY a.customer_id
""")

results = cursor.fetchall()
payment_dates = [r[1] for r in results if r[1]]

# Count distribution
date_counts = Counter(payment_dates)

print("Last Payment Date Distribution:")
print("="*70)
print(f"Total customers with payment history: {len(payment_dates)}")
print(f"Unique last payment dates: {len(date_counts)}")
print(f"\nTop 20 most common last payment dates:")
print("-"*70)

for date_str, count in sorted(date_counts.items(), key=lambda x: (x[1], x[0]), reverse=True)[:20]:
    percentage = (count / len(payment_dates)) * 100
    print(f"{date_str}: {count} customers ({percentage:.1f}%)")

# Get date range
cursor.execute("""
    SELECT 
        MIN((SELECT MAX(date) FROM transactions t WHERE t.account_id = a.account_id AND t.amount < 0)) as earliest,
        MAX((SELECT MAX(date) FROM transactions t WHERE t.account_id = a.account_id AND t.amount < 0)) as latest
    FROM accounts a
    WHERE a.type = 'credit'
""")
result = cursor.fetchone()
earliest = result[0]
latest = result[1]

print(f"\nDate Range:")
print(f"  Earliest last payment: {earliest}")
print(f"  Latest last payment: {latest}")

# Check if many customers share the same date
max_count = max(date_counts.values()) if date_counts else 0
if max_count > len(payment_dates) * 0.1:  # More than 10% share same date
    print(f"\n⚠️  WARNING: {max_count} customers share the same last payment date!")
    print(f"   This is {max_count/len(payment_dates)*100:.1f}% of all customers.")
else:
    print(f"\n✅ Payment dates are well distributed (max {max_count} customers per date)")

conn.close()


