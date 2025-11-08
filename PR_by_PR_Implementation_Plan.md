# SpendSenseAI: PR-by-PR Implementation Plan

## Project Architecture Overview

### UI Strategy & Privacy Considerations

**Is this a backend service for a larger UI application?**
YES. SpendSenseAI is fundamentally a **backend service** that:
- Processes financial transaction data
- Generates behavioral insights
- Provides recommendations via API
- Can be integrated into existing banking/fintech apps

**The Operator Dashboard: Privacy & Purpose**

**NO, an operator dashboard is NOT a privacy violation.** Here's why:

1. **Operator View = Internal Compliance Tool**
   - Operators are bank/fintech employees with existing data access
   - They already have permission to view customer accounts
   - This is for oversight, not customer-facing UI

2. **Privacy Boundaries:**
   - **Operator View:** Internal staff reviewing algorithm decisions (ALLOWED)
   - **Customer Dashboard:** End-users seeing their own data (ALLOWED)
   - **External View:** Third parties seeing customer data (VIOLATION)

3. **Required for Compliance:**
   - Regulators EXPECT human oversight of automated financial systems
   - Operator view provides audit trail
   - Prevents automated harm

**UI Components in This Project:**

| Component | Purpose | Privacy Level | Required? |
|-----------|---------|---------------|-----------|
| **Operator Dashboard** | Internal oversight & review | High (employee access) | YES - Core requirement |
| **API Layer** | Backend service endpoints | Secure | YES - Core requirement |
| **Customer Dashboard** | Optional demo of end-user experience | User sees own data only | OPTIONAL - Enhances submission |
| **Admin Panel** | System configuration | Internal only | OPTIONAL - Nice to have |

---

## PR Strategy: Core Requirements (18 PRs)

### Phase 1: Foundation & Data Infrastructure (PRs 1-4)

#### **PR #1: Project Setup & Documentation**
**Purpose:** Establish repository structure and development environment
**Scope:**
- Repository initialization with .gitignore
- README with project overview
- requirements.txt or package.json with dependencies
- Directory structure for all modules
- Development environment setup guide
- Contributing guidelines

**Dependencies:** None
**Estimated Effort:** 2-4 hours
**Review Focus:** Documentation clarity, setup simplicity

---

#### **PR #2: Data Schema Definition & Validation**
**Purpose:** Define Plaid-compatible data structures
**Scope:**
- Schema definitions for Accounts (account_id, type/subtype, balances, currency)
- Schema definitions for Transactions (account_id, date, amount, merchant, category, pending)
- Schema definitions for Liabilities (credit cards, mortgages, student loans)
- Data validation logic (type checking, required fields, constraints)
- Schema documentation with examples
- Unit tests for validation logic

**Dependencies:** PR #1
**Estimated Effort:** 6-8 hours
**Review Focus:** Plaid compliance, validation completeness

---

#### **PR #3: Data Synthesis & Transformation Engine**
**Purpose:** Transform existing Capital One CSV data into Plaid-compatible format with precision
**Scope:**
- **Phase 1: Account Discovery & Synthesis**
  - Analyze payment_method patterns to identify distinct accounts per customer
  - Synthesize account_id for each account (deterministic mapping)
  - Calculate account balances precisely from transaction history
  - Estimate credit limits accurately from balance patterns
  - Identify account types (checking, savings, credit card, money market, HSA)
  - Create accounts table with all required fields
- **Phase 2: Transaction Enhancement**
  - Map transactions to accounts (add account_id to each transaction)
  - Generate merchant_name deterministically from merchant_id + category
  - Transform merchant_category to Plaid personal_finance_category (primary/detailed)
  - Map payment_method to payment_channel (Plaid format)
  - Map status to pending boolean
  - Validate transaction data integrity
- **Phase 3: Liability Synthesis**
  - Extract credit card payment history from transactions
  - Calculate minimum_payment_amount accurately (industry standard: 2% or $25)
  - Synthesize APR based on utilization tiers (18.99% - 28.99% range)
  - Determine is_overdue status from payment patterns
  - Estimate next_payment_due_date from payment history
  - Calculate last_statement_balance
  - Create liabilities table for credit cards
