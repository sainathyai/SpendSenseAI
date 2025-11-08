# Data Synthesis Strategy: Precision & Accuracy

## Goal

Transform the Capital One CSV data into Plaid-compatible format with **100% accuracy** and **zero data loss**. Every transaction must be correctly mapped, every account properly inferred, and every liability accurately calculated.

---

## Principles for Precision

### 1. **Deterministic Mapping**
- Same input → Same output (always)
- No randomness in critical fields
- Use hash-based IDs for consistency

### 2. **Inference Over Assumption**
- Infer from actual data patterns
- Use statistical analysis, not guesses
- Validate inferences with multiple data points

### 3. **Audit Trail**
- Track every transformation
- Log all synthesis decisions
- Enable rollback if needed

### 4. **Data Integrity**
- No data loss
- No duplicate accounts
- No orphaned transactions

---

## Synthesis Plan: Step-by-Step

### Phase 1: Account Discovery & Synthesis

#### Step 1.1: Analyze Payment Method Patterns

**Goal:** Identify distinct accounts per customer from `payment_method` patterns

**Algorithm:**
```python
# For each customer:
1. Group transactions by payment_method
2. For each payment_method group:
   - If payment_method == "credit_card":
     → Create credit card account
   - If payment_method == "debit_card":
     → Create checking account
   - If payment_method == "bank_transfer" AND large amounts:
     → Could be savings account (check balance patterns)
   - If payment_method == "cash":
     → No account (cash transactions)

3. Track account_balance per payment_method to identify multiple accounts
   - If balance jumps significantly between transactions:
     → Likely different account
```

**Precision Checks:**
- Verify account_balance continuity per payment_method
- Check for balance resets (new account)
- Validate balance math: `balance_after = balance_before - amount`

**Output:**
```python
accounts = {
    "account_id": "ACC-{customer_id}-{type}-{index}",
    "customer_id": "CUST000135",
    "type": "depository" | "credit",
    "subtype": "checking" | "savings" | "credit_card" | "money_market" | "hsa",
    "balances": {
        "available": float,  # Calculate from transactions
        "current": float,    # Latest balance
        "limit": float       # For credit cards, estimate from patterns
    }
}
```

#### Step 1.2: Calculate Account Balances Precisely

**Goal:** Reconstruct accurate account balances from transaction history

**Algorithm:**
```python
# For each account:
1. Sort transactions by date (ascending)
2. Start with first transaction's balance:
   initial_balance = account_balance + amount  # Reverse calculation
3. For each subsequent transaction:
   balance = previous_balance - amount  # For debits
   balance = previous_balance + amount  # For credits/deposits
4. Validate against actual account_balance in CSV
5. If mismatch > $0.01, flag for review
```

**Precision Checks:**
- Balance continuity (no gaps)
- Balance validation against CSV balance
- Handle pending transactions correctly
- Account for refunds (negative amounts)

**Edge Cases:**
- First transaction: Back-calculate initial balance
- Pending transactions: Don't affect balance until posted
- Refunds: Add to balance (negative amount)
- Fees: Subtract from balance (negative amount)

#### Step 1.3: Estimate Credit Limits Accurately

**Goal:** Estimate credit card limits from balance patterns

**Algorithm:**
```python
# For each credit card account:
1. Find maximum balance reached: max_balance
2. Find highest utilization in history: max_util = max_balance / estimated_limit
3. Estimate limit using multiple methods:
   
   Method 1: Max Balance + Buffer
   limit = max_balance * 1.3  # 30% buffer above max
   
   Method 2: Utilization Pattern
   # If balance consistently < 50% of estimated limit
   # Then limit is likely higher
   limit = max_balance * 2.0
   
   Method 3: Payment Pattern
   # If payments are ~2% of balance, estimate from payment history
   # minimum_payment = balance * 0.02
   # If min_payment = $50, balance = $2500, limit ≈ $5000
   
4. Use most conservative estimate: max(Method 1, Method 2, Method 3)
5. Round to nearest $500 (industry standard)
```

**Precision Checks:**
- Limit must be >= max_balance
- Limit should allow for 20-30% utilization in normal cases
- Validate against utilization patterns
- Check for multiple cards (different limits)

**Validation:**
- If balance consistently near limit → estimate is accurate
- If balance rarely >50% of limit → estimate might be too high
- Use payment amounts to validate (2% of balance = minimum payment)

---

### Phase 2: Transaction Enhancement

#### Step 2.1: Generate Account IDs for Transactions

**Goal:** Map every transaction to its account

**Algorithm:**
```python
# For each transaction:
1. Look up account_id from payment_method:
   account_id = account_map[customer_id][payment_method][index]
2. If account not found:
   → Create new account (shouldn't happen if Phase 1 done correctly)
3. Validate account_id exists in accounts table
```

**Precision Checks:**
- Every transaction must have account_id
- account_id must exist in accounts table
- No orphaned transactions

