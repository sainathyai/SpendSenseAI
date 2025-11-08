# SpendSenseAI Testing Guide

## Overview

This guide outlines what to test and look for when validating the SpendSenseAI Operator Dashboard and the complete system.

## Testing Checklist

### 1. System Health & Connectivity

#### API Server
- ✅ **Health Check**: `http://localhost:8000/health`
  - Should return: `{"status": "healthy", "database": "connected"}`
  - Status should be "healthy"
  - Database should show "connected"

#### Dashboard
- ✅ **Dashboard Loads**: `http://localhost:8501`
  - Should show "SpendSenseAI Operator Dashboard"
  - API Status should show "🟢 healthy"
  - No connection errors

### 2. Pending Reviews Page

#### What to Look For:
- **Empty State**: If no reviews exist, should show "No pending reviews"
- **Review List**: If reviews exist, should show:
  - User ID
  - Timestamp
  - Persona assignment
  - Recommendation count
  - Review buttons (Approve/Reject/Flag)

#### Test Scenarios:
1. **No Reviews**: Should display empty state gracefully
2. **With Reviews**: 
   - Click on a review to see details
   - Test Approve button
   - Test Reject button
   - Test Flag button
   - Verify review status updates

#### Expected Behavior:
- Reviews should be sorted by timestamp (newest first)
- Each review should show user ID and creation time
- Clicking a review should expand to show details
- Actions (Approve/Reject) should update the review status

### 3. User Search Page

#### What to Look For:
- **Search Functionality**: Search by user ID
- **User Profile Display**: When user is selected, should show:
  - Behavioral signals (subscriptions, credit utilization, savings, income)
  - Persona assignments (30-day and 180-day windows)
  - Recommendation history
  - Account information

#### Test Scenarios:
1. **Search Non-Existent User**: Should return error message
2. **Search Valid User**: Should display full profile
3. **View Signals**: Should show:
   - Subscription patterns (merchant names, monthly spend, cadence)
   - Credit utilization (current %, limits, balances)
   - Savings patterns (account balances, growth rate, emergency fund coverage)
   - Income stability (frequency, variability, cash flow buffer)

#### Expected Behavior:
- Search should be fast (< 2 seconds)
- All signals should be displayed with proper formatting
- Persona assignments should show confidence scores
- Charts/visualizations should render correctly (if implemented)

### 4. Decision Traces Page

#### What to Look For:
- **Trace List**: All decision traces for a user
- **Trace Details**: When expanded, should show:
  - Signal traces (what was detected)
  - Persona assignment reasoning
  - Recommendation rationales
  - Data citations (which transactions/signals were used)

#### Test Scenarios:
1. **View Trace**: Select a trace to see full details
2. **Trace Content**: Verify it includes:
   - Input signals
   - Persona assignment logic
   - Recommendation generation reasoning
   - All data citations

#### Expected Behavior:
- Traces should be readable and well-formatted
- JSON data should be properly formatted (if displayed)
- All citations should be valid and traceable

### 5. Audit Log Page

#### What to Look For:
- **Consent Audit Trail**: Shows all consent changes
- **Decision Audit Trail**: Shows all operator actions
- **Filtering**: Should allow filtering by date, user, action type

#### Test Scenarios:
1. **View Consent Log**: Should show consent grants/revocations
2. **View Decision Log**: Should show all approve/reject/flag actions
3. **Filter Logs**: Test date range filtering

#### Expected Behavior:
- Logs should be sorted by timestamp (newest first)
- All actions should include:
  - User ID
  - Timestamp
  - Action type
  - Operator who performed action
  - Notes/reason (if provided)

## End-to-End Testing Flow

### Complete User Journey Test

1. **Start with a User ID** (e.g., from your database)
   ```bash
   # Check what users exist in your database
   sqlite3 data/spendsense.db "SELECT DISTINCT customer_id FROM accounts LIMIT 10;"
   ```

2. **Generate Recommendations** (via API)
   ```bash
   # Get recommendations for a user
   curl http://localhost:8000/users/{user_id}/recommendations
   ```

3. **Check Decision Traces Created**
   - Go to "Decision Traces" page
   - Search for the user ID
   - Verify trace was created

4. **Check Pending Reviews**
   - Go to "Pending Reviews" page
   - Verify the new recommendation appears
   - Review the recommendation details

5. **Approve/Reject Recommendation**
   - Click "Approve" or "Reject"
   - Add review notes
   - Verify status updates

6. **Check Audit Log**
   - Go to "Audit Log" page
   - Verify your action is logged

## Data Validation Tests

### 1. Signal Detection Accuracy

**What to Test:**
- **Subscriptions**: 
  - Are recurring merchants correctly identified?
  - Is monthly recurring spend calculated correctly?
  - Are subscription patterns realistic?
  
- **Credit Utilization**:
  - Is utilization % calculated correctly? (balance / limit * 100)
  - Are high utilization flags triggered at >75%?
  - Are interest charges detected?

- **Savings Patterns**:
  - Are savings accounts correctly identified?
  - Is growth rate calculated correctly?
  - Is emergency fund coverage accurate?

- **Income Stability**:
  - Are payroll deposits identified?
  - Is payment frequency detected correctly?
  - Is variability calculated properly?

### 2. Persona Assignment Logic

