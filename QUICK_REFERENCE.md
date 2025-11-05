# SpendSenseAI: Quick Reference Guide

## Project at a Glance

**What:** Explainable financial recommendation engine analyzing Plaid-style transaction data
**Goal:** Deliver personalized financial education with consent, eligibility, and tone guardrails
**Architecture:** Backend service + Operator dashboard (+ optional customer UI)
**Timeline:** 3-4 weeks (core) or 5-6 weeks (with extensions)

---

## Critical Answers to Your Questions

### Is this a backend service for a larger UI application?

**YES.** SpendSenseAI is fundamentally a **REST API backend service** that:
- Processes transaction data
- Generates behavioral insights
- Provides recommendations via API endpoints
- Can be integrated into existing banking/fintech apps

Think of it like Plaid itself - a backend service that banks integrate into their apps.

---

### Operator Dashboard: Privacy Violation?

**NO. Not a privacy violation. Here's why:**

**Operator Dashboard = Internal Compliance Tool**

| Aspect | Explanation |
|--------|-------------|
| **Who are operators?** | Bank/fintech employees, compliance staff, customer support |
| **What do they already see?** | Customer accounts, transactions, balances (part of their job) |
| **What's the operator view?** | Algorithm decisions, recommendation reviews, audit trails |
| **Privacy concern?** | NONE - operators already have this data access |
| **Why is it required?** | Regulators DEMAND human oversight of automated financial systems |

**Real-World Analogies:**
- Customer service reps viewing your account when you call
- Fraud analysts reviewing suspicious transactions
- Compliance officers auditing lending decisions
- **This is the same model - operators reviewing AI recommendations**

**Privacy Boundaries:**

| Who | What They See | Privacy Status |
|-----|--------------|----------------|
| **Operators (Internal)** | Algorithm decisions, customer patterns | ✅ ALLOWED - part of job duties |
| **Customers** | Their own data only | ✅ ALLOWED - personal data access |
| **Third Parties** | Any customer data | ❌ VIOLATION |

**Key Point:** Operators reviewing AI outputs is **required for compliance**, not optional.

---

### Three UI Layers in This Project

#### **Layer 1: REST API Backend** ⭐ REQUIRED
- Service endpoints for all functionality
- POST /users, GET /recommendations, POST /consent, etc.
- This is the core product
- Other systems integrate with this

#### **Layer 2: Operator Dashboard** ⭐ REQUIRED
- Internal web interface for bank staff
- Review recommendations before sending to customers
- Override incorrect/harmful recommendations
- View decision traces for audit
- Flag patterns for policy review
- **NOT customer-facing, NOT a privacy risk**

#### **Layer 3: Customer Dashboard** ⚡ OPTIONAL (but impressive)
- End-user interface showing personalized insights
- Users see ONLY their own data
- Modern, empowering UI design
- Demonstrates UX thinking
- Significantly enhances submission

---

## 30-PR Implementation Path

### Core Requirements (PRs 1-20) - MUST COMPLETE

| Phase | PRs | Key Deliverables | Days |
|-------|-----|-----------------|------|
| **Foundation** | #1-4 | Schemas, synthetic data, ingestion pipeline | 3-5 |
| **Features** | #5-8 | Subscriptions, credit, savings, income detection | 5-7 |
| **Personas** | #9-11 | 5 personas with prioritization | 3-4 |
| **Recommendations** | #12-14 | Content catalog, offers, rationales | 4-5 |
| **Guardrails** | #15-16 | Consent, decision traces | 2-3 |
| **API & UI** | #17-18 | REST API, operator dashboard | 3-5 |
| **Evaluation** | #19-20 | Metrics harness, E2E testing | 3-4 |
| **TOTAL** | **20 PRs** | **100% Requirements** | **23-33 days** |

### Extension Features (PRs 21-30) - VALUE ADDS

**High-Impact Extensions (Pick 3-5):**
- **PR #21:** Customer dashboard (demo end-user experience)
- **PR #24:** Trend analysis (show behavior changes over time)
- **PR #27:** Counterfactual explanations ("what if" scenarios)
- **PR #29:** Bias detection (fairness analysis)
- **PR #30:** Monitoring & alerting (production readiness)

**Extensions add 10-12+ days but significantly strengthen submission**

---

## Must-Hit Success Metrics

| Metric | Target | Why It Matters |
|--------|--------|----------------|
| **Persona Coverage** | 100% | Every user classified |
| **Behaviors Detected** | ≥3 per user | Rich insights |
| **Rationale Coverage** | 100% | Explainability |
| **Decision Traces** | 100% | Auditability |
| **Latency** | <5s per user | Usability |
| **Unit Tests** | ≥10 passing | Code quality |
| **Consent Enforcement** | 100% | Legal compliance |

