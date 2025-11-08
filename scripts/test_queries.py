"""Quick test of query utilities."""
from datetime import date, timedelta
from ingest.queries import (
    get_accounts_by_customer,
    get_transactions_by_customer,
    get_credit_card_liabilities_by_customer
)

db_path = 'data/spendsense.db'

# Test getting accounts for a customer
print("[TEST] Getting accounts for CUST000001...")
accounts = get_accounts_by_customer("CUST000001", db_path)
print(f"   Found {len(accounts)} accounts")
for acc in accounts:
    print(f"   - {acc.account_id}: {acc.type.value} / {acc.subtype.value}")

# Test getting transactions for a customer
print("\n[TEST] Getting transactions for CUST000001...")
transactions = get_transactions_by_customer("CUST000001", db_path)
print(f"   Found {len(transactions)} transactions")

# Test date filtering
print("\n[TEST] Getting transactions for last 30 days...")
start_date = date.today() - timedelta(days=30)
end_date = date.today()
recent_transactions = get_transactions_by_customer(
    "CUST000001", db_path,
    start_date=start_date,
    end_date=end_date
)
print(f"   Found {len(recent_transactions)} transactions in last 30 days")

# Test excluding pending
print("\n[TEST] Getting non-pending transactions...")
non_pending = get_transactions_by_customer(
    "CUST000001", db_path,
    exclude_pending=True
)
print(f"   Found {len(non_pending)} non-pending transactions")

# Test getting liabilities
print("\n[TEST] Getting credit card liabilities for CUST000001...")
liabilities = get_credit_card_liabilities_by_customer("CUST000001", db_path)
print(f"   Found {len(liabilities)} credit card liabilities")
for liab in liabilities:
    print(f"   - {liab.account_id}: APR {liab.aprs[0].percentage}%, Min Payment ${liab.minimum_payment_amount:.2f}")

print("\n[SUCCESS] All query tests passed!")

