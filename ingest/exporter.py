"""
Data export module for SpendSenseAI.

This module exports synthesized Plaid-compatible data to CSV/JSON format.
"""

import json
import pandas as pd
from typing import List
from datetime import date
from pathlib import Path

from .schemas import Account, Transaction, CreditCardLiability


def export_accounts_to_csv(accounts: List[Account], output_path: str) -> None:
    """
    Export accounts to CSV file.
    
    Args:
        accounts: List of Account objects
        output_path: Path to output CSV file
    """
    data = []
    
    for account in accounts:
        data.append({
            'account_id': account.account_id,
            'customer_id': account.customer_id,
            'type': account.type.value,
            'subtype': account.subtype.value,
            'balances_available': account.balances.available,
            'balances_current': account.balances.current,
            'balances_limit': account.balances.limit,
            'iso_currency_code': account.iso_currency_code,
            'holder_category': account.holder_category.value
        })
    
    df = pd.DataFrame(data)
    df.to_csv(output_path, index=False)


def export_transactions_to_csv(transactions: List[Transaction], output_path: str) -> None:
    """
    Export transactions to CSV file.
    
    Args:
        transactions: List of Transaction objects
        output_path: Path to output CSV file
    """
    data = []
    
    for transaction in transactions:
        data.append({
            'transaction_id': transaction.transaction_id,
            'account_id': transaction.account_id,
            'date': transaction.date.isoformat(),
            'amount': transaction.amount,
            'merchant_name': transaction.merchant_name,
            'merchant_entity_id': transaction.merchant_entity_id,
            'payment_channel': transaction.payment_channel.value,
            'personal_finance_category_primary': (
                transaction.personal_finance_category.primary.value
                if transaction.personal_finance_category else None
            ),
            'personal_finance_category_detailed': (
                transaction.personal_finance_category.detailed.value
                if transaction.personal_finance_category else None
            ),
            'pending': transaction.pending,
            'iso_currency_code': transaction.iso_currency_code
        })
    
    df = pd.DataFrame(data)
    df.to_csv(output_path, index=False)


def export_liabilities_to_csv(liabilities: List[CreditCardLiability], output_path: str) -> None:
    """
    Export liabilities to CSV file.
    
    Args:
        liabilities: List of CreditCardLiability objects
        output_path: Path to output CSV file
    """
    data = []
    
    for liability in liabilities:
        # Get primary APR (purchase APR)
        primary_apr = next(
            (apr for apr in liability.aprs if apr.type == "purchase"),
            liability.aprs[0] if liability.aprs else None
        )
        
        data.append({
            'account_id': liability.account_id,
            'apr_type': primary_apr.type if primary_apr else None,
            'apr_percentage': primary_apr.percentage if primary_apr else None,
            'minimum_payment_amount': liability.minimum_payment_amount,
            'last_payment_amount': liability.last_payment_amount,
            'is_overdue': liability.is_overdue,
            'next_payment_due_date': (
                liability.next_payment_due_date.isoformat()
                if liability.next_payment_due_date else None
            ),
            'last_statement_balance': liability.last_statement_balance
        })
    
    df = pd.DataFrame(data)
    df.to_csv(output_path, index=False)


def export_all_to_csv(
    accounts: List[Account],
    transactions: List[Transaction],
    liabilities: List[CreditCardLiability],
    output_dir: str
) -> None:
    """
    Export all synthesized data to CSV files.
    
    Args:
        accounts: List of Account objects
        transactions: List of Transaction objects
        liabilities: List of CreditCardLiability objects
        output_dir: Directory to save CSV files
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Export accounts
    export_accounts_to_csv(accounts, str(output_path / 'accounts.csv'))
    
    # Export transactions
    export_transactions_to_csv(transactions, str(output_path / 'transactions.csv'))
    
    # Export liabilities
    export_liabilities_to_csv(liabilities, str(output_path / 'liabilities.csv'))
    
    print(f"[SUCCESS] Exported {len(accounts)} accounts to {output_path / 'accounts.csv'}")
    print(f"[SUCCESS] Exported {len(transactions)} transactions to {output_path / 'transactions.csv'}")
    print(f"[SUCCESS] Exported {len(liabilities)} liabilities to {output_path / 'liabilities.csv'}")


def export_to_json(
    accounts: List[Account],
    transactions: List[Transaction],
    liabilities: List[CreditCardLiability],
    output_path: str
) -> None:
    """
    Export all synthesized data to JSON file.
    
    Args:
        accounts: List of Account objects
        transactions: List of Transaction objects
        liabilities: List of CreditCardLiability objects
        output_path: Path to output JSON file
    """
    def serialize_account(account: Account) -> dict:
        return {
            'account_id': account.account_id,
            'customer_id': account.customer_id,
            'type': account.type.value,
            'subtype': account.subtype.value,
            'balances': {
                'available': account.balances.available,
                'current': account.balances.current,
                'limit': account.balances.limit
            },
            'iso_currency_code': account.iso_currency_code,
            'holder_category': account.holder_category.value
        }
    
    def serialize_transaction(transaction: Transaction) -> dict:
        return {
            'transaction_id': transaction.transaction_id,
            'account_id': transaction.account_id,
            'date': transaction.date.isoformat(),
            'amount': transaction.amount,
            'merchant_name': transaction.merchant_name,
            'merchant_entity_id': transaction.merchant_entity_id,
            'payment_channel': transaction.payment_channel.value,
            'personal_finance_category': {
                'primary': (
                    transaction.personal_finance_category.primary.value
                    if transaction.personal_finance_category else None
                ),
                'detailed': (
                    transaction.personal_finance_category.detailed.value
                    if transaction.personal_finance_category else None
                )
            },
            'pending': transaction.pending,
            'iso_currency_code': transaction.iso_currency_code
        }
    
    def serialize_liability(liability: CreditCardLiability) -> dict:
        return {
            'account_id': liability.account_id,
            'aprs': [
                {'type': apr.type, 'percentage': apr.percentage}
                for apr in liability.aprs
            ],
            'minimum_payment_amount': liability.minimum_payment_amount,
            'last_payment_amount': liability.last_payment_amount,
            'is_overdue': liability.is_overdue,
            'next_payment_due_date': (
                liability.next_payment_due_date.isoformat()
                if liability.next_payment_due_date else None
            ),
            'last_statement_balance': liability.last_statement_balance
        }
    
    data = {
        'accounts': [serialize_account(acc) for acc in accounts],
        'transactions': [serialize_transaction(txn) for txn in transactions],
        'liabilities': [serialize_liability(liab) for liab in liabilities]
    }
    
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"[SUCCESS] Exported {len(accounts)} accounts, {len(transactions)} transactions, "
          f"{len(liabilities)} liabilities to {output_path}")

