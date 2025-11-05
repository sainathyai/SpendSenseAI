# CSV Data Analysis: Capital One Plaid Data

## Executive Summary

**File Location:** `data/raw/transactions_formatted.csv`

**Overall Assessment:** ✅ **Good foundation** - The CSV has most transaction-level fields needed, but **missing critical account and liability data** required by the PRD.

**Gap Analysis:**
- ✅ Transaction data: 85% complete
- ❌ Account data: 0% (missing entirely)
- ❌ Liability data: 0% (missing entirely)
- ⚠️ Some fields need mapping/transformation

---

## Current CSV Schema

### Fields Present (22 total):

| Field Name | Type | Description | PRD Mapping |
|------------|------|-------------|--------------|
| `transaction_id` | String | Unique transaction identifier | ✅ Maps to transaction ID |
| `timestamp` | DateTime | Full timestamp | ✅ Can derive `date` |
| `date` | Date | Transaction date | ✅ **Required by PRD** |
| `time` | Time | Transaction time | Extra (not in PRD) |
| `customer_id` | String | Customer identifier | ✅ Maps to user ID |
| `merchant_id` | String | Merchant identifier | ✅ Maps to `merchant_entity_id` (PRD) |
| `merchant_category` | String | Category (groceries, gas_station, etc.) | ⚠️ Maps to `personal_finance_category` (needs transformation) |
| `transaction_type` | String | Type (purchase, transfer, refund, etc.) | ✅ Useful for analysis |
| `payment_method` | String | Method (debit_card, credit_card, etc.) | ✅ Maps to `payment_channel` (PRD) |
| `amount` | Float | Transaction amount | ✅ **Required by PRD** |
| `amount_category` | String | Size category (small, medium, large, etc.) | Extra (not in PRD) |
| `status` | String | Status (approved, declined, pending) | ✅ Maps to `pending` status |
| `latitude` | Float | Transaction location | Extra (not in PRD) |
| `longitude` | Float | Transaction location | Extra (not in PRD) |
| `account_balance` | Float | Balance after transaction | ✅ **Useful** - but needs account-level data |
| `is_fraud` | Boolean | Fraud flag | Extra (not in PRD) |
| `hour` | Integer | Hour of day | Extra (not in PRD) |
| `day_of_week` | String | Day name | Extra (not in PRD) |
| `month` | Integer | Month number | Extra (not in PRD) |
| `month_name` | String | Month name | Extra (not in PRD) |
| `quarter` | Integer | Quarter number | Extra (not in PRD) |
| `year` | Integer | Year | Extra (not in PRD) |

---

## PRD Requirements vs. Current Data

### ✅ **Transactions - Mostly Complete**

| PRD Requirement | Current CSV | Status | Action Needed |
|----------------|------------|--------|---------------|
| `account_id` | ❌ Missing | ❌ **CRITICAL** | **Must synthesize** - Map to account per customer |
| `date` | ✅ Present | ✅ Complete | None |
| `amount` | ✅ Present | ✅ Complete | None |
| `merchant_name` or `merchant_entity_id` | ⚠️ `merchant_id` | ⚠️ Partial | **Synthesize `merchant_name`** from `merchant_id` |
| `payment_channel` | ✅ `payment_method` | ✅ Maps well | Map values: debit_card→online, credit_card→online, etc. |
| `personal_finance_category` (primary) | ⚠️ `merchant_category` | ⚠️ Needs mapping | **Transform** to Plaid categories (GENERAL_MERCHANDISE, FOOD_AND_DRINK, etc.) |
| `personal_finance_category` (detailed) | ❌ Missing | ❌ Needed | **Synthesize** detailed subcategories |
| `pending` status | ✅ `status` | ✅ Maps well | Map: "pending"→true, "approved"/"declined"→false |

**Transaction Fields Score: 6/7 required = 85%**

---

### ❌ **Accounts - Missing Entirely (CRITICAL GAP)**

| PRD Requirement | Current CSV | Status | Action Needed |
|----------------|------------|--------|---------------|
| `account_id` | ❌ Missing | ❌ **CRITICAL** | **Must synthesize** - Create accounts per customer |
| `type` (checking, savings, credit card, etc.) | ❌ Missing | ❌ **CRITICAL** | **Must synthesize** - Infer from `payment_method` and transaction patterns |
| `subtype` | ❌ Missing | ❌ **CRITICAL** | **Must synthesize** - Money market, HSA, etc. |
| `balances.available` | ⚠️ `account_balance` (post-transaction) | ⚠️ Partial | **Synthesize** - Calculate from transactions |
| `balances.current` | ⚠️ `account_balance` | ⚠️ Partial | **Synthesize** - Use account_balance as current |
| `balances.limit` | ❌ Missing | ❌ **CRITICAL** | **Must synthesize** - For credit cards, estimate from patterns |
| `iso_currency_code` | ❌ Missing | ❌ Needed | **Synthesize** - Default to "USD" |
| `holder_category` | ❌ Missing | ❌ Needed | **Synthesize** - Default to "consumer" |

