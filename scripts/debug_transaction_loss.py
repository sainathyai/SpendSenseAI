"""Debug script to find why transactions were lost."""
import pandas as pd
from ingest.synthesis import discover_accounts, create_account_lookup

# Load CSV
df = pd.read_csv('data/raw/transactions_formatted.csv')
df['date'] = pd.to_datetime(df['date'])

# Filter out cash
non_cash = df[df['payment_method'] != 'cash']
print(f"Non-cash transactions: {len(non_cash)}")

# Discover accounts
accounts_by_customer = discover_accounts(df)
all_accounts = [acc for accounts in accounts_by_customer.values() for acc in accounts]
print(f"Accounts discovered: {len(all_accounts)}")

# Create lookup
account_lookup = create_account_lookup(accounts_by_customer)
print(f"Account lookup entries: {len(account_lookup)}")

# Check which transactions can be mapped
mapped_count = 0
unmapped = []

for _, row in non_cash.iterrows():
    key = (row['customer_id'], row['payment_method'])
    if key in account_lookup:
        mapped_count += 1
    else:
        unmapped.append({
            'transaction_id': row['transaction_id'],
            'customer_id': row['customer_id'],
            'payment_method': row['payment_method'],
            'account_balance': row['account_balance']
        })

print(f"\nTransactions that can be mapped: {mapped_count}")
print(f"Transactions that CANNOT be mapped: {len(unmapped)}")

if unmapped:
    print(f"\nSample unmapped transactions:")
    unmapped_df = pd.DataFrame(unmapped[:10])
    print(unmapped_df)
    
    # Check payment method distribution of unmapped
    print(f"\nPayment method breakdown of unmapped:")
    print(pd.DataFrame(unmapped)['payment_method'].value_counts())