- **Validation & Quality Checks**
  - Data integrity validation (no orphaned transactions, no duplicate accounts)
  - Balance math validation (balance = previous_balance - amount)
  - Credit limit validation (limit >= max_balance)
  - Utilization validation (utilization <= 100%)
  - APR validation (realistic range: 15-30%)
- Export to Plaid-compatible format (CSV/JSON)
- Precision metrics reporting (account mapping %, balance accuracy, etc.)
- Unit tests for synthesis algorithms
- Documentation of synthesis rules and precision

**Dependencies:** PR #2 (Schema definitions needed before synthesis)
**Estimated Effort:** 14-18 hours
**Review Focus:** Precision, accuracy, zero data loss, Plaid compliance

---

#### **PR #4: Data Ingestion & Storage Pipeline**
**Purpose:** Load synthetic data into database
**Scope:**
- SQLite database setup
- Data loading functions (CSV/JSON to database)
- Data integrity checks
- Query utilities for retrieving accounts, transactions, liabilities
- Transaction filtering (exclude pending, exclude business accounts)
- Date range queries for windowing
- Unit tests for ingestion pipeline

**Dependencies:** PR #3
**Estimated Effort:** 6-8 hours
**Review Focus:** Data integrity, query performance

---

### Phase 2: Behavioral Signal Detection (PRs 5-8)

#### **PR #5: Subscription Detection Engine**
**Purpose:** Identify recurring subscription patterns
**Scope:**
- Merchant transaction grouping
- Cadence detection (monthly, weekly, biweekly)
- Minimum occurrence threshold (≥3 in 90 days)
- Monthly recurring spend calculation
- Subscription share of total spend
- 30-day and 180-day window support
- Edge case handling (skipped months, annual subscriptions)
- Unit tests with known patterns

**Dependencies:** PR #4
**Estimated Effort:** 10-12 hours
**Review Focus:** Pattern accuracy, false positive rate

---

#### **PR #6: Credit Utilization Analysis**
**Purpose:** Calculate credit usage metrics
**Scope:**
- Per-card utilization calculation (balance / limit)
- Threshold flagging (30%, 50%, 80%)
- Minimum-payment-only detection
- Interest charge identification
- Overdue status tracking
- Multi-card aggregation
- 30-day and 180-day trending
- Unit tests with various credit scenarios

**Dependencies:** PR #4
**Estimated Effort:** 8-10 hours
**Review Focus:** Math accuracy, threshold logic

---

#### **PR #7: Savings Pattern Detection**
**Purpose:** Analyze savings behaviors and growth
**Scope:**
- Savings account identification (savings, money market, HSA, cash management)
- Net inflow calculation (deposits - withdrawals)
- Growth rate computation over window
- Emergency fund coverage (savings balance / avg monthly expenses)
- Automated transfer detection
- 30-day and 180-day comparison
- Unit tests for various saving patterns

**Dependencies:** PR #4
**Estimated Effort:** 10-12 hours
**Review Focus:** Account classification, calculation accuracy

---

#### **PR #8: Income Stability Analysis**
**Purpose:** Detect and assess income patterns
**Scope:**
- Payroll ACH identification (employer deposits)
- Payment frequency calculation (biweekly, monthly, irregular)
- Income variability measurement (coefficient of variation)
- Cash-flow buffer calculation (balance / monthly burn rate)
- Median pay gap calculation
- Gig/freelance income detection
- 30-day and 180-day windowing
- Unit tests for various income scenarios

**Dependencies:** PR #4
**Estimated Effort:** 12-14 hours
**Review Focus:** Payroll detection accuracy, variability metrics

---

### Phase 3: Persona System (PRs 9-11)

#### **PR #9: Persona Definition & Assignment Logic**
**Purpose:** Implement 4 required personas with matching criteria
**Scope:**
- **Persona 1: High Utilization**
  - Criteria: utilization ≥50% OR interest charges > 0 OR minimum-payment-only OR overdue
  - Focus: Payment planning, debt reduction
- **Persona 2: Variable Income Budgeter**
  - Criteria: Median pay gap > 45 days AND cash-flow buffer < 1 month
  - Focus: Percent-based budgets, emergency fund