**Account Fields Score: 0/8 required = 0%** ❌

---

### ❌ **Liabilities - Missing Entirely (CRITICAL GAP)**

| PRD Requirement | Current CSV | Status | Action Needed |
|----------------|------------|--------|---------------|
| Credit Card: `APRs` (type/percentage) | ❌ Missing | ❌ **CRITICAL** | **Must synthesize** - Estimate based on utilization |
| Credit Card: `minimum_payment_amount` | ❌ Missing | ❌ **CRITICAL** | **Must synthesize** - Calculate from balance |
| Credit Card: `last_payment_amount` | ❌ Missing | ❌ **CRITICAL** | **Must synthesize** - Extract from payment transactions |
| Credit Card: `is_overdue` | ❌ Missing | ❌ **CRITICAL** | **Must synthesize** - Infer from payment patterns |
| Credit Card: `next_payment_due_date` | ❌ Missing | ❌ **CRITICAL** | **Must synthesize** - Estimate from payment history |
| Credit Card: `last_statement_balance` | ❌ Missing | ❌ **CRITICAL** | **Must synthesize** - Use current balance as proxy |
| Mortgages/Student Loans | ❌ Missing | ❌ Not needed initially | Optional for future |

**Liability Fields Score: 0/6 required = 0%** ❌

---

## Most Useful Fields (Existing Data)

### 🎯 **Critical for Feature Detection**

1. **`customer_id`** ⭐⭐⭐⭐⭐
   - **Use:** User identification, persona assignment
   - **Status:** ✅ Complete

2. **`date`** ⭐⭐⭐⭐⭐
   - **Use:** Temporal windows (30d, 180d), time-series analysis
   - **Status:** ✅ Complete

3. **`amount`** ⭐⭐⭐⭐⭐
   - **Use:** All calculations (utilization, savings, income, subscriptions)
   - **Status:** ✅ Complete

4. **`merchant_id`** ⭐⭐⭐⭐⭐
   - **Use:** Subscription detection (recurring merchants)
   - **Status:** ✅ Complete - can identify recurring patterns

5. **`payment_method`** ⭐⭐⭐⭐⭐
   - **Use:** Distinguish credit vs debit (for utilization analysis)
   - **Status:** ✅ Complete - maps to `payment_channel`

6. **`merchant_category`** ⭐⭐⭐⭐
   - **Use:** Categorize spending, identify subscription patterns
   - **Status:** ⚠️ Needs transformation to Plaid categories

7. **`account_balance`** ⭐⭐⭐⭐
   - **Use:** Savings analysis, emergency fund calculation
   - **Status:** ⚠️ Post-transaction balance, needs account-level aggregation

8. **`status`** ⭐⭐⭐
   - **Use:** Filter pending transactions, identify issues
   - **Status:** ✅ Complete

### 📊 **Useful for Analysis (Bonus Fields)**

9. **`transaction_type`** ⭐⭐⭐
   - **Use:** Identify deposits (income), transfers (savings), fees
   - **Status:** ✅ Complete

10. **`timestamp`** ⭐⭐⭐
    - **Use:** Precise timing for recurring patterns
    - **Status:** ✅ Complete

11. **`amount_category`** ⭐⭐
    - **Use:** Quick filtering, visualization
    - **Status:** Extra data

12. **`is_fraud`** ⭐⭐
    - **Use:** Filter out fraudulent transactions
    - **Status:** Extra data

---

## Required Modifications & Synthesized Fields

### 🔧 **Immediate Actions Required**

#### 1. **Synthesize Account Data** (HIGH PRIORITY)

**Create accounts table with:**
```python
# Per customer_id, infer accounts from payment_method patterns
accounts = {
    "account_id": "ACC-{customer_id}-{type}-{index}",  # e.g., "ACC-CUST000135-CHECKING-1"
    "customer_id": "CUST000135",
    "type": "checking" | "savings" | "credit_card" | "money_market" | "hsa",
    "subtype": "checking" | "savings" | "credit_card" | "money_market" | "hsa",
    "balances": {
        "available": float,  # Calculate from transactions
        "current": float,    # Current balance
        "limit": float       # For credit cards, synthesize from patterns
    },
    "iso_currency_code": "USD",
    "holder_category": "consumer"
}
```