#### Step 2.2: Generate Merchant Names

**Goal:** Create realistic merchant names from merchant_id + category

**Algorithm:**
```python
# Deterministic mapping (same merchant_id → same name)
merchant_name_map = {}

# For each unique merchant_id:
1. Extract category: merchant_category
2. Generate name based on category:
   
   Category-Based Naming:
   - groceries → ["Whole Foods", "Safeway", "Kroger", "Walmart", "Target"]
   - gas_station → ["Shell", "Exxon", "BP", "Chevron", "Mobil"]
   - restaurant → ["McDonald's", "Starbucks", "Chipotle", "Subway", "Pizza Hut"]
   - retail → ["Amazon", "Walmart", "Target", "Costco", "Best Buy"]
   - utilities → ["Electric Company", "Water Utility", "Gas Company"]
   - healthcare → ["CVS Pharmacy", "Walgreens", "Medical Center"]
   - transportation → ["Uber", "Lyft", "Metro Transit"]
   - entertainment → ["Netflix", "Spotify", "Movie Theater"]
   - online_shopping → ["Amazon", "eBay", "Etsy"]
   
3. Use merchant_id hash to select name deterministically:
   name_index = hash(merchant_id) % len(category_names)
   merchant_name = category_names[name_index] + f" #{merchant_id[-3:]}"
   
   Example: "Groceries Store #159"
```

**Precision Checks:**
- Same merchant_id → Same name (always)
- Names are realistic for category
- No duplicate names per customer (unless intentional)

#### Step 2.3: Transform Merchant Categories to Plaid Format

**Goal:** Map merchant categories to Plaid's personal_finance_category

**Algorithm:**
```python
# Precise mapping (no ambiguity)
CATEGORY_MAP = {
    "groceries": {
        "primary": "GENERAL_MERCHANDISE",
        "detailed": "GROCERIES"
    },
    "gas_station": {
        "primary": "GAS_STATIONS",
        "detailed": "GAS_STATIONS"
    },
    "restaurant": {
        "primary": "FOOD_AND_DRINK",
        "detailed": "RESTAURANTS"
    },
    "retail": {
        "primary": "GENERAL_MERCHANDISE",
        "detailed": "GENERAL_MERCHANDISE"
    },
    "utilities": {
        "primary": "GENERAL_SERVICES",
        "detailed": "UTILITIES"
    },
    "healthcare": {
        "primary": "GENERAL_SERVICES",
        "detailed": "HEALTHCARE"
    },
    "transportation": {
        "primary": "TRANSPORTATION",
        "detailed": "TRANSPORTATION"
    },
    "entertainment": {
        "primary": "ENTERTAINMENT",
        "detailed": "ENTERTAINMENT"
    },
    "online_shopping": {
        "primary": "GENERAL_MERCHANDISE",
        "detailed": "GENERAL_MERCHANDISE"
    },
    "other": {
        "primary": "GENERAL_MERCHANDISE",
        "detailed": "GENERAL_MERCHANDISE"
    }
}
```

**Precision Checks:**
- 100% category coverage (no unmapped categories)
- Consistent mapping (same category → same Plaid category)
- Validate against Plaid's official categories

#### Step 2.4: Map Payment Method to Payment Channel

**Goal:** Transform payment_method to Plaid's payment_channel

**Algorithm:**
```python
PAYMENT_CHANNEL_MAP = {
    "debit_card": "online",      # Most debit cards are online
    "credit_card": "online",     # Most credit cards are online
    "bank_transfer": "other",    # ACH transfers
    "digital_wallet": "online", # Apple Pay, Google Pay
    "cash": "other",             # Cash transactions
}
```

**Precision Checks:**
- All payment methods mapped
- Consistent mapping

---

### Phase 3: Liability Synthesis

#### Step 3.1: Extract Credit Card Payment History

**Goal:** Identify all credit card payments accurately

**Algorithm:**
```python
# For each credit card account:
1. Find all transactions with:
   - account_id matches credit card account
   - transaction_type == "transfer" OR
   - transaction_type == "deposit" AND amount > 0 (payment to credit card)
   - OR amount < 0 AND payment_method == "credit_card" (payment)
   
2. Sort by date (descending)
3. Extract payment amounts
4. Calculate payment frequency
5. Identify last payment: last_payment_amount, last_payment_date
```

**Precision Checks:**
- Payments must be positive amounts (or negative from credit card perspective)
- Payments should be on credit card accounts only
- Validate payment amounts are reasonable (not $0.01)

#### Step 3.2: Calculate Minimum Payment Amount

**Goal:** Estimate minimum payment accurately

**Algorithm:**
```python
# Industry standard: 2% of balance or $25, whichever is higher
current_balance = account.balances.current
minimum_payment = max(current_balance * 0.02, 25.0)

# Round to nearest dollar
minimum_payment = round(minimum_payment)
```

