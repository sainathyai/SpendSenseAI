#!/usr/bin/env python3
"""Test the fixed balance calculation."""
from ingest.queries import get_customer_summary

customer_id = 'CUST000001'
summary = get_customer_summary('data/spendsense.db', customer_id)

print(f'Customer Summary for {customer_id}:')
print(f'  Account count: {summary["account_count"]}')
print(f'  Transaction count: {summary["transaction_count"]}')
print(f'  Total balance (net worth): ${summary["total_balance"]:,.2f}')
print(f'  Account types: {summary["account_types"]}')

print('\nExpected: $5,590.86 (depository: $7,439.78 - credit: $1,848.92)')