**Logic:**
- If `payment_method == "credit_card"` → Create credit card account
- If `payment_method == "debit_card"` → Create checking account
- If `transaction_type == "deposit"` and large amounts → Could be savings account
- Track `account_balance` per payment method to identify multiple accounts

#### 2. **Synthesize Merchant Names** (MEDIUM PRIORITY)

**From `merchant_id` → `merchant_name`:**
```python
# Option 1: Use category + ID
merchant_name = f"{merchant_category.title()} Store #{merchant_id[-3:]}"
# Example: "Groceries Store #126"

# Option 2: Create realistic names by category
merchant_map = {
    "groceries": ["Whole Foods", "Safeway", "Kroger", "Walmart"],
    "gas_station": ["Shell", "Exxon", "BP", "Chevron"],
    "restaurant": ["McDonald's", "Starbucks", "Chipotle", "Subway"],
    # ... etc
}
```

#### 3. **Transform Merchant Categories to Plaid Categories** (HIGH PRIORITY)

**Current → Plaid Mapping:**
```python
CATEGORY_MAP = {
    "groceries": "GENERAL_MERCHANDISE",
    "gas_station": "GAS_STATIONS",
    "restaurant": "FOOD_AND_DRINK",
    "retail": "GENERAL_MERCHANDISE",
    "utilities": "GENERAL_SERVICES",
    "healthcare": "GENERAL_SERVICES",
    "transportation": "TRANSPORTATION",
    "entertainment": "ENTERTAINMENT",
    "online_shopping": "GENERAL_MERCHANDISE",
    "other": "GENERAL_MERCHANDISE"
}
```

**Detailed Subcategories:**
```python
DETAILED_CATEGORY_MAP = {
    "groceries": "GROCERIES",
    "gas_station": "GAS_STATIONS",
    "restaurant": "RESTAURANTS",
    "retail": "GENERAL_MERCHANDISE",
    # ... etc
}
```

#### 4. **Synthesize Liability Data** (HIGH PRIORITY)

**For credit card accounts:**
```python
# Extract from transaction patterns
liabilities = {
    "account_id": "ACC-{customer_id}-CREDIT-1",
    "type": "credit",
    "aprs": {
        "type": "purchase",
        "percentage": 18.99  # Synthesize based on balance/utilization
    },
    "minimum_payment_amount": balance * 0.02,  # 2% of balance
    "last_payment_amount": extract_from_payments(),  # From payment transactions
    "is_overdue": infer_from_payment_gaps(),  # If no payment in 30+ days
    "next_payment_due_date": estimate_from_history(),  # Based on patterns
    "last_statement_balance": current_balance  # Use current as proxy
}
```

**Logic:**
- Find all credit card payment transactions (`transaction_type == "transfer"` or `payment_method == "credit_card"` with negative amounts)
- Calculate `last_payment_amount` from recent payments
- Calculate `minimum_payment_amount` as 2% of current balance (industry standard)
- Infer `is_overdue` if no payment in 30+ days and balance > 0
- Estimate `next_payment_due_date` based on payment frequency
- Synthesize `APRs` based on utilization (high utilization = higher APR)

#### 5. **Add `account_id` to Transactions** (CRITICAL)

**Map transactions to accounts:**
```python
# For each transaction, assign account_id based on payment_method
transaction.account_id = f"ACC-{customer_id}-{payment_method_to_account_type(payment_method)}-1"
```

**Example:**
- `payment_method == "credit_card"` → `account_id = "ACC-CUST000135-CREDIT-1"`
- `payment_method == "debit_card"` → `account_id = "ACC-CUST000135-CHECKING-1"`

---

## Data Synthesis Strategy

### Phase 1: Account Discovery (PR #2-3)

1. **Group transactions by `customer_id` and `payment_method`**
2. **Identify account types:**
   - Credit cards: `payment_method == "credit_card"`
   - Checking: `payment_method == "debit_card"` or `payment_method == "bank_transfer"`
   - Savings: Large deposits, infrequent transactions
   - Money market/HSA: Need to infer from patterns