**Non-Negotiable:** 100% on all metrics, or submission is incomplete.

---

## 5 Personas You Must Implement

### 1. High Utilization (REQUIRED)
**Criteria:** Credit utilization ≥50% OR interest charges > 0 OR minimum-payment-only OR overdue
**Focus:** Debt reduction, payment planning
**Priority:** #1 (immediate financial risk)

### 2. Variable Income Budgeter (REQUIRED)
**Criteria:** Median pay gap > 45 days AND cash-flow buffer < 1 month
**Focus:** Percent-based budgets, emergency fund
**Priority:** #3

### 3. Subscription-Heavy (REQUIRED)
**Criteria:** Recurring merchants ≥3 AND (monthly spend ≥$50 OR subscription share ≥10%)
**Focus:** Subscription audit, cancellation tips
**Priority:** #4

### 4. Savings Builder (REQUIRED)
**Criteria:** Savings growth ≥2% OR net inflow ≥$200/month, AND all utilizations < 30%
**Focus:** Goal setting, APY optimization
**Priority:** #5

### 5. Custom Persona (YOU DESIGN)
**Recommended: Financial Fragility**
**Criteria:** Overdrafts OR checking balance < $500 consistently OR late fees
**Focus:** Immediate cash-flow management, fee avoidance
**Priority:** #2
**Rationale:** Addresses acute financial stress not captured by other personas

---

## Critical Nuances

### Temporal Windows
- **30-day window:** Short-term behaviors, immediate concerns
- **180-day window:** Long-term trends, structural patterns
- **Compute ALL signals for BOTH windows**
- Personas can differ between windows

### Credit Utilization Thresholds
- **≥30%:** Warning zone (mention in recommendations)
- **≥50%:** High utilization (triggers High Utilization persona)
- **≥80%:** Critical zone (urgent priority)

### Persona Conflicts
**What if user matches multiple personas?**
- Use prioritization hierarchy (High Utilization > Financial Fragility > Variable Income > Subscription-Heavy > Savings Builder)
- Assign primary + secondary personas
- Recommendations address both

### Tone Compliance
**❌ Never say:**
- "You're overspending"
- "Stop wasting money"
- "Your savings rate is too low"

**✅ Always say:**
- "We noticed recurring charges totaling $X"
- "Reducing utilization could save $X in interest"
- "Increasing savings by X% would build Y-month emergency fund"

---

## Technology Stack Recommendations

**Backend:**
- **Language:** Python (pandas, scikit-learn) or Node.js
- **API:** Flask/FastAPI (Python) or Express (Node)
- **Database:** SQLite (required for simplicity)
- **Analytics:** Parquet for feature vectors

**Operator Dashboard:**
- **Framework:** React/Vue (if you know them) OR Streamlit (fastest)
- **Alternative:** Simple HTML + vanilla JS (totally acceptable)
- **Charts:** Chart.js, Recharts, or Plotly

**Customer Dashboard (Optional):**
- **Framework:** React with modern UI library (Chakra, shadcn)
- **Design:** Clean, empowering, mobile-responsive

**Testing:**
- **Python:** pytest
- **Node:** Jest
- **E2E:** Playwright or Cypress

---

## Common Mistakes to Avoid

### ❌ Mistake 1: Over-Engineering
Don't build complex ML when rules work fine. Focus on explainability.

### ❌ Mistake 2: Skipping Documentation
Every design decision needs justification in decision log.

### ❌ Mistake 3: Ignoring Edge Cases
Test with sparse data, new users, conflicting signals.

### ❌ Mistake 4: Shaming Language
Review all copy for tone. No judgment.

### ❌ Mistake 5: Weak Operator View
Don't treat it as afterthought. Operators need real utility.

### ❌ Mistake 6: Missing Decision Traces
100% of recommendations need audit trails. Non-negotiable.

---

## Your Recommended Path

### Week 1: Foundation & Features (PRs #1-8)
**Goal:** Synthetic data + signal detection
- Days 1-2: Setup, schemas, data generation
- Days 3-7: Build all 4 signal detectors (subscriptions, credit, savings, income)
- **Checkpoint:** Can query user signals for 30d and 180d windows

### Week 2: Personas & Recommendations (PRs #9-14)
**Goal:** Persona system + recommendation engine
- Days 8-10: Implement 5 personas with prioritization
- Days 11-14: Content catalog, offers, rationales
- **Checkpoint:** Can generate 3-5 recommendations per user with rationales

### Week 3: Guardrails & UI (PRs #15-18)
**Goal:** Compliance + operator interface
- Days 15-17: Consent system, decision traces
- Days 18-21: REST API, operator dashboard
- **Checkpoint:** Operators can review/override recommendations

