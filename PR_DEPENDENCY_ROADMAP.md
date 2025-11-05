# SpendSenseAI: PR Dependency Roadmap

## Visual PR Flow

This document shows the dependency chain and parallel work opportunities for all 30 PRs.

---

## Phase 1: Foundation (Days 1-5)

**Sequential - Must complete in order:**

```
PR #1: Project Setup
   └─> PR #2: Data Schemas
          └─> PR #3: Synthetic Data Generator
                 └─> PR #4: Data Ingestion Pipeline
```

**No parallelization opportunity** - each depends on previous

**Total Time:** 26-36 hours (3-5 days)

---

## Phase 2: Features (Days 6-12)

**Parallel - All depend on PR #4 only:**

```
PR #4 (completed)
   ├─> PR #5: Subscription Detection ────┐
   ├─> PR #6: Credit Utilization ────────┤
   ├─> PR #7: Savings Analysis ──────────┤──> All ready for PR #9
   └─> PR #8: Income Stability ──────────┘
```

**HIGH PARALLELIZATION** - Can work on multiple simultaneously or tackle in any order

**Recommended Order:** #5 → #6 → #7 → #8 (easiest to hardest)

**Total Time:** 40-48 hours (5-7 days if sequential, 3-4 days if parallel)

---

## Phase 3: Personas (Days 13-16)

**Sequential with PR #11 parallelizable:**

```
PRs #5-8 (completed)
   └─> PR #9: 4 Required Personas
          └─> PR #10: Custom 5th Persona ─────┐
                 └─> PR #11: Prioritization ───┘
```

**Slight parallelization:** PR #11 can start while finalizing PR #10

**Total Time:** 22-28 hours (3-4 days)

---

## Phase 4: Recommendations (Days 17-21)

**Sequential pipeline:**

```
PR #11 (completed)
   └─> PR #12: Content Catalog
          └─> PR #13: Partner Offers
                 └─> PR #14: Rationale Generator
```

**No parallelization** - each builds on previous

**Total Time:** 30-36 hours (4-5 days)

---

## Phase 5: Guardrails (Days 22-24)

**Parallel - Different dependencies:**

```
PR #4 (completed)
   └─> PR #15: Consent System

PR #14 (completed)
   └─> PR #16: Decision Traces
```

**HIGH PARALLELIZATION** - Independent workstreams

**Total Time:** 14-18 hours (2-3 days if parallel, 3-4 days if sequential)

---

## Phase 6: API & UI (Days 25-30)

**Sequential - UI depends on API:**

```
PR #16 (completed)
   └─> PR #17: REST API Implementation
          └─> PR #18: Operator Dashboard
```

**No parallelization** - dashboard needs API endpoints

**Total Time:** 26-34 hours (3-5 days)

---

## Phase 7: Evaluation (Days 31-33)

**Parallel start, then integration:**

```
PR #18 (completed) ────┐
                       ├─> PR #19: Metrics Harness ─────┐
All previous PRs ──────┘                                ├─> PR #20: E2E Testing
                                                        │
                                                        └─> CORE COMPLETE
```

**Total Time:** 22-28 hours (3-4 days)

---

## Extension PRs (Days 34-48) - Optional

### Extension Track A: Enhanced UX

```
PR #17 (API completed)
   ├─> PR #21: Customer Dashboard ─────────────┐
   ├─> PR #22: Notification System ────────────┤
   └─> PR #14 ─> PR #23: Calculators ──────────┤
                                                └─> Enhanced UX Complete
```

**Parallelizable:** PR #21 and #22 can be done simultaneously

**Time:** 30-38 hours (4-5 days if parallel)

---

### Extension Track B: Advanced Analytics

```
PRs #5-8 (Features completed)
   ├─> PR #24: Trend Analysis ──────────────────┐
   │                                             │
PR #19 (Metrics completed)                      │
   └─> PR #25: Cohort Analysis ─────────────────┤
                                                 ├─> Analytics Complete
PR #23 (Calculators completed)                  │
   └─> PR #26: Effectiveness Tracking ──────────┘
```