3. **Calculate balances:**
   - Start with initial balance (first transaction's `account_balance - amount`)
   - Track balance changes per account
   - For credit cards, estimate limit from max balance + 20-30%

### Phase 2: Merchant Enhancement (PR #3)

1. **Generate merchant names** from `merchant_id` + `merchant_category`
2. **Create merchant lookup table** for consistency
3. **Map to Plaid categories**

### Phase 3: Liability Inference (PR #3)

1. **For each credit card account:**
   - Extract payment transactions
   - Calculate payment history
   - Synthesize APR based on utilization
   - Estimate due dates

---

## Sample Data Transformation

### Before (Current CSV):
```csv
transaction_id,customer_id,merchant_id,merchant_category,payment_method,amount,account_balance
TXN00000001,CUST000135,MERCH000159,other,debit_card,100.46,6846.96
TXN00000004,CUST000036,MERCH000030,utilities,credit_card,26.94,5523.1
```

### After (Plaid-Compatible):
```csv
# Transactions
account_id,date,amount,merchant_name,merchant_entity_id,payment_channel,personal_finance_category.primary,personal_finance_category.detailed,pending
ACC-CUST000135-CHECKING-1,2024-01-01,100.46,Other Store #159,MERCH000159,online,GENERAL_MERCHANDISE,GENERAL_MERCHANDISE,false
ACC-CUST000036-CREDIT-1,2024-01-01,26.94,Utilities Store #30,MERCH000030,online,GENERAL_SERVICES,UTILITIES,false

# Accounts (synthesized)
account_id,customer_id,type,subtype,balances.available,balances.current,balances.limit,iso_currency_code,holder_category
ACC-CUST000135-CHECKING-1,CUST000135,depository,checking,6947.42,6947.42,null,USD,consumer
ACC-CUST000036-CREDIT-1,CUST000036,credit,credit_card,5473.06,5550.00,10000.00,USD,consumer

# Liabilities (synthesized)
account_id,type,apr.percentage,minimum_payment_amount,last_payment_amount,is_overdue,next_payment_due_date,last_statement_balance
ACC-CUST000036-CREDIT-1,credit,18.99,111.00,500.00,false,2024-02-15,5550.00
```

---

## Recommendations

### ✅ **What to Keep (Most Useful)**

1. **`customer_id`** - Perfect for user identification
2. **`date`** - Exact date for temporal analysis
3. **`amount`** - Precise transaction amounts
4. **`merchant_id`** - Excellent for subscription detection
5. **`payment_method`** - Critical for account type inference
6. **`merchant_category`** - Good foundation, needs transformation
7. **`account_balance`** - Useful for balance tracking (post-transaction)
8. **`status`** - Important for filtering
9. **`transaction_type`** - Useful for income detection

### ⚠️ **What Needs Transformation**

1. **`merchant_category`** → Transform to Plaid categories
2. **`payment_method`** → Map to `payment_channel`
3. **`status`** → Map to `pending` boolean

### ➕ **What to Synthesize**

1. **`account_id`** - CRITICAL - Map transactions to accounts
2. **Account data** - CRITICAL - Full account structure
3. **`merchant_name`** - Generate from merchant_id + category
4. **Liability data** - CRITICAL - Credit card details
5. **Plaid category details** - Detailed subcategories

### 🗑️ **What to Ignore (Not Needed)**

1. **`latitude/longitude`** - Not in PRD
2. **`is_fraud`** - Filter out, but not needed for analysis
3. **`hour`, `day_of_week`, `month`, etc.** - Can derive from `date`
4. **`amount_category`** - Extra categorization

---

## Implementation Priority

### 🔴 **CRITICAL (Must Have)**
1. Synthesize `account_id` for each transaction
2. Create accounts table with type, balances, limits
3. Create liabilities table for credit cards
4. Transform merchant categories to Plaid format

### 🟡 **HIGH PRIORITY (Should Have)**
5. Generate merchant names
6. Add detailed Plaid subcategories
7. Map payment_method to payment_channel
8. Calculate account balances from transactions

### 🟢 **MEDIUM PRIORITY (Nice to Have)**
9. Infer account subtypes (HSA, money market)
10. Synthesize mortgage/student loan data (optional)
11. Add ISO currency codes (default to USD)

---

## Next Steps

1. **Create data transformation script** (PR #2-3)
   - Load CSV
   - Synthesize accounts
   - Synthesize liabilities
   - Transform categories
   - Export to Plaid-compatible format

2. **Update data schema** (PR #2)
   - Define Plaid-compatible schemas
   - Document transformation rules

3. **Create synthetic data generator** (PR #3)
   - Use this CSV as template
   - Generate additional users
   - Ensure 50-100 users total

---

## Summary Score

| Component | Current Status | Required | Gap | Priority |
|-----------|---------------|----------|-----|----------|
| **Transactions** | 85% | 7 fields | 2 missing | 🟡 HIGH |
| **Accounts** | 0% | 8 fields | 8 missing | 🔴 CRITICAL |
| **Liabilities** | 0% | 6 fields | 6 missing | 🔴 CRITICAL |
| **Overall** | **28%** | 21 fields | 16 missing | **Needs work** |

**Verdict:** ✅ **Good foundation** - The transaction data is solid, but we need to **synthesize account and liability data** to meet PRD requirements. This is achievable with the existing transaction data.

