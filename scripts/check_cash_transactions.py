"""Check cash transactions data."""
import pandas as pd

df = pd.read_csv('data/raw/transactions_formatted.csv')
cash = df[df['payment_method'] == 'cash']

print(f"Total cash transactions: {len(cash)}")
print(f"\nSample cash transactions:")
print(cash[['transaction_id', 'customer_id', 'date', 'amount', 'merchant_category', 'account_balance', 'transaction_type']].head(10))

print(f"\nAccount balance info available: {cash['account_balance'].notna().sum()} / {len(cash)}")
print(f"Account balance stats:")
print(cash['account_balance'].describe())

print(f"\nTransaction types for cash:")
print(cash['transaction_type'].value_counts())

print(f"\nMerchant categories for cash:")
print(cash['merchant_category'].value_counts())

print(f"\nUnique customers with cash transactions: {cash['customer_id'].nunique()}")

