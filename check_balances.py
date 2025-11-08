#!/usr/bin/env python3
"""Check account balances for a customer."""
from ingest.queries import get_accounts_by_customer

customer_id = 'CUST000001'
accounts = get_accounts_by_customer(customer_id, 'data/spendsense.db')

print(f'Accounts for {customer_id}:\n')
print(f'{"Account Type":<20} {"Subtype":<20} {"Available":<15} {"Current":<15} {"Limit":<15}')
print('=' * 85)

total_available = 0
total_current = 0

for account in accounts:
    available = account.balances.available if account.balances.available else 0
    current = account.balances.current if account.balances.current else 0
    limit = account.balances.limit if account.balances.limit else 0
    
    print(f'{account.type.value:<20} {account.subtype.value:<20} ${available:>12,.2f} ${current:>12,.2f} ${limit:>12,.2f}')
    
    # Sum up totals (excluding credit accounts as they represent debt)
    if account.type.value != 'credit':
        total_available += available
        total_current += current

print('=' * 85)
print(f'{"Total (excl. credit)":<40} ${total_available:>12,.2f} ${total_current:>12,.2f}')

# Show credit card debt separately
credit_accounts = [a for a in accounts if a.type.value == 'credit']
if credit_accounts:
    print('\n' + '=' * 85)
    print('Credit Card Debt:')
    total_credit_debt = sum(a.balances.current for a in credit_accounts)
    total_credit_limit = sum(a.balances.limit for a in credit_accounts if a.balances.limit)
    print(f'Total debt: ${total_credit_debt:,.2f}')
    print(f'Total credit limit: ${total_credit_limit:,.2f}')
    if total_credit_limit > 0:
        utilization = (total_credit_debt / total_credit_limit) * 100
        print(f'Utilization: {utilization:.2f}%')

# Net worth calculation
net_worth = total_current - sum(a.balances.current for a in credit_accounts)
print('\n' + '=' * 85)
print(f'Net Worth (Assets - Debt): ${net_worth:,.2f}')

