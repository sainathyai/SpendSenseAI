"""Quick script to check transaction counts."""
import pandas as pd

df = pd.read_csv('data/raw/transactions_formatted.csv')

print(f"Total transactions in CSV: {len(df)}")
print(f"\nPayment method breakdown:")
print(df['payment_method'].value_counts())
print(f"\nCash transactions: {len(df[df['payment_method'] == 'cash'])}")
print(f"Non-cash transactions: {len(df[df['payment_method'] != 'cash'])}")

# Check status breakdown
print(f"\nStatus breakdown:")
print(df['status'].value_counts())

# Check for any other exclusions
print(f"\nTotal that should be processed: {len(df[df['payment_method'] != 'cash'])}")

