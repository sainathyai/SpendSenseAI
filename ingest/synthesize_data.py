"""
Script to synthesize Plaid-compatible data from Capital One CSV.

Usage:
    python -m ingest.synthesize_data <input_csv> <output_dir>
"""

import sys
import argparse
from pathlib import Path

from .synthesis import synthesize_data
from .exporter import export_all_to_csv, export_to_json


def main():
    """Main function to synthesize and export data."""
    parser = argparse.ArgumentParser(
        description='Synthesize Plaid-compatible data from Capital One CSV'
    )
    parser.add_argument(
        'input_csv',
        type=str,
        help='Path to input CSV file (Capital One transactions)'
    )
    parser.add_argument(
        'output_dir',
        type=str,
        help='Directory to save synthesized data (CSV and JSON)'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Also export to JSON format'
    )
    
    args = parser.parse_args()
    
    # Validate input file exists
    input_path = Path(args.input_csv)
    if not input_path.exists():
        print(f"[ERROR] Input file not found: {input_path}")
        sys.exit(1)
    
    # Create output directory
    output_path = Path(args.output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    print(f"[INFO] Starting data synthesis...")
    print(f"   Input: {input_path}")
    print(f"   Output: {output_path}")
    
    try:
        # Synthesize data
        accounts, transactions, liabilities = synthesize_data(str(input_path))
        
        print(f"\n[SUCCESS] Synthesis complete!")
        print(f"   Accounts: {len(accounts)}")
        print(f"   Transactions: {len(transactions)}")
        print(f"   Liabilities: {len(liabilities)}")
        
        # Export to CSV
        print(f"\n[INFO] Exporting to CSV...")
        export_all_to_csv(accounts, transactions, liabilities, str(output_path))
        
        # Export to JSON if requested
        if args.json:
            print(f"\n[INFO] Exporting to JSON...")
            json_path = output_path / 'plaid_data.json'
            export_to_json(accounts, transactions, liabilities, str(json_path))
        
        print(f"\n[SUCCESS] Data synthesis complete!")
        print(f"   Output directory: {output_path}")
        
    except Exception as e:
        print(f"\n[ERROR] Error during synthesis: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