- **Persona 3: Subscription-Heavy**
  - Criteria: Recurring merchants ≥3 AND (monthly spend ≥$50 OR subscription share ≥10%)
  - Focus: Subscription audit, cancellation tips
- **Persona 4: Savings Builder**
  - Criteria: Growth rate ≥2% OR net inflow ≥$200/month, AND utilizations < 30%
  - Focus: Goal setting, APY optimization
- Persona matching algorithm
- 30-day and 180-day persona assignment
- Unit tests for each persona criteria

**Dependencies:** PRs #5-8
**Estimated Effort:** 10-12 hours
**Review Focus:** Criteria accuracy, test coverage

---

#### **PR #10: Custom 5th Persona Design & Implementation**
**Purpose:** Create additional persona for unmet needs
**Scope:**
- Persona design document with rationale
- **Recommended: "Financial Fragility" Persona**
  - Criteria: Overdrafts in past 30d OR checking balance < $500 consistently OR late fees present
  - Focus: Immediate cash-flow management, fee avoidance, buffer building
  - Why: Addresses immediate financial stress not captured by other personas
- Implementation of criteria logic
- Documentation of focus areas
- Unit tests for new persona

**Dependencies:** PR #9
**Estimated Effort:** 6-8 hours
**Review Focus:** Persona uniqueness, criteria validity

---

#### **PR #11: Persona Prioritization & Conflict Resolution**
**Purpose:** Handle users matching multiple personas
**Scope:**
- Prioritization rules documentation
  - Priority 1: High Utilization (immediate financial risk)
  - Priority 2: Financial Fragility (if implemented)
  - Priority 3: Variable Income Budgeter (income instability)
  - Priority 4: Subscription-Heavy (spending optimization)
  - Priority 5: Savings Builder (growth opportunity)
- Primary + secondary persona assignment
- Temporal consistency checks (avoid persona flickering)
- Edge case handling (no persona match)
- Unit tests for multi-persona scenarios

**Dependencies:** PR #10
**Estimated Effort:** 6-8 hours
**Review Focus:** Prioritization logic, edge cases

---

### Phase 4: Recommendation Engine (PRs 12-14)

#### **PR #12: Education Content Catalog**
**Purpose:** Build library of educational content
**Scope:**
- Content structure definition (title, description, type, target_persona)
- **Per Persona Content (3-5 items each):**
  - High Utilization: Debt paydown strategies, balance transfer guides, autopay setup
  - Variable Income: Budgeting templates, emergency fund calculators, income smoothing
  - Subscription-Heavy: Audit checklists, negotiation tips, bill alerts
  - Savings Builder: Goal-setting tools, HYSA comparison, CD basics
  - Financial Fragility: Fee avoidance, overdraft protection, buffer strategies
- Content metadata (difficulty, estimated_time, format)
- Content storage (JSON catalog)
- Content retrieval functions

**Dependencies:** PR #11
**Estimated Effort:** 8-10 hours
**Review Focus:** Content quality, persona alignment

---

