"""
Validation script to check CSV structure and test synthesis.

This script validates the CSV structure and provides a test run of the synthesis.
"""

import sys
import pandas as pd
from pathlib import Path

def validate_csv_structure(csv_path: str) -> bool:
    """
    Validate that CSV has all required columns.
    
    Args:
        csv_path: Path to CSV file
        
    Returns:
        True if valid, False otherwise
    """
    print(f"🔍 Validating CSV structure: {csv_path}")
    
    try:
        df = pd.read_csv(csv_path)
        
        # Required columns for synthesis
        required_columns = [
            'transaction_id',
            'customer_id',
            'merchant_id',
            'merchant_category',
            'payment_method',
            'amount',
            'account_balance',
            'status',
            'date'
        ]
        
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            print(f"[ERROR] Missing required columns: {missing_columns}")
            return False
        
        print(f"[SUCCESS] All required columns present")
        print(f"   Total rows: {len(df)}")
        print(f"   Total columns: {len(df.columns)}")
        
        # Check data types
        print(f"\n[INFO] Data Summary:")
        print(f"   Unique customers: {df['customer_id'].nunique()}")
        print(f"   Unique merchants: {df['merchant_id'].nunique()}")
        print(f"   Date range: {df['date'].min()} to {df['date'].max()}")
        print(f"   Payment methods: {df['payment_method'].unique().tolist()}")
        print(f"   Transaction types: {df['transaction_type'].unique().tolist()}")
        
        # Check for credit cards
        credit_card_count = len(df[df['payment_method'] == 'credit_card'])
        debit_card_count = len(df[df['payment_method'] == 'debit_card'])
        
        print(f"\n[INFO] Payment Method Distribution:")
        print(f"   Credit cards: {credit_card_count}")
        print(f"   Debit cards: {debit_card_count}")
        print(f"   Other: {len(df) - credit_card_count - debit_card_count}")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Error validating CSV: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_synthesis_sample(csv_path: str, sample_size: int = 100) -> bool:
    """
    Test synthesis on a sample of data.
    
    Args:
        csv_path: Path to CSV file
        sample_size: Number of rows to sample
        
    Returns:
        True if successful, False otherwise
    """
    print(f"\n[TEST] Testing synthesis on sample data ({sample_size} rows)...")
    
    try:
        # Import synthesis module
        from ingest.synthesis import synthesize_data
        
        # Create sample CSV
        df = pd.read_csv(csv_path)
        sample_df = df.head(sample_size)
        
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            sample_df.to_csv(f.name, index=False)
            temp_path = f.name
        
        try:
            # Run synthesis
            accounts, transactions, liabilities = synthesize_data(temp_path)
            
            print(f"[SUCCESS] Synthesis successful!")
            print(f"   Accounts created: {len(accounts)}")
            print(f"   Transactions processed: {len(transactions)}")
            print(f"   Liabilities created: {len(liabilities)}")
            
            # Show sample account
            if accounts:
                print(f"\n[SAMPLE] Sample Account:")
                acc = accounts[0]
                print(f"   Account ID: {acc.account_id}")
                print(f"   Customer ID: {acc.customer_id}")
                print(f"   Type: {acc.type.value}")
                print(f"   Subtype: {acc.subtype.value}")
                print(f"   Current Balance: ${acc.balances.current:.2f}")
                if acc.balances.limit:
                    print(f"   Credit Limit: ${acc.balances.limit:.2f}")
            
            # Show sample transaction
            if transactions:
                print(f"\n[SAMPLE] Sample Transaction:")
                txn = transactions[0]
                print(f"   Transaction ID: {txn.transaction_id}")
                print(f"   Account ID: {txn.account_id}")
                print(f"   Amount: ${txn.amount:.2f}")
                print(f"   Merchant: {txn.merchant_name}")
                print(f"   Category: {txn.personal_finance_category.primary.value if txn.personal_finance_category else 'N/A'}")
                print(f"   Payment Channel: {txn.payment_channel.value}")
            
            # Show sample liability
            if liabilities:
                print(f"\n[SAMPLE] Sample Liability:")
                liab = liabilities[0]
                print(f"   Account ID: {liab.account_id}")
                print(f"   APR: {liab.aprs[0].percentage}%")
                print(f"   Minimum Payment: ${liab.minimum_payment_amount:.2f}")
                print(f"   Overdue: {liab.is_overdue}")
            
            return True
            
        finally:
            import os
            os.unlink(temp_path)
            
    except Exception as e:
        print(f"[ERROR] Error during synthesis test: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main function."""
    csv_path = "data/raw/transactions_formatted.csv"
    
    if not Path(csv_path).exists():
        print(f"[ERROR] CSV file not found: {csv_path}")
        sys.exit(1)
    
    print("=" * 60)
    print("Data Synthesis Validation & Test")
    print("=" * 60)
    
    # Validate CSV structure
    if not validate_csv_structure(csv_path):
        print("\n[ERROR] CSV validation failed. Please check the file structure.")
        sys.exit(1)
    
    # Test synthesis on sample
    print("\n" + "=" * 60)
    if not test_synthesis_sample(csv_path, sample_size=100):
        print("\n[ERROR] Synthesis test failed. Please check the errors above.")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("[SUCCESS] All validations passed!")
    print("\nTo run full synthesis:")
    print(f"  python -m ingest.synthesize_data {csv_path} data/processed --json")
    print("=" * 60)


if __name__ == '__main__':
    main()

