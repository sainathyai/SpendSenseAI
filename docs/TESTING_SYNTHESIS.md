# Testing Data Synthesis

## Quick Start

### Prerequisites
1. Python 3.9+ installed
2. Dependencies installed: `pip install -r requirements.txt`
3. CSV file at `data/raw/transactions_formatted.csv`

### Step 1: Validate CSV Structure

```bash
python scripts/validate_and_test_synthesis.py
```

This will:
- ✅ Validate CSV has all required columns
- ✅ Check data types and structure
- ✅ Test synthesis on a 100-row sample
- ✅ Show sample output (accounts, transactions, liabilities)

### Step 2: Run Full Synthesis

```bash
python -m ingest.synthesize_data data/raw/transactions_formatted.csv data/processed --json
```

This will:
- 🔄 Synthesize all accounts from transactions
- 🔄 Enhance all transactions with Plaid format
- 🔄 Generate all credit card liabilities
- 📝 Export to CSV files in `data/processed/`
- 📝 Export to JSON file (if `--json` flag used)

### Step 3: Check Output

After synthesis, you'll have:

**CSV Files:**
- `data/processed/accounts.csv` - All synthesized accounts
- `data/processed/transactions.csv` - All enhanced transactions
- `data/processed/liabilities.csv` - All credit card liabilities

**JSON File (if --json used):**
- `data/processed/plaid_data.json` - Complete data in JSON format

## Expected Output

### Sample Account
```
Account ID: ACC-CUST000135-CHECKING-1
Customer ID: CUST000135
Type: depository
Subtype: checking
Current Balance: $6846.96
Credit Limit: None
```

### Sample Transaction
```
Transaction ID: TXN00000001
Account ID: ACC-CUST000135-CHECKING-1
Amount: $100.46
Merchant: Whole Foods #159
Category: GENERAL_MERCHANDISE (GROCERIES)
Payment Channel: online
Pending: False
```

### Sample Liability
```
Account ID: ACC-CUST000036-CREDIT-1
APR: 18.99%
Minimum Payment: $111.00
Overdue: False
Next Payment Due: 2024-02-15
```

## Validation Checks

The synthesis automatically validates:
- ✅ All accounts have valid account_id
- ✅ All transactions have account_id
- ✅ Credit cards have limits
- ✅ Credit limits >= current balance
- ✅ APRs are realistic (15-30%)
- ✅ Minimum payments are > 0
- ✅ All dates are valid

## Troubleshooting

### Error: "Python was not found"
**Solution:** Install Python or activate virtual environment
```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\Activate.ps1

# Activate (Mac/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Error: "Module not found: ingest"
**Solution:** Make sure you're in the project root directory
```bash
cd SpendSenseAI
python -m ingest.synthesize_data ...
```

### Error: "CSV file not found"
**Solution:** Check CSV file path
```bash
# Verify file exists
ls data/raw/transactions_formatted.csv

# Or use absolute path
python -m ingest.synthesize_data "C:/path/to/transactions_formatted.csv" data/processed
```

### Error: "Missing required columns"
**Solution:** Check CSV has all required columns:
- transaction_id
- customer_id
- merchant_id
- merchant_category
- payment_method
- amount
- account_balance
- status
- date

## Running Tests

```bash
# Run all synthesis tests
pytest tests/test_synthesis.py -v

# Run specific test
pytest tests/test_synthesis.py::test_generate_merchant_name -v
```

## Next Steps

After successful synthesis:
1. ✅ Review output files in `data/processed/`
2. ✅ Validate data quality (check for any issues)
3. ✅ Proceed to PR #4: Data Ingestion (load into SQLite)
4. ✅ Start feature detection (PR #5-8)

