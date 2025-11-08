"""
Grant consent to test customers
"""
import sys
import os
import sqlite3
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from guardrails.consent import grant_consent, ConsentScope, create_consent_tables

DB_PATH = "data/spendsense.db"

# Create tables if they don't exist
create_consent_tables(DB_PATH)

# Get all customers from the database
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
cursor.execute('SELECT DISTINCT customer_id FROM accounts ORDER BY customer_id')
customers = [row[0] for row in cursor.fetchall()]
conn.close()

print(f"Found {len(customers)} customers in the database")

for customer_id in customers:
    try:
        consent = grant_consent(
            customer_id, 
            DB_PATH, 
            scope=ConsentScope.ALL,
            notes="Test consent for demo"
        )
        print(f"✅ Granted consent to {customer_id}")
    except Exception as e:
        print(f"❌ Error granting consent to {customer_id}: {e}")

print(f"\n✅ Consent granted to {len(customers)} customers")


