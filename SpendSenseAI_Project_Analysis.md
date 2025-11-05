# SpendSenseAI: PRD Analysis & Implementation Guide

## Project Summary

**SpendSenseAI** is a consent-aware, explainable AI system that analyzes Plaid-style transaction data to:
- Detect behavioral patterns (subscriptions, savings, credit usage, income stability)
- Assign users to financial personas (5 types)
- Deliver personalized financial **education** (not advice) with clear rationales
- Maintain strict guardrails around eligibility, consent, and tone

**Core Philosophy:** Transparency over sophistication, education over sales, explainability over black-box AI.

---

## Key Challenges

### 1. Regulatory & Compliance Challenges
- **Financial Advice Boundary**: Walking the line between education and regulated financial advice
- **Consent Management**: Building explicit opt-in/opt-out mechanisms and enforcing them consistently
- **Tone Guardrails**: Preventing shaming language while still being actionable
- **Disclosure Requirements**: Every recommendation needs "not financial advice" disclaimer

### 2. Data Quality & Realism
- **Synthetic Data Generation**: Creating 50-100 realistic user profiles with diverse financial situations
- **Plaid Schema Compliance**: Matching exact structure (accounts, transactions, liabilities)
- **Behavioral Diversity**: Ensuring data spans income levels, credit behaviors, saving patterns
- **No Real PII**: Generating believable fake data without privacy concerns

### 3. Feature Engineering Complexity
- **Temporal Windows**: Computing signals across both 30-day and 180-day windows
- **Recurring Pattern Detection**: Identifying subscriptions (≥3 occurrences with monthly/weekly cadence)
- **Income Stability**: Detecting payroll ACH, payment frequency, variability
- **Edge Cases**: Handling irregular payments, seasonal variations, one-time large expenses

### 4. Persona Assignment Logic
- **Multiple Persona Matching**: What if a user qualifies for multiple personas?
- **Prioritization Rules**: Need clear hierarchy when conflicts occur
- **Custom 5th Persona**: Designing a meaningful persona not already covered
- **Temporal Consistency**: Preventing persona "flickering" between time windows

### 5. Explainability Requirements
- **100% Rationale Coverage**: Every recommendation needs plain-language explanation
- **Decision Traceability**: Maintaining complete audit trails
- **Data Citation**: Rationales must cite specific transactions/balances
- **Non-technical Language**: Explaining complex financial concepts simply

### 6. Eligibility & Safety
- **Product Filtering**: Don't recommend savings accounts to users who already have one
- **Credit Checks**: Respect minimum income/credit requirements
- **Harmful Products**: Actively exclude predatory loans, high-fee products
- **Context Awareness**: Recommendations must match actual user situation

---

## Critical Nuances to Pay Attention To

### A. Temporal Granularity
**Two Analysis Windows:**
- **30-day window:** Short-term behaviors, immediate concerns
- **180-day window:** Long-term trends, structural patterns

- Signals must be computed for BOTH windows
- Personas can differ between windows (e.g., recent high utilization vs. long-term builder)
- Recommendations should acknowledge timeframe context

### B. Financial Category Subtleties

**Credit Utilization Thresholds:**
- ≥30%: Warning zone
- ≥50%: High utilization (triggers Persona 1)
- ≥80%: Critical zone

**Savings Account Types to Track:**
- Savings, Money Market, Cash Management, HSA
- Don't confuse checking accounts with savings

**Income Detection:**
- Must distinguish payroll ACH from other deposits
- Payment frequency matters (biweekly vs. monthly vs. variable)
- Cash-flow buffer = savings / monthly expenses

### C. Persona Priority Logic

Critical question: **What if someone is both "High Utilization" AND "Savings Builder"?**
- High Utilization should likely take priority (address immediate risk)
- Document your prioritization rules explicitly
- Consider primary/secondary persona assignments

**Suggested Priority Order (Highest to Lowest):**
1. High Utilization (immediate financial risk)
2. Variable Income Budgeter (income instability)
3. Subscription-Heavy (spending optimization)
4. Savings Builder (growth opportunity)
5. Custom Persona (depends on design)