**What to Test:**
- **Persona Criteria**:
  - High Utilization Persona: Should trigger at >75% utilization
  - Variable Income Budgeter: Should trigger with income variability
  - Subscription Heavy: Should trigger at >20% subscription share
  - Savings Builder: Should trigger with positive savings growth

- **Persona Prioritization**:
  - If user matches multiple personas, which one is primary?
  - Secondary personas should be assigned correctly

### 3. Recommendation Quality

**What to Test:**
- **Content Relevance**:
  - Are recommendations relevant to the persona?
  - Do educational content items match the persona?
  - Are partner offers appropriate?

- **Rationales**:
  - Are rationales clear and understandable?
  - Do they cite specific data (transactions, signals)?
  - Are they personalized (not generic)?

- **Tone**:
  - Is tone appropriate for the persona?
  - Financial Fragility persona should have gentle tone
  - Savings Builder persona should have empowering tone

## Error Handling Tests

### 1. Invalid User ID
- **Test**: Search for non-existent user ID
- **Expected**: Should show error message, not crash

### 2. Missing Data
- **Test**: User with no transactions
- **Expected**: Should handle gracefully, show "No data available"

### 3. API Connection Loss
- **Test**: Stop API server while dashboard is open
- **Expected**: Dashboard should show connection error, not crash

### 4. Database Connection Issues
- **Test**: Rename/delete database file
- **Expected**: API should return error, dashboard should show error message

## Performance Tests

### 1. Response Times
- **API Health Check**: Should be < 100ms
- **User Search**: Should be < 2 seconds
- **Recommendation Generation**: Should be < 5 seconds
- **Dashboard Page Load**: Should be < 3 seconds

### 2. Concurrent Users
- **Test**: Multiple dashboard sessions
- **Expected**: Should handle multiple users without issues

## Security Tests

### 1. Consent Enforcement
- **Test**: Generate recommendations with consent revoked
- **Expected**: Should not generate recommendations or show limited content

### 2. Data Privacy
- **Test**: Verify no sensitive data exposed in logs
- **Expected**: Account numbers, SSNs should never appear in traces

### 3. Operator Actions Audit
- **Test**: All operator actions should be logged
- **Expected**: Every approve/reject/flag should appear in audit log

## Edge Cases to Test

### 1. User with No Transactions
- **Expected**: Should show "No data available" or "Insufficient data"

### 2. User with Only Credit Card Transactions
- **Expected**: Should still detect credit utilization, but may not detect income

### 3. User with Multiple Personas
- **Expected**: Should show primary persona, with secondary personas listed

### 4. Very Large Transaction History
- **Expected**: Should still process efficiently without timeouts

### 5. Invalid Date Ranges
- **Expected**: Should handle gracefully, use default windows

## Visual/UI Tests

### 1. Dashboard Layout
- All pages should be accessible
- Navigation should work smoothly
- No broken links or missing content

### 2. Data Display
- Numbers should be formatted correctly (currency, percentages)
- Dates should be readable format
- Charts/graphs should render (if implemented)

### 3. Responsive Design
- Dashboard should work in different browser window sizes
- Tables should be scrollable if needed

## Testing with Real Data

### Sample User Test Flow

1. **Pick a user from your database**:
   ```sql
   SELECT DISTINCT customer_id FROM accounts LIMIT 1;
   ```

2. **Generate recommendations**:
   ```bash
   curl http://localhost:8000/users/{customer_id}/recommendations
   ```

3. **Check all pages**:
   - Pending Reviews: Should show new recommendation
   - User Search: Search for user_id, view profile
   - Decision Traces: View trace for this recommendation
   - Audit Log: Should show trace creation

4. **Take action**:
   - Approve or reject the recommendation
   - Add review notes
   - Verify status updates

5. **Verify data flow**:
   - All signals should be accurate
   - Persona should match user's behavior
   - Recommendations should be relevant
   - Rationales should cite real data

## Success Criteria

### ✅ System is Working If:
- ✅ Dashboard loads without errors
- ✅ API health check returns "healthy"
- ✅ User search finds valid users
- ✅ Recommendations can be generated
- ✅ Decision traces are created
- ✅ Operator actions (approve/reject) work
- ✅ Audit log records all actions
- ✅ All data is accurate and traceable

### ⚠️ Warning Signs:
- ⚠️ API errors (500, 404)
- ⚠️ Slow response times (> 5 seconds)
- ⚠️ Missing data in traces
- ⚠️ Incorrect persona assignments
- ⚠️ Generic/non-personalized recommendations
- ⚠️ Broken UI elements
- ⚠️ Database connection errors

## Quick Test Commands

```bash
# Test API health
curl http://localhost:8000/health

# Get list of users (if you have a test endpoint)
curl http://localhost:8000/users

# Get recommendations for a user
curl http://localhost:8000/users/{user_id}/recommendations

# Get pending reviews
curl http://localhost:8000/operator/review

# Get user signals
curl http://localhost:8000/operator/signals/{user_id}

# Check database directly
sqlite3 data/spendsense.db "SELECT COUNT(*) FROM transactions;"
sqlite3 data/spendsense.db "SELECT DISTINCT customer_id FROM accounts LIMIT 5;"
```

## Next Steps After Testing

1. **Document Issues**: Note any bugs or unexpected behavior
2. **Verify Data Accuracy**: Check that signals match actual transaction data
3. **Test Edge Cases**: Try unusual scenarios
4. **Performance Check**: Verify response times are acceptable
5. **Security Review**: Ensure no sensitive data is exposed