**Precision Checks:**
- Minimum payment >= $25 (industry minimum)
- Minimum payment <= balance (can't pay more than owed)
- Validate against actual payment history if available

#### Step 3.3: Synthesize APR Based on Utilization

**Goal:** Estimate realistic APR based on credit profile

**Algorithm:**
```python
# For each credit card account:
1. Calculate current utilization: utilization = balance / limit
2. Estimate APR based on utilization tier:
   
   Utilization Tier → APR:
   - 0-30%: 18.99% (average APR for good credit)
   - 30-50%: 22.99% (higher risk)
   - 50-80%: 25.99% (high risk)
   - 80-100%: 28.99% (very high risk)
   
3. Add variability based on payment history:
   - If is_overdue: +2.0% APR
   - If no payments in 60 days: +1.5% APR
   - If consistent payments: -0.5% APR
   
4. Round to 2 decimal places
```

**Precision Checks:**
- APR between 15% and 30% (realistic range)
- Higher utilization → Higher APR (logical)
- Validate against industry averages

#### Step 3.4: Determine Overdue Status

**Goal:** Accurately identify if account is overdue

**Algorithm:**
```python
# For each credit card account:
1. Find last payment date: last_payment_date
2. Calculate days since last payment: days_since_payment
3. Estimate payment due date (typically monthly):
   # If balance > 0, payments due monthly
   # Estimate from payment history frequency
   
4. Determine overdue:
   is_overdue = (
       current_balance > 0 AND
       days_since_payment > 30 AND
       (no payment in last 30 days OR balance increased)
   )
```

**Precision Checks:**
- Overdue only if balance > 0
- Overdue only if no payment in 30+ days
- Validate against transaction history

#### Step 3.5: Estimate Next Payment Due Date

**Goal:** Calculate realistic next payment due date

**Algorithm:**
```python
# For each credit card account:
1. Analyze payment history:
   - Find payment frequency (monthly, biweekly, etc.)
   - Find most common payment day of month
   
2. If payment history exists:
   next_due_date = last_payment_date + average_payment_interval
   
3. If no payment history:
   # Default to 30 days from last statement
   next_due_date = last_transaction_date + 30 days
   
4. Round to nearest day
```

**Precision Checks:**
- Due date in future (not past)
- Due date within 30-45 days typically
- Consistent with payment history

---

## Validation & Quality Checks

### 1. Data Integrity Checks

```python
# Run after synthesis:
1. Every transaction has account_id → accounts table
2. Every account has at least one transaction
3. No duplicate account_ids
4. Balance math is correct (balance = previous_balance - amount)
5. Credit limits >= max balance
6. Utilization <= 100%
7. APR values are realistic (15-30%)
8. Due dates are in future
```

### 2. Statistical Validation

```python
# Check distributions:
1. Account type distribution (should match payment_method distribution)
2. Credit utilization distribution (should be realistic)
3. APR distribution (should correlate with utilization)
4. Payment frequency distribution (should be realistic)
```

### 3. Business Logic Validation

```python
# Validate business rules:
1. Credit card accounts have liabilities
2. Checking accounts don't have limits
3. Savings accounts have higher balances
4. Utilization patterns are consistent
5. Payment patterns are realistic
```

---

## Implementation Order

### PR #2: Data Schema Definition & Validation
**Before synthesis, we need:**
- Define Plaid-compatible schemas
- Create validation functions
- Document data structures

### PR #3: Data Synthesis & Transformation
**This is where synthesis happens:**
- Implement Phase 1: Account Discovery
- Implement Phase 2: Transaction Enhancement
- Implement Phase 3: Liability Synthesis
- Run validation checks
- Export to Plaid-compatible format

---

## Precision Metrics

### Target Accuracy

| Metric | Target | How to Measure |
|--------|--------|----------------|
| Account Mapping | 100% | Every transaction has valid account_id |
| Balance Accuracy | 99.9% | Balance math matches within $0.01 |
| Credit Limit Estimation | ±10% | Estimated limits within 10% of actual |
| APR Estimation | ±3% | APR within 3% of realistic range |
| Category Mapping | 100% | All categories mapped to Plaid format |
| Merchant Name Generation | 100% | Deterministic (same ID → same name) |

### Success Criteria

- ✅ No data loss (all transactions included)
- ✅ No orphaned transactions (all have account_id)
- ✅ No duplicate accounts
- ✅ Balance math is correct
- ✅ Credit limits are realistic
- ✅ Utilization calculations are accurate
- ✅ All categories mapped correctly
- ✅ All merchant names generated deterministically

---

## Next Steps

1. **PR #2: Schema Definition** (Foundation)
   - Define schemas
   - Create validation functions

2. **PR #3: Data Synthesis** (Implementation)
   - Implement synthesis algorithms
   - Run validation
   - Export transformed data

This ensures we have the foundation before synthesis.