### D. Recommendation Eligibility Matrix

| Offer Type | Eligibility Checks |
|------------|-------------------|
| Balance Transfer Card | Current utilization ≥30%, credit score threshold, no recent applications |
| High-Yield Savings | No existing HYSA, building emergency fund, minimum deposit met |
| Budgeting App | Variable income or insufficient tracking |
| Subscription Manager | ≥3 recurring subscriptions detected |

### E. Tone Compliance Examples

**❌ Bad (Shaming):**
- "You're overspending on subscriptions"
- "Stop wasting money on interest"
- "Your savings rate is too low"
- "You can't afford this lifestyle"

**✅ Good (Educational):**
- "We noticed recurring charges totaling $147/month across 5 services"
- "Reducing utilization below 30% could save $87/month in interest"
- "Increasing savings by 2% would build a 3-month emergency fund in X months"
- "Your monthly subscription spend has increased 23% over the past quarter"

---

## Technical Architecture Considerations

### Modular Design
- **ingest/** → Data validation, schema enforcement
- **features/** → Signal detection (most complex module)
- **personas/** → Assignment logic with prioritization
- **recommend/** → Content matching + eligibility filtering
- **guardrails/** → Consent checks, tone validation, safety filters
- **ui/** → Operator view (critical for auditability)
- **eval/** → Metrics harness
- **docs/** → Decision log (mandatory)

### Performance Targets
- **<5 seconds** per user for recommendations (100% compliance required)
- **100% coverage** (every user gets persona + ≥3 behaviors)
- **100% explainability** (every recommendation has rationale)
- **≥10 tests** with deterministic behavior

### Storage Strategy
- **SQLite**: User accounts, transactions, consent records, liabilities
- **Parquet**: Feature vectors, time-series analysis, behavioral signals
- **JSON**: Config files, decision traces, rationales, content catalog

### API Endpoints Required
- **POST /users** - Create user
- **POST /consent** - Record consent
- **GET /profile/{user_id}** - Get behavioral profile
- **GET /recommendations/{user_id}** - Get recommendations
- **POST /feedback** - Record user feedback
- **GET /operator/review** - Operator approval queue
- **GET /operator/signals/{user_id}** - View detected signals
- **POST /operator/override/{rec_id}** - Override recommendation

---

## High-Risk Areas

### 1. Feature Engineering Bugs
- Off-by-one errors in date windows
- Timezone handling for transactions
- Pending vs. posted transaction confusion
- Double-counting recurring charges
- Incorrectly classifying one-time charges as recurring

### 2. Consent Violations
- Processing data without explicit opt-in
- Not respecting revoked consent
- Stale consent status
- Assuming implicit consent

### 3. Harmful Recommendations
- Suggesting debt consolidation to someone with stable finances
- Recommending products they're ineligible for
- Creating false urgency ("Act now!")
- Pushing high-fee products

### 4. Edge Cases
- Users with only 1-2 transactions
- Brand new accounts (<30 days data)
- Users who change behavior mid-window
- Seasonal workers with irregular income
- Students with parental deposits
- Retirees with pension income
- Gig economy workers

---

## Success Metrics You Must Hit

| Metric | Target | Why It Matters | How to Measure |
|--------|--------|----------------|----------------|
| Persona Coverage | 100% | Every user should get classified | Count(users_with_persona) / Count(total_users) |
| Behavior Detection | ≥3 per user | Minimum signal richness | Avg(detected_behaviors_per_user) |
| Rationale Coverage | 100% | Explainability requirement | Count(recs_with_rationale) / Count(total_recs) |
| Latency | <5s per user | Usability | Time from request to response |
| Decision Traces | 100% | Auditability for regulators | Count(recs_with_trace) / Count(total_recs) |
| Tests | ≥10 passing | Code quality | Run pytest/unittest |
| Consent Enforcement | 100% | Legal requirement | No recs without consent |

---

## What Makes This Project Unique

### 1. Regulatory Awareness Built-In
Unlike typical ML projects, this requires understanding financial services regulations, consent management, and disclosure requirements.

### 2. Explainability as Primary Goal
Most recommender systems optimize for accuracy/engagement. This optimizes for **transparency** and **trust**.

### 3. Human-in-the-Loop
The operator view is not optional—it's a core requirement. Human oversight is mandatory.

### 4. Harm Prevention
Active filtering against predatory products, not just passive recommendations.

### 5. Privacy-First Design
Consent tracking, data minimization, explicit opt-in/out mechanisms.

---

## Recommended Implementation Order

### Phase 1: Data Foundation (Days 1-3)
**Goal:** Generate realistic synthetic data matching Plaid schema

**Tasks:**
- [ ] Define data schemas (accounts, transactions, liabilities)
- [ ] Create synthetic user generator (50-100 users)
- [ ] Ensure diversity across income levels, credit behaviors, saving patterns
- [ ] Build data validation pipeline
- [ ] Export to CSV/JSON
- [ ] Load into SQLite database

**Deliverables:**
- Synthetic dataset with 50-100 users
- Schema documentation
- Data validation tests

### Phase 2: Feature Engineering (Days 4-7)
**Goal:** Detect behavioral signals across time windows

**Tasks:**
- [ ] Implement subscription detection (recurring merchants ≥3 times)
- [ ] Calculate credit utilization per card
- [ ] Detect savings patterns and growth rates
- [ ] Identify income sources and stability
- [ ] Compute emergency fund coverage
- [ ] Generate 30-day and 180-day windows
- [ ] Handle edge cases (new users, sparse data)

**Deliverables:**
- Feature extraction module
- Signal detection for all 4 categories
- Unit tests for each signal type

### Phase 3: Persona System (Days 8-10)
**Goal:** Assign users to personas with clear prioritization

**Tasks:**
- [ ] Implement 4 defined personas
- [ ] Design custom 5th persona (document rationale)
- [ ] Build prioritization logic for conflicts
- [ ] Test edge cases (multi-persona users)
- [ ] Validate temporal consistency
- [ ] Document decision rules

**Deliverables:**
- Persona assignment module
- Custom persona design doc
- Prioritization rules documentation
- Test coverage for all personas

### Phase 4: Recommendation Engine (Days 11-14)
**Goal:** Generate personalized education + offers with rationales

**Tasks:**
- [ ] Build content catalog (articles, calculators, tips)
- [ ] Create partner offer database
- [ ] Implement eligibility filtering
- [ ] Generate plain-language rationales
- [ ] Add "because" citations to data points
- [ ] Build tone validation (no shaming)
- [ ] Add mandatory disclaimers

**Deliverables:**
- Recommendation engine
- Content catalog (3-5 items per persona)
- Eligibility filter system
- Rationale generator
- Tone compliance tests

### Phase 5: Guardrails & Compliance (Days 15-17)
**Goal:** Enforce consent, eligibility, and safety

**Tasks:**
- [ ] Build consent management system
- [ ] Track opt-in/opt-out status
- [ ] Enforce consent before recommendations
- [ ] Implement eligibility checks
- [ ] Filter harmful/predatory products
- [ ] Add disclosure text to all outputs
- [ ] Build decision trace logging

**Deliverables:**
- Consent management module
- Eligibility enforcement
- Decision trace system
- Compliance documentation

### Phase 6: Operator View (Days 18-20)
**Goal:** Human oversight interface

**Tasks:**
- [ ] Build web interface for operators
- [ ] Display detected signals per user
- [ ] Show persona assignments (30d and 180d)
- [ ] Show generated recommendations with rationales
- [ ] Add approve/override functionality
- [ ] Display decision traces
- [ ] Add flag-for-review feature

**Deliverables:**
- Operator dashboard (web UI)
- Override logging system
- Approval workflow

### Phase 7: Evaluation & Documentation (Days 21-23)
**Goal:** Measure performance and document system

**Tasks:**
- [ ] Build metrics harness
- [ ] Compute coverage, explainability, latency
- [ ] Run fairness analysis
- [ ] Generate per-user decision traces
- [ ] Write evaluation report (1-2 pages)
- [ ] Document all design decisions
- [ ] Create README with setup instructions
- [ ] Record demo video

**Deliverables:**
- Evaluation report (JSON + summary)
- Decision log document
- README with one-command setup
- Demo video

---

## Critical Questions to Answer in Your Design

### 1. Persona Conflict Resolution
**Question:** How do you prioritize when multiple personas match?

**Example Scenario:** User has:
- Credit utilization at 65% (matches High Utilization)
- $300/month net savings inflow (matches Savings Builder)
- 5 recurring subscriptions (matches Subscription-Heavy)

**Recommended Approach:**
- Define explicit priority hierarchy
- Assign primary + secondary personas
- Ensure recommendations address all relevant signals

### 2. Recommendation Freshness
**Question:** How often should personas be recalculated?

**Options:**
- On-demand (when user requests)
- Daily batch processing
- Weekly recalculation
- Event-triggered (after major transaction)

**Recommendation:** Daily batch for 30-day window, weekly for 180-day window

### 3. Consent Granularity
**Question:** Can users consent to some features but not others?

**Options:**
- All-or-nothing consent
- Feature-level consent (subscriptions yes, credit analysis no)
- Time-limited consent

**Recommendation:** Start with all-or-nothing, document ability to extend

### 4. Operator Override Handling
**Question:** How are manual overrides logged and enforced?

**Requirements:**
- Log operator ID, timestamp, reason
- Override takes precedence over algorithm
- Audit trail for compliance
- Expiration policy for overrides

### 5. Custom 5th Persona Design
**Question:** What gap exists in the 4 defined personas?

**Possible Options:**
- **Early Career Professional:** Low balance but high income trajectory
- **Debt-Free Optimizer:** No debt, wants to maximize returns
- **Life Event Planner:** Saving for specific goal (house, wedding, baby)
- **Financial Fragility:** Overdrafts, low balance, needs immediate help
- **High Earner, High Spender:** Good income but low savings rate

**Recommendation:** "Financial Fragility" addresses immediate risk not covered by others

---

## Synthetic Data Generation Strategy

### User Profiles to Create (50-100 users)

**Income Distribution:**
- Low income (<$35k): 20%
- Middle income ($35k-$100k): 50%
- High income (>$100k): 30%

**Credit Behavior Mix:**
- High utilization: 25%
- Moderate utilization: 35%
- Low utilization: 30%
- No credit cards: 10%

**Savings Behavior Mix:**
- Active savers: 30%
- Occasional savers: 40%
- Non-savers: 30%

**Subscription Patterns:**
- Heavy (5+): 20%
- Moderate (2-4): 50%
- Light (0-1): 30%

### Transaction Generation Rules

**Frequency:**
- Income deposits: 1-2 per month (biweekly or monthly)
- Subscriptions: Exact monthly intervals
- Groceries: 8-12 per month
- Dining: 4-8 per month
- Gas: 2-4 per month
- Utilities: 1 per month
- Rent/Mortgage: 1 per month

**Realistic Patterns:**
- Morning coffee charges on weekdays
- Grocery shopping on weekends
- Gas station visits before commutes
- Subscription charges on fixed dates
- Payroll on 1st/15th or every other Friday

---

## Testing Strategy

### Unit Tests (≥10 Required)

1. **Subscription Detection:**
   - Test recurring pattern recognition
   - Test frequency calculation (monthly vs. weekly)
   - Test minimum occurrence threshold (≥3)

2. **Credit Utilization:**
   - Test utilization calculation
   - Test threshold flagging (30%, 50%, 80%)
   - Test handling of multiple cards

3. **Savings Growth:**
   - Test net inflow calculation
   - Test growth rate computation
   - Test emergency fund coverage

4. **Income Stability:**
   - Test payroll ACH detection
   - Test payment frequency calculation
   - Test cash-flow buffer computation

5. **Persona Assignment:**
   - Test single persona match
   - Test multi-persona prioritization
   - Test edge cases (no match)

6. **Consent Enforcement:**
   - Test no recommendations without consent
   - Test consent revocation
   - Test consent status tracking

7. **Eligibility Filtering:**
   - Test product eligibility checks
   - Test existing account filtering
   - Test harmful product exclusion

8. **Rationale Generation:**
   - Test data citation accuracy
   - Test plain-language output
   - Test tone compliance

9. **Decision Tracing:**
   - Test trace completeness
   - Test trace auditability
   - Test trace retrieval

10. **Latency:**
    - Test per-user processing time
    - Test batch processing performance
    - Test <5s requirement compliance

### Integration Tests

- End-to-end: Ingest → Features → Persona → Recommendations → Output
- API testing: All endpoints with various scenarios
- Operator view: Full workflow from review to override

---

## Example Decision Trace Structure

**Decision traces should include:**
- User ID and timestamp
- Window period (30d or 180d)
- Detected signals with numerical values
- Persona matches with confidence levels
- Assigned persona with prioritization rule used
- List of recommendations with rationales
- Data citations for each claim made
- Consent status verification
- Operator review status

**Each recommendation should document:**
- Type (education or partner offer)
- Title and description
- Plain-language rationale
- Specific data citations (account IDs, balances, limits)
- Eligibility checks performed
- Mandatory disclaimer text

---

## Common Pitfalls to Avoid

### 1. Over-Engineering
- Don't build complex ML models when rules work fine
- Focus on explainability, not sophistication
- Keep it simple and auditable

### 2. Under-Documenting
- Every design decision needs justification
- Limitations must be explicit
- Decision traces are not optional

### 3. Privacy Violations
- No real PII in synthetic data
- Consent is not optional
- Log everything for audit purposes

### 4. Ignoring Edge Cases
- Test with sparse data
- Handle new users gracefully
- Account for temporal gaps

### 5. Shaming Language
- Review all copy for tone
- Use neutral, empowering language
- Avoid judgment and urgency

### 6. Skipping the Operator View
- Human oversight is core, not optional
- Build it early, not as an afterthought
- Make it genuinely useful

---

## Resources & References

### Financial Services Regulations
- Consumer Financial Protection Bureau (CFPB) guidelines
- Fair Credit Reporting Act (FCRA)
- Financial advice vs. education distinction

### Plaid API Documentation
- Transaction categorization schema
- Account types and subtypes
- Liability structures

### Privacy & Consent
- GDPR consent requirements (as reference)
- CCPA data rights
- Financial data handling best practices

### Tone & Language
- Plain Language guidelines (plainlanguage.gov)
- Consumer-friendly financial education examples
- Non-judgmental communication principles

---

## Final Checklist

**Before Submission:**

- [ ] 50-100 synthetic users generated
- [ ] All 4 signal types detected (subscriptions, savings, credit, income)
- [ ] All 5 personas implemented and documented
- [ ] 3-5 education items per persona
- [ ] 1-3 partner offers per persona
- [ ] 100% of recommendations have rationales
- [ ] 100% of recommendations have decision traces
- [ ] Consent system fully implemented
- [ ] Eligibility filters working
- [ ] Tone validation passing
- [ ] Operator view functional
- [ ] <5 second latency per user
- [ ] ≥10 unit/integration tests passing
- [ ] README with one-command setup
- [ ] Decision log document complete
- [ ] Evaluation report generated
- [ ] Demo video recorded
- [ ] "Not financial advice" disclaimers on all outputs
- [ ] No real PII in any data
- [ ] No predatory products recommended
- [ ] Code organized into clear modules
- [ ] Git repository ready to submit

---

## Success Criteria Summary

**You've succeeded when:**
1. Every user gets a persona and ≥3 detected behaviors
2. Every recommendation has a clear, plain-language rationale
3. No recommendations go out without consent
4. Operators can review and override any recommendation
5. The system processes users in <5 seconds each
6. All tests pass deterministically
7. A regulator could audit your decision traces
8. Users would actually trust this with their financial data

**Core Principles to Remember:**
- **Transparency over sophistication**
- **User control over automation**
- **Education over sales**
- **Fairness built in from day one**

Build systems people can trust with their financial data.