### Week 4: Evaluation & Extensions (PRs #19-20 + extensions)
**Goal:** Validate metrics + add value
- Days 22-23: Metrics harness, E2E testing
- Days 24-28: Add 2-3 extension PRs (customer dashboard, trend analysis, bias detection)
- **Checkpoint:** 100% on all success metrics

---

## What Makes Your Submission Platinum-Level

**Minimum (Good):**
- ✅ All 20 core PRs complete
- ✅ 100% on all success metrics
- ✅ Clean, modular code
- ✅ Basic documentation

**Strong (Very Good):**
- ✅ Above +
- ✅ Customer dashboard (PR #21)
- ✅ Thoughtful custom persona (PR #10)
- ✅ Comprehensive testing
- ✅ Excellent documentation

**Platinum (Exceptional):**
- ✅ Above +
- ✅ Bias detection & fairness (PR #29)
- ✅ Counterfactual explanations (PR #27)
- ✅ Trend analysis (PR #24)
- ✅ Production monitoring (PR #30)
- ✅ Research-level documentation
- ✅ Deployment-ready system

**Aim for Strong minimum, Platinum if time allows.**

---

## Decision Log Structure

**Required in docs/ folder - document these:**

### 1. Design Decisions
- Why SQLite over PostgreSQL?
- Why rules-based over ML model?
- Why these 30d/180d windows specifically?
- How did you design custom persona?

### 2. Prioritization Logic
- How do you resolve persona conflicts?
- Why this priority order?
- How do you handle edge cases?

### 3. Eligibility Rules
- What makes someone eligible for each offer?
- How do you prevent harmful recommendations?
- What products are blacklisted and why?

### 4. Tone Guidelines
- How do you validate tone compliance?
- What phrases are forbidden?
- How do you frame recommendations positively?

### 5. Performance Optimizations
- How do you stay under 5 seconds?
- What queries are expensive?
- How did you optimize signal detection?

### 6. Limitations
- What can the system not do?
- What assumptions did you make?
- What would you improve with more time?

---

## Submission Checklist

**Before submitting, verify you have:**

- [ ] GitHub repository with all code
- [ ] README with one-command setup
- [ ] requirements.txt or package.json
- [ ] 50-100 user synthetic dataset (CSV/JSON)
- [ ] All 5 personas implemented and tested
- [ ] Recommendation engine with 100% rationales
- [ ] Consent system with enforcement
- [ ] Operator dashboard (functional web UI)
- [ ] REST API with documentation
- [ ] ≥10 passing unit/integration tests
- [ ] Metrics report (JSON + summary)
- [ ] Decision log document
- [ ] Demo video (5-10 minutes)
- [ ] Technical writeup (1-2 pages)
- [ ] All success metrics at 100%

---

## Key Takeaways

1. **This is a backend service** - API-first architecture, UIs are interfaces to it
2. **Operator dashboard is required** - NOT a privacy violation, it's compliance
3. **Customer dashboard is optional** - But makes submission much stronger
4. **20 core PRs get you 100%** - 10 extension PRs make you exceptional
5. **Explainability over complexity** - Rules-based is fine if well-documented
6. **Every recommendation needs "because"** - Data citations are non-negotiable
7. **100% on all metrics or fail** - This is pass/fail, not partial credit
8. **Document everything** - Decision log is as important as code

---

## Quick Start Commands

**After planning, when you start implementation:**

Setup repository structure:
- Create directories: ingest/, features/, personas/, recommend/, guardrails/, ui/, eval/, docs/
- Initialize git, add .gitignore
- Create requirements.txt
- Write README

Generate synthetic data:
- Create 50-100 user profiles
- Generate realistic transaction patterns
- Export to CSV/JSON
- Validate against Plaid schema

Build incrementally:
- One PR at a time
- Test as you go
- Document decisions immediately
- Run metrics after each major milestone

---

## Contact & Resources

**Project Contact:** Bryce Harris - bharris@peak6.com

**Key References:**
- Plaid API documentation (for schema compliance)
- CFPB guidelines (for financial education vs. advice)
- This PRD (source of truth for requirements)

**Your Planning Documents:**
- **Platinum Project_ Peak6_SpendSense.md** - Original PRD
- **SpendSenseAI_Project_Analysis.md** - Detailed analysis
- **PR_by_PR_Implementation_Plan.md** - 30-PR roadmap
- **QUICK_REFERENCE.md** - This document

---

## You're Ready to Build

**You understand:**
- ✅ The architecture (backend service + operator dashboard)
- ✅ The privacy model (operator access is legitimate)
- ✅ The 30-PR path (20 core + 10 extensions)
- ✅ The success metrics (100% on all)
- ✅ The key nuances (personas, tone, explainability)

**Now execute. Build systems people can trust with their financial data.**