**Parallelizable:** PR #24 and #25 can start together

**Time:** 28-36 hours (4-5 days if parallel)

---

### Extension Track C: Safety & Explainability

```
PR #14 (Recommendations completed)
   ├─> PR #27: Counterfactual Explanations ─────┐
   │                                             │
PR #20 (E2E Testing completed)                  ├─> Safety Complete
   ├─> PR #28: Adversarial Testing ─────────────┤
   │                                             │
PR #25 (Cohort Analysis completed)              │
   └─> PR #29: Bias Detection ──────────────────┘
```

**Parallelizable:** PR #27 and #28 can start together

**Time:** 30-36 hours (4-5 days if parallel)

---

### Extension Track D: Production Readiness

```
PR #17 (API completed)
   └─> PR #30: Monitoring & Alerting
```

**Standalone** - can be done anytime after API exists

**Time:** 8-10 hours (1-2 days)

---

## Parallelization Strategy

### Maximum Parallel Work Opportunities

**Phase 2 (Features):** 4 PRs can be done in parallel
- Assign PRs #5-8 to different days or work sessions
- Each is independent signal detector

**Phase 5 (Guardrails):** 2 PRs can be done in parallel
- PR #15 (Consent) and PR #16 (Decision Traces)
- Different systems, different dependencies

**Extension Tracks:** All 3 tracks can run in parallel
- Track A (UX), Track B (Analytics), Track C (Safety)
- Pick 1-2 tracks based on goals

---

## Critical Path Analysis

**The LONGEST sequential chain (no parallelization):**

```
PR #1 → PR #2 → PR #3 → PR #4 → 
PR #5 → PR #9 → PR #10 → PR #11 → 
PR #12 → PR #13 → PR #14 → PR #16 → 
PR #17 → PR #18 → PR #19 → PR #20
```

**Critical Path Time:** ~160-190 hours (20-24 days)

**With Optimal Parallelization:**
- Phase 2: Save 2-3 days (work on features in parallel)
- Phase 5: Save 1 day (consent + traces in parallel)
- **Optimized Core Completion:** 17-20 days

---

## Recommended Work Patterns

### Pattern 1: Solo Developer (Linear)
**Approach:** One PR at a time, following numbered sequence
**Timeline:** 23-33 days for core
**Best for:** Thoroughness, learning, careful testing

### Pattern 2: Solo Developer (Optimized)
**Approach:** Batch parallel work in Phase 2 (features)
**Timeline:** 20-28 days for core
**Best for:** Efficiency, good time management

### Pattern 3: Team of 2
**Developer A:**
- Weeks 1-2: PRs #1-4, #5, #7 (foundation + subscriptions + savings)
- Week 3: PRs #9-11 (personas)
- Week 4: PRs #17-18 (API + operator UI)

**Developer B:**
- Weeks 1-2: PRs #6, #8 (credit + income, after #4 done)
- Week 3: PRs #12-14 (recommendations)
- Week 4: PRs #15-16, #19-20 (guardrails + evaluation)

**Timeline:** ~3 weeks for core