#### **PR #13: Partner Offer System with Eligibility**
**Purpose:** Create partner product catalog with eligibility rules
**Scope:**
- Partner offer structure (product type, provider, requirements, benefits)
- Eligibility rule engine:
  - Minimum income checks
  - Credit score thresholds (simulated for synthetic data)
  - Existing account checks (don't offer HYSA if user has one)
  - Product suitability (credit utilization for balance transfer cards)
- Harmful product blacklist (payday loans, predatory products)
- Offer-persona mapping
- Eligibility validation functions
- Unit tests for eligibility logic

**Dependencies:** PR #11
**Estimated Effort:** 10-12 hours
**Review Focus:** Eligibility accuracy, safety filters

---

#### **PR #14: Rationale Generation & Recommendation Builder**
**Purpose:** Generate plain-language explanations with data citations
**Scope:**
- Recommendation builder (combines persona + signals + content + offers)
- Rationale template system
- Data citation extraction (specific balances, limits, transaction counts)
- Plain-language generation:
  - "We noticed your Visa ending in 4523 is at 68% utilization..."
  - "Your recurring subscriptions total $147/month across 5 services..."
- Tone validation (no shaming language)
- "Because" clause generation citing concrete data
- Mandatory disclaimer attachment
- Unit tests for rationale generation

**Dependencies:** PR #13
**Estimated Effort:** 12-14 hours
**Review Focus:** Language quality, data accuracy, tone

---

### Phase 5: Guardrails & Compliance (PRs 15-16)

#### **PR #15: Consent Management System**
**Purpose:** Track and enforce user consent
**Scope:**
- Consent data model (user_id, status, timestamp, scope)
- Consent states: pending, active, revoked
- Opt-in function with timestamp logging
- Opt-out/revocation function
- Consent verification before recommendations
- Consent audit trail
- Grace period handling
- Unit tests for consent enforcement

**Dependencies:** PR #4
**Estimated Effort:** 6-8 hours
**Review Focus:** Enforcement completeness, audit trail

---

#### **PR #16: Decision Trace Logging System**
**Purpose:** Create audit trail for all recommendations
**Scope:**
- Decision trace structure (user, timestamp, window, signals, personas, recommendations)
- Trace generation at each decision point
- Data citation logging
- Confidence score tracking
- Operator review status
- Trace storage (JSON files or database)
- Trace retrieval API
- Unit tests for trace completeness

**Dependencies:** PRs #11, #14
**Estimated Effort:** 8-10 hours
**Review Focus:** Auditability, completeness

---

### Phase 6: API & Operator Interface (PRs 17-18)

#### **PR #17: REST API Implementation**
**Purpose:** Create service endpoints for all functionality
**Scope:**
- Framework setup (Flask/FastAPI/Express)
- User management endpoints:
  - POST /users - Create user
  - GET /users/{user_id} - Get user details
- Consent endpoints:
  - POST /consent - Record consent
  - DELETE /consent/{user_id} - Revoke consent
- Profile endpoints:
  - GET /profile/{user_id} - Get behavioral profile (signals + persona)
- Recommendation endpoints:
  - GET /recommendations/{user_id} - Get recommendations with rationales
- Feedback endpoints:
  - POST /feedback - Record user feedback
- Operator endpoints:
  - GET /operator/review - Approval queue
  - GET /operator/signals/{user_id} - View signals
  - POST /operator/override/{rec_id} - Override recommendation
  - GET /operator/trace/{rec_id} - View decision trace
- API documentation (OpenAPI/Swagger)
- Integration tests for all endpoints

**Dependencies:** PRs #14, #16
**Estimated Effort:** 12-16 hours
**Review Focus:** API design, error handling, documentation

---

#### **PR #18: Operator Dashboard UI**
**Purpose:** Build internal oversight interface
**Scope:**
- Web interface setup (React/Vue/Streamlit/simple HTML)
- **Dashboard Views:**
  - User search and selection
  - Signal visualization (charts for utilization, savings, income)
  - Persona assignment display (30d and 180d)
  - Recommendation list with rationales
  - Decision trace viewer (expandable JSON/tree view)
  - Approve/reject/override controls
  - Flag-for-review functionality
  - Override reason capture
  - Audit log view
- Responsive design (desktop-first, operators use workstations)
- No PII exposure beyond what operators already access
- Unit/integration tests for UI components

**Dependencies:** PR #17
**Estimated Effort:** 14-18 hours
**Review Focus:** Usability, oversight capabilities, audit trail

---

### Phase 7: Evaluation & Testing (PRs 19-20 - Continuation of Core)

#### **PR #19: Metrics & Evaluation Harness**
**Purpose:** Measure system performance against success criteria
**Scope:**
- Coverage metrics:
  - Persona assignment rate (target: 100%)
  - Behaviors detected per user (target: ≥3)
- Explainability metrics:
  - Recommendations with rationales (target: 100%)
  - Decision trace completeness (target: 100%)
- Performance metrics:
  - Latency per user (target: <5 seconds)
  - Batch processing throughput
- Fairness analysis:
  - Persona distribution by demographic (if available)
  - Offer distribution parity
- Metrics export (JSON/CSV)
- Summary report generation (1-2 pages)
- Visualization of key metrics

**Dependencies:** All previous PRs
**Estimated Effort:** 10-12 hours
**Review Focus:** Metric completeness, success criteria validation

---

#### **PR #20: Integration Testing & End-to-End Validation**
**Purpose:** Ensure all components work together
**Scope:**
- End-to-end test scenarios:
  - New user ingestion → signal detection → persona → recommendations → operator review
- Multi-user batch processing
- Consent enforcement validation
- Eligibility filter validation
- Latency benchmarking
- Edge case testing (no data, sparse data, conflicting signals)
- Performance profiling
- Test report generation
- Bug fixes and refinements

**Dependencies:** All previous PRs
**Estimated Effort:** 12-16 hours
**Review Focus:** System reliability, edge case handling

---

## PR Strategy: Extended Features (10 PRs)

### Extension Category A: Enhanced User Experience

#### **PR #21: Customer-Facing Dashboard (Demo)**
**Purpose:** Show how recommendations appear to end users
**Scope:**
- Simple web interface for customers to view:
  - Their assigned persona (educational framing)
  - Personalized recommendations
  - Educational content
  - Financial snapshot (balances, trends)
- Privacy-first: users only see their own data
- Modern, empowering UI design
- Mobile-responsive
- **NOT required, but significantly enhances submission**

**Dependencies:** PR #17
**Estimated Effort:** 12-16 hours
**Value Add:** Shows complete user journey, demonstrates UX thinking

---

#### **PR #22: Notification System Design**
**Purpose:** How recommendations are delivered to users
**Scope:**
- Notification templates (email, push, in-app)
- Trigger logic (new persona, important insight, offer expiration)
- Frequency controls (avoid spam)
- Personalization engine (dynamic content insertion)
- Unsubscribe handling
- Template examples for each persona
- A/B testing framework design

**Dependencies:** PR #14
**Estimated Effort:** 8-10 hours
**Value Add:** Shows production-readiness thinking

---

#### **PR #23: Interactive Financial Calculators**
**Purpose:** Provide actionable tools within recommendations
**Scope:**
- Credit payoff calculator (time to 30% utilization)
- Emergency fund calculator (months to goal)
- Subscription cost analyzer (annual savings from cancellations)
- Budget planner for variable income
- Embeddable widgets for recommendations
- Shareable results

**Dependencies:** PR #14
**Estimated Effort:** 10-12 hours
**Value Add:** Increases engagement, demonstrates product thinking

---

### Extension Category B: Advanced Analytics

#### **PR #24: Behavioral Trend Analysis**
**Purpose:** Track changes in user behavior over time
**Scope:**
- Month-over-month trend calculation
- Behavior improvement detection
- Persona evolution tracking (are users "graduating"?)
- Early warning signals (savings declining, utilization rising)
- Trend visualization for operator dashboard
- Predictive signals (based on trajectory)

**Dependencies:** PRs #5-8
**Estimated Effort:** 10-12 hours
**Value Add:** Shows longitudinal thinking, impact measurement

---

#### **PR #25: Cohort Analysis & Segmentation**
**Purpose:** Group users by characteristics for insights
**Scope:**
- Cohort definition (by age, income level, join date, geography)
- Persona distribution by cohort
- Average metrics by cohort
- Cohort performance over time
- Fairness analysis (outcome parity across demographics)
- Report generation for operator view

**Dependencies:** PR #19
**Estimated Effort:** 8-10 hours
**Value Add:** Demonstrates fairness awareness, population-level insights

---

#### **PR #26: Recommendation Effectiveness Tracking**
**Purpose:** Measure impact of recommendations
**Scope:**
- Engagement metrics (click-through, completion rates)
- Outcome tracking (did utilization improve after recommendation?)
- Content performance (which articles/tools most effective?)
- Offer conversion rates
- Attribution logic (which recommendation caused change?)
- Feedback loop to recommendation engine
- ROI calculation for partner offers

**Dependencies:** PR #23
**Estimated Effort:** 10-14 hours
**Value Add:** Shows impact measurement, data-driven iteration

---

### Extension Category C: Safety & Explainability

#### **PR #27: Counterfactual Explanations**
**Purpose:** Show "what if" scenarios to increase trust
**Scope:**
- "If you reduced utilization to 30%, your interest would decrease by $X"
- "If you saved $200/month, you'd have 3-month emergency fund in Y months"
- "If you canceled these 3 subscriptions, you'd save $X/year"
- Counterfactual generation engine
- Visualization of scenarios
- Integration with recommendations

**Dependencies:** PR #14
**Estimated Effort:** 8-10 hours
**Value Add:** Advanced explainability, research-level sophistication

---

#### **PR #28: Adversarial Testing & Edge Cases**
**Purpose:** Stress-test the system against unusual inputs
**Scope:**
- Adversarial scenarios:
  - User with extreme behaviors (99% utilization, $0 savings)
  - Users with very little data
  - Users with conflicting signals
  - Data quality issues (missing fields, outliers)
- Graceful degradation logic
- Edge case documentation
- Robustness improvements
- Expanded test suite

**Dependencies:** PR #20
**Estimated Effort:** 10-12 hours
**Value Add:** Shows production readiness, safety consciousness

---

#### **PR #29: Bias Detection & Mitigation**
**Purpose:** Ensure fairness across user groups
**Scope:**
- Demographic parity analysis (if demographics in synthetic data)
- Disparate impact testing (do recommendations differ unfairly?)
- Calibration checks (are confidence scores accurate across groups?)
- Bias mitigation strategies (re-weighting, threshold adjustments)
- Fairness report generation
- Regular fairness audits

**Dependencies:** PR #25
**Estimated Effort:** 12-14 hours
**Value Add:** Ethical AI leadership, regulatory compliance

---

### Extension Category D: Production Readiness

#### **PR #30: Monitoring & Alerting System**
**Purpose:** Detect system issues in production
**Scope:**
- Health check endpoints
- Performance monitoring (latency, throughput)
- Error rate tracking
- Data quality monitors (missing transactions, schema violations)
- Anomaly detection (sudden persona distribution changes)
- Alert configuration (email, Slack, PagerDuty)
- Dashboard for system health

**Dependencies:** PR #17
**Estimated Effort:** 8-10 hours
**Value Add:** Production operations thinking

---

## UI Architecture Deep Dive

### The Three UI Layers

#### **Layer 1: Backend Service (Core)**
**What:** REST API providing recommendation engine
**Users:** Other systems, integrations
**Privacy:** Secure API keys, authentication
**Status:** REQUIRED

#### **Layer 2: Operator Dashboard (Core)**
**What:** Internal web interface for compliance staff
**Users:** Bank employees, compliance officers, customer support
**Privacy:** 
- Operators already have access to customer data (part of their job)
- Equivalent to looking up customer in existing systems
- Logged and audited
- NOT a privacy violation
**Status:** REQUIRED by PRD

**Why Operators Need This:**
- Review algorithm recommendations before sending to customers
- Override harmful/incorrect recommendations
- Investigate customer complaints ("why did I get this recommendation?")
- Audit compliance with regulations
- Flag patterns requiring policy changes

#### **Layer 3: Customer Dashboard (Extension)**
**What:** End-user web/mobile interface showing their personalized insights
**Users:** Bank customers (end users)
**Privacy:**
- Users see ONLY their own data
- Behind authentication
- Same privacy as online banking
**Status:** OPTIONAL (but impressive)

**Customer Dashboard Value:**
- Demonstrates complete user experience
- Shows UI/UX design skills
- Makes project more tangible
- Easier to demo/present
- Could use screenshots/mockups instead of full implementation

---

### Privacy Guardrails for Operator View

**What Operators CAN See:**
- Customer transaction patterns (they already have access)
- Generated recommendations before delivery
- Decision traces and rationales
- System-generated insights

**What Operators CANNOT Do:**
- Share data externally
- Use data for non-work purposes
- Access customers outside their support scope

**How to Document This:**
- Operator access logging (who viewed what, when)
- Role-based access control (not all operators see all customers)
- Audit trail for all actions
- Compliance documentation

**This is Standard Banking Practice:**
- Customer service reps can view your account
- Fraud analysts review transactions
- Compliance officers audit patterns
- Operators reviewing AI decisions is the SAME MODEL

---

## Recommended PR Sequence

### Minimum Viable Product (18 PRs - 3 weeks)
Complete PRs #1-20 for 100% requirement compliance

### Enhanced Submission (25 PRs - 4 weeks)
Add PRs #21 (Customer Dashboard), #24 (Trend Analysis), #27 (Counterfactuals), #28 (Adversarial Testing), #29 (Bias Detection)

### Production-Ready System (30 PRs - 5-6 weeks)
Complete all PRs for comprehensive, deployable system

---

## Timeline Estimates

| Phase | Core PRs | Extended PRs | Total Hours | Calendar Days |
|-------|----------|--------------|-------------|---------------|
| Foundation | 4 | 0 | 26-36 | 3-5 days |
| Features | 4 | 2 | 40-48 + 18-22 | 5-7 days |
| Personas | 3 | 0 | 22-28 | 3-4 days |
| Recommendations | 3 | 1 | 30-36 + 10-12 | 4-5 days |
| Guardrails | 2 | 3 | 14-18 + 30-36 | 2-3 days |
| UI & API | 2 | 1 | 26-34 + 12-16 | 3-5 days |
| Evaluation | 2 | 1 | 22-28 + 8-10 | 3-4 days |
| **TOTAL** | **20** | **10** | **180-228 + 78-96** | **23-33 days** |

**Core Requirements Only:** 180-228 hours (~3-4 weeks full-time)
**With Extensions:** 258-324 hours (~5-6 weeks full-time)

---

## Review Checklist Per PR

Before submitting each PR, verify:

- [ ] Meets stated scope completely
- [ ] Includes unit tests (where applicable)
- [ ] Passes all existing tests
- [ ] Documentation updated (README, API docs, decision log)
- [ ] No hardcoded values (use configs)
- [ ] Deterministic behavior (seeded randomness)
- [ ] Error handling implemented
- [ ] Performance acceptable (<5s for recommendation PRs)
- [ ] Privacy considerations addressed
- [ ] Code follows style guidelines
- [ ] PR description explains "why" not just "what"
- [ ] Edge cases considered and tested
- [ ] Reviewer can run and validate locally

---

## Success Metrics Tracking

**Track these metrics as you build:**

| Metric | Target | PRs That Impact It |
|--------|--------|-------------------|
| Persona Coverage | 100% | #9-11 |
| Behaviors per User | ≥3 | #5-8 |
| Rationale Coverage | 100% | #14 |
| Decision Traces | 100% | #16 |
| Latency | <5s/user | #5-8, #12-14 |
| Unit Tests | ≥10 | All PRs |
| Consent Enforcement | 100% | #15 |

**Run metrics after PRs #19-20 to validate 100% compliance**

---

## Key Differentiators in Your Submission

**What Makes a Platinum-Level Submission:**

1. **100% Core Requirements Met** (PRs #1-20)
2. **Customer Dashboard** (PR #21) - Shows end-to-end thinking
3. **Bias Detection** (PR #29) - Demonstrates ethical AI awareness
4. **Counterfactual Explanations** (PR #27) - Advanced explainability
5. **Production Monitoring** (PR #30) - Shows operational maturity
6. **Comprehensive Documentation** - Every decision justified
7. **Clean, Modular Code** - Easy to understand and extend
8. **Thoughtful Custom Persona** (PR #10) - Original thinking

**Go beyond "it works" to "it should be deployed"**

---

## Final Note on UI & Privacy

**Bottom Line:**
- **Backend Service:** Core architecture (REQUIRED)
- **Operator Dashboard:** Compliance necessity, NOT privacy violation (REQUIRED)
- **Customer Dashboard:** Enhances submission, shows UX skills (OPTIONAL but valuable)

**Operator Dashboard Privacy:**
- Operators are trusted employees with data access
- Equivalent to customer service tools in banking
- Required for human oversight of AI systems
- Logged and audited
- Industry standard practice

**Build the Operator Dashboard without hesitation - it's a requirement, not a risk.**

