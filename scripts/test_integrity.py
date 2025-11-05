"""Quick test of integrity check."""
from ingest.queries import check_data_integrity

integrity = check_data_integrity('data/spendsense.db')
print(f"Integrity Passed: {integrity['integrity_passed']}")
print(f"Integrity Score: {integrity['integrity_score']:.2%}")
print(f"Orphaned Transactions: {integrity['orphaned_transactions']}")
print(f"Orphaned Liabilities: {integrity['orphaned_liabilities']}")
print(f"Credit Cards Without Liabilities: {integrity['credit_cards_without_liabilities']}")
print(f"Accounts Without Transactions: {integrity['accounts_without_transactions']}")