### Pattern 4: Team of 3+
**Developer A:** Foundation + Features (#1-8)
**Developer B:** Personas + Recommendations (#9-14)
**Developer C:** Guardrails + API + UI (#15-18)
**Everyone:** Evaluation together (#19-20)

**Timeline:** ~2.5 weeks for core

---

## Dependencies Matrix

| PR | Depends On | Can Start After | Blocks |
|----|-----------|-----------------|--------|
| #1 | None | Immediately | #2 |
| #2 | #1 | Day 1 | #3 |
| #3 | #2 | Day 2 | #4 |
| #4 | #3 | Day 3 | #5-8, #15 |
| #5 | #4 | Day 4 | #9, #24 |
| #6 | #4 | Day 4 | #9 |
| #7 | #4 | Day 4 | #9 |
| #8 | #4 | Day 4 | #9 |
| #9 | #5-8 | Day 8 | #10 |
| #10 | #9 | Day 11 | #11 |
| #11 | #10 | Day 12 | #12 |
| #12 | #11 | Day 13 | #13 |
| #13 | #12 | Day 15 | #14 |
| #14 | #13 | Day 17 | #16, #23, #27 |
| #15 | #4 | Day 4 (parallel with #5-8) | #19 |
| #16 | #14 | Day 17 | #17 |
| #17 | #16 | Day 19 | #18, #21, #30 |
| #18 | #17 | Day 22 | #19 |
| #19 | #18, #15 | Day 25 | #20, #25 |
| #20 | #19 | Day 28 | Extensions, #28 |

---

## Daily Work Plan (Solo Developer, Optimized)

**Week 1:**
- **Day 1:** PR #1 (Setup) + PR #2 (Schemas) - 8-12 hours
- **Day 2-3:** PR #3 (Synthetic Data) - 12-16 hours
- **Day 4:** PR #4 (Ingestion) - 6-8 hours
- **Day 5:** PR #5 (Subscriptions) - 10-12 hours

**Week 2:**
- **Day 6:** PR #6 (Credit) - 8-10 hours
- **Day 7:** PR #7 (Savings) - 10-12 hours
- **Day 8:** PR #8 (Income) - 12-14 hours
- **Day 9:** PR #9 (4 Personas) - 10-12 hours
- **Day 10:** PR #10 (Custom Persona) - 6-8 hours

**Week 3:**
- **Day 11:** PR #11 (Prioritization) - 6-8 hours
- **Day 12:** PR #12 (Content Catalog) - 8-10 hours
- **Day 13:** PR #13 (Partner Offers) - 10-12 hours
- **Day 14:** PR #14 (Rationales) - 12-14 hours
- **Day 15:** PR #15 (Consent) - 6-8 hours

**Week 4:**
- **Day 16:** PR #16 (Decision Traces) - 8-10 hours
- **Day 17-18:** PR #17 (REST API) - 12-16 hours
- **Day 19-20:** PR #18 (Operator Dashboard) - 14-18 hours
- **Day 21:** PR #19 (Metrics) - 10-12 hours

**Week 5:**
- **Day 22:** PR #20 (E2E Testing) - 12-16 hours
- **Day 23-24:** Extensions (pick 2-3 high-value ones)
- **Day 25:** Final testing, documentation polish, demo video

---

## PR Size Guidelines

**Small PRs (2-4 hours):**
- #1: Project Setup
- #10: Custom Persona (if you have clear design)
- #30: Monitoring

**Medium PRs (6-10 hours):**
- #2: Schemas
- #4: Ingestion
- #6: Credit Utilization
- #9: 4 Personas
- #11: Prioritization
- #12: Content Catalog
- #15: Consent
- #16: Decision Traces
- #19: Metrics

**Large PRs (12-18 hours):**
- #3: Synthetic Data
- #5: Subscription Detection
- #7: Savings Analysis
- #8: Income Stability
- #13: Partner Offers
- #14: Rationale Generator
- #17: REST API
- #18: Operator Dashboard
- #20: E2E Testing
- #21: Customer Dashboard

---

## Checkpoint Validation

**After PR #4 (Day 5):**
- [ ] Can query synthetic users, accounts, transactions from database
- [ ] Data matches Plaid schema exactly
- [ ] 50-100 diverse users generated
- [ ] No real PII present

**After PR #8 (Day 12):**
- [ ] Can compute all 4 signal types for any user
- [ ] 30-day and 180-day windows both work
- [ ] Edge cases handled (no data, sparse data)
- [ ] Unit tests pass for all detectors

**After PR #11 (Day 16):**
- [ ] All 5 personas implemented
- [ ] Every synthetic user assigned a persona
- [ ] Prioritization handles conflicts
- [ ] Custom persona is well-justified

**After PR #14 (Day 21):**
- [ ] Can generate 3-5 recommendations per user
- [ ] Every recommendation has plain-language rationale
- [ ] Rationales cite specific data points
- [ ] Tone is educational, not shaming

**After PR #18 (Day 25):**
- [ ] REST API endpoints all functional
- [ ] Operator dashboard shows all signals
- [ ] Operators can review and override recommendations
- [ ] Decision traces visible

**After PR #20 (Day 30):**
- [ ] 100% persona coverage
- [ ] ≥3 behaviors detected per user
- [ ] 100% rationales present
- [ ] 100% decision traces
- [ ] <5 second latency per user
- [ ] ≥10 tests passing
- [ ] Consent enforcement working

---

## Risk Mitigation by Phase

**Phase 2 Risk (Features):**
- **Risk:** Complex signal detection takes longer than expected
- **Mitigation:** Start with subscriptions (easiest), leave income for last
- **Buffer:** Build in 2-3 extra days

**Phase 4 Risk (Recommendations):**
- **Risk:** Rationale generation is tricky, might need iteration
- **Mitigation:** Start with template system, iterate on quality
- **Buffer:** This is on critical path, allocate extra time

**Phase 6 Risk (API & UI):**
- **Risk:** Operator dashboard might be unfamiliar if new to web dev
- **Mitigation:** Use Streamlit (Python) for rapid prototyping, or simple HTML
- **Buffer:** Can use basic UI if time constrained

---

## When to Add Extensions

**Scenario 1: On Schedule (Day 23-24)**
Add extensions in this priority order:
1. **PR #21 (Customer Dashboard)** - Highest impact, shows end-to-end
2. **PR #27 (Counterfactuals)** - Advanced explainability
3. **PR #29 (Bias Detection)** - Demonstrates ethics
4. **PR #24 (Trend Analysis)** - Shows longitudinal thinking
5. **PR #30 (Monitoring)** - Production readiness

**Scenario 2: Behind Schedule (Day 25-26)**
- **Skip extensions, focus on perfecting core**
- Ensure 100% on all success metrics
- Polish documentation and demo video
- Strong core > weak core + extensions

**Scenario 3: Ahead of Schedule (Day 20)**
- **Add 4-5 extensions**
- Aim for platinum-level submission
- Go deep on 1-2 tracks (UX + Safety recommended)

---

## Final Pre-Submission Checklist

**Before you submit, walk through this PR-by-PR:**

- [ ] PR #1: README is clear, one-command setup works
- [ ] PR #2: Schemas documented, examples provided
- [ ] PR #3: 50-100 diverse users, no PII, deterministic
- [ ] PR #4: All data loads correctly, queries work
- [ ] PR #5: Subscription detection accurate, tested
- [ ] PR #6: Credit utilization math correct, thresholds work
- [ ] PR #7: Savings classification accurate, growth calculated
- [ ] PR #8: Income detection reliable, variability measured
- [ ] PR #9: All 4 personas match criteria exactly
- [ ] PR #10: Custom persona well-justified, unique
- [ ] PR #11: Prioritization handles all conflicts
- [ ] PR #12: 3-5 content items per persona
- [ ] PR #13: Eligibility filters prevent harmful offers
- [ ] PR #14: 100% rationales, plain language, data citations
- [ ] PR #15: Consent enforced, no recs without opt-in
- [ ] PR #16: Decision traces complete, auditable
- [ ] PR #17: All API endpoints work, documented
- [ ] PR #18: Operator dashboard functional, shows all data
- [ ] PR #19: All metrics at 100%, report generated
- [ ] PR #20: E2E tests pass, system reliable

**If any PR above is incomplete, submission fails requirements.**

---

## Summary

**Core Path:** 20 PRs → 23-33 days → 100% Requirements
**Extended Path:** 30 PRs → 33-48 days → Platinum Submission

**Key Parallelization Opportunities:**
- Phase 2 (Features): 4 parallel PRs, save 2-3 days
- Phase 5 (Guardrails): 2 parallel PRs, save 1 day
- Extensions: 3 tracks can run in parallel

**Critical Path:** PRs #1→#2→#3→#4→#9→#11→#12→#13→#14→#17→#18→#20

**Your roadmap is complete. Execute systematically, validate at checkpoints, and ship with confidence.**

