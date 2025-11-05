# Next PR: Data Synthesis Strategy

## Answer: Yes, PR #3 is Data Synthesis!

**BUT** we need **PR #2 (Schema Definition) first** as the foundation.

---

## PR Sequence

### ✅ **PR #1: Project Setup** - DONE
- Repository structure
- Documentation
- Git configuration

### 🔄 **PR #2: Data Schema Definition & Validation** - NEXT
**Why first?** We need to define what Plaid-compatible data looks like before we can synthesize it.

**What we'll do:**
- Define Plaid-compatible schemas for Accounts, Transactions, Liabilities
- Create validation functions
- Document data structures
- Write schema validation tests

**Time:** 6-8 hours

### 🎯 **PR #3: Data Synthesis & Transformation** - THEN
**This is where synthesis happens!** With precision and accuracy.

**What we'll do:**
- **Phase 1:** Account Discovery (infer accounts from payment_method patterns)
- **Phase 2:** Transaction Enhancement (map to accounts, transform categories)
- **Phase 3:** Liability Synthesis (extract credit card data from transactions)
- **Validation:** Ensure zero data loss, 100% accuracy

**Time:** 14-18 hours

---

## Precision Strategy for PR #3

### Principles

1. **Deterministic Mapping** - Same input → Same output (always)
2. **Inference Over Assumption** - Use actual data patterns, not guesses
3. **Audit Trail** - Track every transformation
4. **Data Integrity** - Zero data loss, no orphaned transactions

### Step-by-Step Synthesis

#### **Phase 1: Account Discovery**

**Goal:** Identify distinct accounts per customer from `payment_method` patterns

**Algorithm:**
1. Group transactions by `customer_id` + `payment_method`
2. For each group:
   - `credit_card` → Create credit card account
   - `debit_card` → Create checking account
   - `bank_transfer` + large amounts → Could be savings
3. Track `account_balance` per `payment_method` to identify multiple accounts
4. Calculate balances precisely from transaction history
5. Estimate credit limits from balance patterns (max_balance * 1.3, rounded to $500)

**Output:** Accounts table with all required fields

#### **Phase 2: Transaction Enhancement**

**Goal:** Enhance transactions with account_id, merchant_name, Plaid categories

**Algorithms:**
1. **Account Mapping:** Map each transaction to account_id based on payment_method
2. **Merchant Names:** Generate deterministically from merchant_id + category
   - Example: `groceries` + `MERCH000126` → `"Groceries Store #126"`
3. **Category Transformation:** Map merchant_category to Plaid format
   - `groceries` → `GENERAL_MERCHANDISE` (primary) + `GROCERIES` (detailed)
4. **Payment Channel:** Map payment_method to payment_channel
   - `credit_card` → `online`
   - `debit_card` → `online`

**Output:** Enhanced transactions table with all Plaid fields

#### **Phase 3: Liability Synthesis**

**Goal:** Extract credit card liability data from transactions

**Algorithms:**
1. **Payment History:** Extract all credit card payments from transactions
2. **Minimum Payment:** Calculate as 2% of balance or $25 (whichever is higher)
3. **APR Estimation:** Based on utilization tier
   - 0-30% utilization → 18.99% APR
   - 30-50% → 22.99% APR
   - 50-80% → 25.99% APR
   - 80-100% → 28.99% APR
4. **Overdue Status:** No payment in 30+ days AND balance > 0 → overdue
5. **Due Date:** Estimate from payment history frequency

**Output:** Liabilities table for credit cards

---

## Precision Metrics (Targets)

| Metric | Target | How to Measure |
|--------|--------|----------------|
| Account Mapping | 100% | Every transaction has valid account_id |
| Balance Accuracy | 99.9% | Balance math matches within $0.01 |
| Credit Limit Estimation | ±10% | Estimated limits within 10% of actual |
| APR Estimation | ±3% | APR within 3% of realistic range |
| Category Mapping | 100% | All categories mapped to Plaid format |
| Merchant Name Generation | 100% | Deterministic (same ID → same name) |

---

## Validation Checks

After synthesis, we'll validate:

1. ✅ **Data Integrity:**
   - Every transaction has account_id
   - Every account has transactions
   - No duplicate accounts
   - Balance math is correct

2. ✅ **Statistical Validation:**
   - Account type distribution is realistic
   - Credit utilization distribution is realistic
   - APR distribution correlates with utilization

3. ✅ **Business Logic:**
   - Credit cards have liabilities
   - Checking accounts don't have limits
   - Utilization <= 100%
   - APR values are realistic (15-30%)

---

## Next Steps

### Immediate Action:
1. **Start PR #2: Schema Definition** (Foundation)
   - Create branch: `pr-002-data-schemas`
   - Define Plaid-compatible schemas
   - Create validation functions
   - Write tests

### After PR #2:
2. **Start PR #3: Data Synthesis** (Implementation)
   - Create branch: `pr-003-data-synthesis`
   - Implement Phase 1: Account Discovery
   - Implement Phase 2: Transaction Enhancement
   - Implement Phase 3: Liability Synthesis
   - Run validation checks

---

## Why This Order?

**PR #2 → PR #3** because:
- We need to know what Plaid-compatible data looks like (schemas)
- We need validation functions to check synthesis quality
- We need to test against the schema before synthesis
- Foundation before implementation

**This ensures precision and accuracy!**

